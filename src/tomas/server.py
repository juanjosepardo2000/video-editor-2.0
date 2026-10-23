"""Panel local del sistema de control de tomas (solo escucha en 127.0.0.1).

Arranque:  PYTHONPATH=src .venv/bin/python -m tomas.server   →   http://127.0.0.1:8765
Sin dependencias externas: usa la biblioteca estándar y los módulos de este paquete.
"""
import json
import mimetypes
import re
import shutil
import subprocess
import threading
import time
import traceback
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from . import capcut, clasificador, maquetado, multicam
from .util import CONFIG, DATA, REPO, VIDEO_EXT, list_clips, read_json, write_json

WEB = Path(__file__).parent / "web"
HOME = Path.home()
JOBS: dict[str, dict] = {}
LOCK = threading.Lock()   # un trabajo pesado a la vez (la CPU y el disco son pocos)


def _job(fn, *args, **kw) -> str:
    jid = uuid.uuid4().hex[:8]
    JOBS[jid] = {"id": jid, "estado": "en cola", "log": [], "resultado": None, "error": None, "t0": time.time()}

    def log(msg="", *a):
        JOBS[jid]["log"].append(str(msg))

    def run():
        with LOCK:
            JOBS[jid]["estado"] = "ejecutando"
            try:
                JOBS[jid]["resultado"] = fn(*args, log=log, **kw)
                JOBS[jid]["estado"] = "terminado"
            except Exception as e:   # se muestra en el panel
                JOBS[jid]["estado"] = "error"
                JOBS[jid]["error"] = f"{type(e).__name__}: {e}"
                JOBS[jid]["log"].append(traceback.format_exc()[-800:])
            JOBS[jid]["segundos"] = round(time.time() - JOBS[jid]["t0"], 1)

    threading.Thread(target=run, daemon=True).start()
    return jid


def _ruta(txt: str) -> Path:
    p = Path(txt).expanduser()
    if not p.is_absolute():
        p = REPO / p
    return p


def _permitida(p: Path) -> bool:
    p = p.resolve()
    return str(p).startswith(str(HOME)) or str(p).startswith("/Volumes/")


def _proyecto_cfg(nombre: str) -> dict:
    return read_json(DATA / nombre / "proyecto.json", {})


def _guardar_cfg(nombre: str, **kw) -> None:
    cfg = {**_proyecto_cfg(nombre), **kw}
    write_json(DATA / nombre / "proyecto.json", cfg)


def _slug(txt: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", txt).strip("._") or "proyecto"


def _subidos(proyecto: str, tipo: str) -> Path:
    if tipo not in ("tomas", "guion", "multicam", "maquetado"):
        raise KeyError("tipo")
    return DATA / _slug(proyecto) / "subidos" / tipo


def _lista_subidos(proyecto: str, tipo: str) -> list[dict]:
    d = _subidos(proyecto, tipo)
    return [{"nombre": x.name, "bytes": x.stat().st_size} for x in sorted(d.glob("*")) if x.is_file() and not x.name.startswith(".")] if d.exists() else []


def _miniatura(p: Path) -> Path:
    d = DATA / "proxy" / "miniaturas"
    d.mkdir(parents=True, exist_ok=True)
    out = d / (re.sub(r"[^A-Za-z0-9._-]+", "_", f"{p.parent.name}_{p.stem}") + f"_{int(p.stat().st_mtime)}.jpg")
    if not out.exists():
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "1", "-i", str(p), "-frames:v", "1", "-vf", "scale=360:-2", "-q:v", "5", str(out)], capture_output=True)
        if not out.exists():   # clips de menos de 1 s
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(p), "-frames:v", "1", "-vf", "scale=360:-2", "-q:v", "5", str(out)], capture_output=True)
    return out


def _proxy(p: Path) -> Path:
    """Versión ligera en H.264 para reproducir en el navegador (MP4/MOV de cámara pueden no abrirse directo)."""
    d = DATA / "proxy"
    d.mkdir(parents=True, exist_ok=True)
    out = d / (re.sub(r"[^A-Za-z0-9._-]+", "_", f"{p.parent.name}_{p.stem}") + f"_{int(p.stat().st_mtime)}.mp4")
    if not out.exists():
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(p), "-vf", "scale=-2:360", "-c:v", "libx264", "-preset", "veryfast",
                        "-crf", "32", "-c:a", "aac", "-b:a", "64k", "-movflags", "+faststart", str(out)], capture_output=True)
    return out


class H(BaseHTTPRequestHandler):
    server_version = "Tomas/0.1"

    def log_message(self, *a):   # silencio
        pass

    def _json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False, default=float).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _archivo(self, p: Path, ctype: str | None = None):
        if not p.is_file():
            return self._json({"error": "no existe"}, 404)
        size = p.stat().st_size
        rng = self.headers.get("Range")
        a, b = 0, size - 1
        if rng and (m := re.match(r"bytes=(\d*)-(\d*)", rng)):
            a = int(m.group(1)) if m.group(1) else 0
            b = int(m.group(2)) if m.group(2) else size - 1
        self.send_response(206 if rng else 200)
        self.send_header("Content-Type", ctype or mimetypes.guess_type(str(p))[0] or "application/octet-stream")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(b - a + 1))
        if rng:
            self.send_header("Content-Range", f"bytes {a}-{b}/{size}")
        self.end_headers()
        with p.open("rb") as f:
            f.seek(a)
            left = b - a + 1
            while left > 0:
                chunk = f.read(min(1 << 20, left))
                if not chunk:
                    break
                try:
                    self.wfile.write(chunk)
                except (BrokenPipeError, ConnectionResetError):
                    return
                left -= len(chunk)

    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}
        if u.path in ("/", "/index.html"):
            return self._archivo(WEB / "index.html", "text/html; charset=utf-8")
        if u.path == "/api/estado":
            proys = sorted(p.name for p in DATA.iterdir() if p.is_dir() and not p.name.startswith(("_", "proxy"))) if DATA.exists() else []
            return self._json({"proyectos": proys, "criterios": CONFIG["criterios"], "home": str(HOME),
                               "libre_gb": round(shutil.disk_usage(HOME).free / 1e9, 1),
                               "juez_claude": bool(__import__("os").environ.get("ANTHROPIC_API_KEY"))})
        if u.path == "/api/proyecto":
            n = q["nombre"]
            return self._json({"cfg": _proyecto_cfg(n), "clasificacion": read_json(DATA / n / "clasificacion.json"),
                               "revision": read_json(DATA / n / "revision.json", {}), "multicam": read_json(DATA / n / "multicam/multicam.json"),
                               "maquetado": read_json(DATA / n / "maquetado/maquetado.json"),
                               "concordancia": clasificador.concordancia(n),
                               "previews": sorted(x.name for x in (DATA / n / "maquetado").glob("maquetado_*.mp4")) if (DATA / n / "maquetado").exists() else []})
        if u.path == "/api/job":
            j = JOBS.get(q.get("id", ""))
            return self._json(j or {"error": "trabajo desconocido"}, 200 if j else 404)
        if u.path == "/api/explorar":
            p = _ruta(q.get("ruta") or str(HOME))
            if not _permitida(p) or not p.exists():
                return self._json({"error": "ruta no permitida"}, 400)
            if p.is_file():
                p = p.parent
            try:
                items = [{"nombre": x.name, "dir": x.is_dir(), "ruta": str(x)} for x in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
                         if not x.name.startswith(".") and (x.is_dir() or x.suffix.lower() in VIDEO_EXT | {".txt", ".md", ".csv", ".docx"})]
            except PermissionError:
                return self._json({"error": "macOS no deja a este programa leer esa carpeta"}, 403)
            return self._json({"ruta": str(p), "padre": str(p.parent), "items": items[:300]})
        if u.path == "/api/video":
            p = _ruta(q["ruta"])
            if not _permitida(p) and not str(p.resolve()).startswith(str(DATA.resolve())):
                return self._json({"error": "ruta no permitida"}, 403)
            if p.suffix.lower() not in (".mp4", ".m4v"):
                p = _proxy(p)
            return self._archivo(p, "video/mp4")
        if u.path == "/api/subidos":
            return self._json({"archivos": _lista_subidos(q["proyecto"], q["tipo"]), "carpeta": str(_subidos(q["proyecto"], q["tipo"]))})
        if u.path == "/api/miniatura":
            p = _ruta(q["ruta"])
            if not _permitida(p) and not str(p.resolve()).startswith(str(DATA.resolve())):
                return self._json({"error": "ruta no permitida"}, 403)
            m = _miniatura(p)
            return self._archivo(m, "image/jpeg") if m.exists() else self._json({"error": "sin miniatura"}, 404)
        if u.path == "/api/preview":
            return self._archivo(DATA / q["proyecto"] / "maquetado" / Path(q["archivo"]).name, "video/mp4")
        self._json({"error": "no encontrado"}, 404)

    def _subir(self, q: dict):
        """Guarda el cuerpo de la petición (el archivo) por trozos: sirve para videos de varios GB."""
        n = int(self.headers.get("Content-Length") or 0)
        nombre = _slug(Path(unquote(q.get("nombre", "archivo"))).name)
        dest_dir = _subidos(q["proyecto"], q["tipo"])
        dest_dir.mkdir(parents=True, exist_ok=True)
        libre = shutil.disk_usage(dest_dir).free
        if n > libre - 300_000_000:
            self.rfile.read(0)
            return self._json({"error": f"No hay espacio: el archivo pesa {n/1e9:.1f} GB y quedan {libre/1e9:.1f} GB"}, 507)
        tmp = dest_dir / f".{nombre}.part"
        left = n
        with tmp.open("wb") as f:
            while left > 0:
                chunk = self.rfile.read(min(1 << 20, left))
                if not chunk:
                    break
                f.write(chunk)
                left -= len(chunk)
        if left:
            tmp.unlink(missing_ok=True)
            return self._json({"error": "La subida se cortó"}, 400)
        tmp.replace(dest_dir / nombre)
        self._json({"ok": True, "nombre": nombre, "archivos": _lista_subidos(q["proyecto"], q["tipo"])})

    def do_POST(self):
        pu = urlparse(self.path)
        if pu.path == "/api/subir":
            try:
                return self._subir({k: v[0] for k, v in parse_qs(pu.query).items()})
            except KeyError as e:
                return self._json({"error": f"Falta el dato {e}"}, 400)
        n = int(self.headers.get("Content-Length") or 0)
        d = json.loads(self.rfile.read(n) or b"{}")
        u = pu.path
        try:
            if u == "/api/quitar":
                (_subidos(d["proyecto"], d["tipo"]) / Path(d["nombre"]).name).unlink(missing_ok=True)
                return self._json({"archivos": _lista_subidos(d["proyecto"], d["tipo"])})
            if u == "/api/abrir":
                p = _ruta(d["ruta"])
                if not _permitida(p) and not str(p.resolve()).startswith(str(DATA.resolve())):
                    return self._json({"error": "ruta no permitida"}, 403)
                subprocess.run(["open", str(p)])
                return self._json({"ok": True})
            if u == "/api/clasificar":
                carpeta = _ruta(d["carpeta"]) if d.get("carpeta") else _subidos(d["proyecto"], "tomas")
                guion = _ruta(d["guion"]) if d.get("guion") else next(iter(sorted(_subidos(d["proyecto"], "guion").glob("*"))), None) \
                    if _subidos(d["proyecto"], "guion").exists() else None
                if not carpeta.is_dir() or not list_clips(carpeta):
                    return self._json({"error": f"No hay videos en {carpeta}"}, 400)
                _guardar_cfg(d["proyecto"], carpeta_tomas=str(carpeta), guion=str(guion) if guion else None)
                def tarea_clas(proyecto, carpeta, guion, opts, log):
                    r = clasificador.clasificar_carpeta(proyecto, carpeta, guion, opts, log)
                    log("Preparando miniaturas…")
                    for t in r["tomas"]:
                        _miniatura(Path(t["archivo"]))
                    return {"tomas": len(r["tomas"])}
                return self._json({"job": _job(tarea_clas, d["proyecto"], carpeta, guion,
                                               {"modelo": d.get("modelo", "small"), "juez": d.get("juez", "difuso")})})
            if u == "/api/revision":
                return self._json(clasificador.aplicar_revision(d["proyecto"], d["nombre"], d["semaforo"], d.get("nota", "")))
            if u == "/api/carpetas":
                return self._json(clasificador.exportar_carpetas(d["proyecto"]))
            if u == "/api/multicam":
                carpeta = _ruta(d["carpeta"])
                if not carpeta.is_dir():
                    return self._json({"error": f"No existe {carpeta}"}, 400)
                _guardar_cfg(d["proyecto"], carpeta_multicam=str(carpeta))
                return self._json({"job": _job(multicam.analizar, d["proyecto"], carpeta, {})})
            if u == "/api/maquetar":
                carpeta, guion = _ruta(d["carpeta"]), _ruta(d["guion"])
                clips = list_clips(carpeta) if carpeta.is_dir() else [carpeta]
                if not clips or not guion.is_file():
                    return self._json({"error": "Faltan los videos o el guion"}, 400)
                _guardar_cfg(d["proyecto"], carpeta_maquetado=str(carpeta), guion=str(guion))
                opts = {k: d[k] for k in ("pausa_frase", "silencio_max", "modelo") if k in d}

                def tarea(proyecto, clips, guion, opts, log):
                    r = maquetado.maquetar(proyecto, clips, guion, opts, log)
                    maquetado.renderizar(proyecto, "preview", log)
                    return r["resumen"]
                return self._json({"job": _job(tarea, d["proyecto"], clips, guion, opts)})
            if u == "/api/capcut":
                fn = {"maquetado": capcut.desde_maquetado, "multicam": capcut.desde_multicam}[d["servicio"]]

                def tarea_cc(proyecto, nombre, log):
                    b = fn(proyecto, nombre or None, log=log)
                    return {"proyecto_capcut": str(b), "instalar": f'python3 src/nle_bridge/install_capcut_draft.py "{b.relative_to(REPO)}"'}
                return self._json({"job": _job(tarea_cc, d["proyecto"], d.get("nombre", ""))})
            if u == "/api/render":
                return self._json({"job": _job(lambda p, c, log: str(maquetado.renderizar(p, c, log)), d["proyecto"], d.get("calidad", "final"))})
        except KeyError as e:
            return self._json({"error": f"Falta el dato {e}"}, 400)
        self._json({"error": "no encontrado"}, 404)


def main(port: int = 8765):
    DATA.mkdir(exist_ok=True)
    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    print(f"Panel de control de tomas: http://127.0.0.1:{port}  (Ctrl+C para salir)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
