"""Servicio 3: maquetado. Con tomas largas + guion elige la mejor toma de cada línea y corta muletillas, silencios,
reinicios y respiraciones fuertes, dejando una pausa corta entre frases. Sin transiciones ni efectos.

Salida: lista de segmentos a conservar (clip, inicio, fin), lista de cortes con su motivo y un informe por línea del guion.
"""
import subprocess
from pathlib import Path

import numpy as np

from . import audio as A
from . import guion as G
from .ficha import ficha
from .habla import marcar_muletillas
from .util import DATA, content_tokens, norm, tokens, write_json

PARAMS = {"pausa_frase": 0.35, "silencio_max": 0.40, "pausa_interna": 0.22, "pad": 0.06, "respiracion_db": 9.0,
          "cobertura_min": 0.55, "modelo": "small", "idioma": "es"}


def _candidatos(palabras: list[dict], linea: list[str], n_linea: int, top: int = 4) -> list[dict]:
    """Ventanas de palabras de un clip que se parecen a una línea del guion (cada ventana = una toma de esa línea)."""
    ref = set(linea)
    toks = [norm(p["w"]).replace(" ", "") for p in palabras]
    anclas = [i for i, t in enumerate(toks) if t in ref]
    vistos, cands = set(), []
    lmin, lmax = max(2, int(n_linea * 0.6)), int(n_linea * 1.7) + 4
    for a in anclas:
        for s in range(max(0, a - 3), a + 1):
            if s in vistos:
                continue
            vistos.add(s)
            mejor = None
            for ln in range(lmin, lmax + 1):
                e = s + ln
                if e > len(palabras):
                    break
                ven = [t for t in (content_tokens(palabras[k]["w"]) for k in range(s, e)) for t in t]
                cov, prec = G.solape(ven, linea)
                f1 = 2 * cov * prec / (cov + prec) if cov + prec else 0.0
                if mejor is None or f1 > mejor["f1"] + 1e-9:
                    mejor = {"s": s, "e": e, "f1": f1, "cobertura": cov, "precision": prec}
            if mejor and mejor["f1"] > 0.35:
                cands.append(mejor)
    cands.sort(key=lambda c: -c["f1"])
    out = []
    for c in cands:   # sin ventanas casi idénticas entre sí
        if all(abs(c["s"] - o["s"]) > 2 or abs(c["e"] - o["e"]) > 2 for o in out):
            out.append(c)
        if len(out) >= top:
            break
    return out


def _calidad(c: dict, palabras: list[dict], flags: list[bool], orden: int) -> float:
    ven = palabras[c["s"]: c["e"]]
    mul = sum(flags[c["s"]: c["e"]]) / max(len(ven), 1)
    conf = sum(p.get("score", 0) for p in ven) / max(len(ven), 1)
    return 0.70 * c["f1"] + 0.10 * (1 - min(mul * 4, 1)) + 0.15 * conf + 0.05 * c["cobertura"] + 0.0005 * orden


def _limpiar_ventana(pal: list[dict], flags: list[bool], x: np.ndarray, piso: float, P: dict, clip_idx: int,
                     lim_ant: float, lim_sig: float, ultima: bool, texto_dicho: list) -> tuple[list[dict], list[dict]]:
    """Convierte una ventana en segmentos a conservar; devuelve (segmentos, cortes internos con motivo)."""
    cortes, keep = [], []
    prev = None
    for p, m in zip(pal, flags):
        if m:
            cortes.append({"clip": clip_idx, "start": p["start"], "end": p["end"], "motivo": f"muletilla «{p['w']}»"})
            continue
        if prev is not None and norm(prev["w"]) == norm(p["w"]) and p["start"] - prev["end"] < 0.6 and len(norm(p["w"])) <= 4:
            cortes.append({"clip": clip_idx, "start": keep[-1]["start"], "end": keep[-1]["end"], "motivo": f"repetición «{prev['w']}»"})
            keep.pop()
        keep.append(p)
        prev = p
    if not keep:
        return [], cortes
    segs, ini = [], keep[0]["start"]
    for a, b in zip(keep, keep[1:]):
        hueco = b["start"] - a["end"]
        resp = hueco >= 0.18 and A.energia_entre(x, a["end"] + 0.03, b["start"] - 0.03, piso) > P["respiracion_db"]
        if hueco > P["silencio_max"] or resp:
            quedar = P["pad"] if resp else P["pausa_interna"] / 2
            segs.append((ini, a["end"] + quedar))
            cortes.append({"clip": clip_idx, "start": a["end"] + quedar, "end": b["start"] - quedar,
                           "motivo": ("respiración fuerte" if resp else f"silencio de {hueco:.1f} s")})
            ini = b["start"] - quedar
    segs.append((ini, keep[-1]["end"]))
    mitad = P["pausa_frase"] / 2
    s0 = max(segs[0][0] - mitad, lim_ant)
    s1 = min(segs[-1][1] + (0.12 if ultima else mitad), lim_sig)
    segs[0] = (s0, segs[0][1])
    segs[-1] = (segs[-1][0], s1)
    return [{"clip": clip_idx, "start": round(a, 3), "end": round(b, 3)} for a, b in segs if b - a > 0.05], cortes


def maquetar(proyecto: str, clips: list[Path], guion_path: Path, opciones: dict | None = None, log=print) -> dict:
    P = {**PARAMS, **(opciones or {})}
    proy = DATA / proyecto
    gui = G.leer_guion(guion_path)
    if not gui:
        raise ValueError("El guion está vacío o no se pudo leer.")
    fichas, xs, pisos, flags_c = [], [], [], []
    for c in clips:
        log(f"Analizando {c.name}…")
        f = ficha(c, proy / "fichas", True, P["modelo"], P["idioma"], log)
        fichas.append(f)
        x = A.leer(c, 0, f["duracion"]) if f["tiene_audio"] else np.zeros(0, np.float32)
        xs.append(x)
        db = 20 * np.log10(np.sqrt((x[: len(x) // 800 * 800].reshape(-1, 800) ** 2).mean(axis=1)) + 1e-9) if len(x) >= 800 else np.array([-90.0])
        pisos.append(float(np.percentile(db, 10)))
        flags_c.append(marcar_muletillas(f["habla"]["palabras"]))
    log(f"Buscando las tomas de cada línea ({len(gui)} líneas del guion)…")
    todos = []   # (calidad, linea, clip, cand)
    por_linea: dict[int, list] = {}
    for li, g in enumerate(gui):
        lt = content_tokens(g["texto"])
        n = len(tokens(g["texto"]))
        for ci, f in enumerate(fichas):
            pal = f["habla"]["palabras"]
            for c in _candidatos(pal, lt, n):
                q = _calidad(c, pal, flags_c[ci], ci)
                reg = {"q": q, "linea": li, "clip": ci, **c}
                todos.append(reg)
                por_linea.setdefault(li, []).append(reg)
    elegidas: dict[int, dict] = {}
    usados: list[tuple[int, int, int]] = []
    for reg in sorted(todos, key=lambda r: -r["q"]):
        if reg["linea"] in elegidas or reg["cobertura"] < P["cobertura_min"]:
            continue
        if any(reg["clip"] == c and reg["s"] < e and s < reg["e"] for c, s, e in usados):
            continue
        elegidas[reg["linea"]] = reg
        usados.append((reg["clip"], reg["s"], reg["e"]))
    segmentos, cortes, lineas = [], [], []
    for li, g in enumerate(gui):
        reg = elegidas.get(li)
        alt = [r for r in por_linea.get(li, []) if r is not reg and r["f1"] >= 0.5]
        if not reg:
            lineas.append({"n": g["n"], "escena": g["escena"], "guion": g["texto"], "estado": "no encontrada",
                           "motivo": "no se encontró una toma que diga esto: grabar de nuevo o revisar a mano", "alternativas": len(alt)})
            continue
        pal = fichas[reg["clip"]]["habla"]["palabras"]
        ven = pal[reg["s"]: reg["e"]]
        lim_ant = pal[reg["s"] - 1]["end"] + 0.02 if reg["s"] > 0 else 0.0
        lim_sig = pal[reg["e"]]["start"] - 0.02 if reg["e"] < len(pal) else fichas[reg["clip"]]["duracion"]
        segs, cs = _limpiar_ventana(ven, flags_c[reg["clip"]][reg["s"]: reg["e"]], xs[reg["clip"]], pisos[reg["clip"]], P,
                                    reg["clip"], max(lim_ant, ven[0]["start"] - P["pausa_frase"]), lim_sig, li == len(gui) - 1, [])
        for s in segs:
            s["linea"] = g["n"]
        segmentos += segs
        cortes += cs
        estado = "ok" if reg["cobertura"] >= 0.8 else "incompleta"
        lineas.append({"n": g["n"], "escena": g["escena"], "guion": g["texto"], "estado": estado,
                       "clip": Path(fichas[reg["clip"]]["archivo"]).name, "inicio": ven[0]["start"], "fin": ven[-1]["end"],
                       "dicho": " ".join(p["w"] for p in ven), "cobertura": round(reg["cobertura"], 2), "calidad": round(reg["q"], 2),
                       "alternativas": len(alt),
                       "motivo": (f"mejor de {len(alt)+1} tomas" if alt else "única toma") +
                                 ("" if estado == "ok" else f" · cubre solo {reg['cobertura']*100:.0f}% de la línea: revisar")})
    # lo que queda fuera: tiempo total y reparto
    total = sum(f["duracion"] for f in fichas)
    final = sum(s["end"] - s["start"] for s in segmentos)
    resumen = {"duracion_original": round(total, 1), "duracion_final": round(final, 1), "ahorro_pct": round(100 * (1 - final / total), 1) if total else 0,
               "lineas_ok": sum(1 for l in lineas if l["estado"] == "ok"), "lineas_total": len(gui),
               "muletillas_cortadas": sum(1 for c in cortes if c["motivo"].startswith("muletilla")),
               "silencios_cortados": sum(1 for c in cortes if c["motivo"].startswith("silencio")),
               "respiraciones_cortadas": sum(1 for c in cortes if c["motivo"].startswith("respiración")),
               "repeticiones_cortadas": sum(1 for c in cortes if c["motivo"].startswith("repetición"))}
    res = {"proyecto": proyecto, "clips": [str(c) for c in clips], "guion": str(guion_path), "parametros": P,
           "segmentos": segmentos, "cortes": cortes, "lineas": lineas, "resumen": resumen}
    write_json(proy / "maquetado/maquetado.json", res)
    return res


def renderizar(proyecto: str, calidad: str = "preview", log=print) -> Path:
    """Une los segmentos en un solo video (sin transiciones). 'preview' = 640 px, ligero; 'final' = resolución original."""
    proy = DATA / proyecto
    from .util import read_json
    m = read_json(proy / "maquetado/maquetado.json")
    if not m or not m["segmentos"]:
        raise ValueError("No hay segmentos: ejecuta primero el maquetado.")
    clips = m["clips"]
    partes, n = [], len(m["segmentos"])
    for i, s in enumerate(m["segmentos"]):
        a, b, k = s["start"], s["end"], s["clip"]
        d = b - a
        fi = min(0.01, d / 4)
        partes.append(f"[{k}:v]trim=start={a}:end={b},setpts=PTS-STARTPTS[v{i}];"
                      f"[{k}:a]atrim=start={a}:end={b},asetpts=PTS-STARTPTS,afade=t=in:d={fi},afade=t=out:st={d-fi:.3f}:d={fi}[a{i}]")
    cat = "".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a]"
    escala = ",scale=640:-2" if calidad == "preview" else ""
    script = ";".join(partes) + ";" + cat.replace("[v][a]", "[vc][a]") + f";[vc]format=yuv420p{escala}[v]"
    salida = proy / f"maquetado/maquetado_{calidad}.mp4"
    salida.parent.mkdir(parents=True, exist_ok=True)
    sf = salida.with_suffix(".filter")
    sf.write_text(script)
    cmd = ["ffmpeg", "-y", "-v", "error"]
    for c in clips:
        cmd += ["-i", c]
    cmd += ["-/filter_complex", str(sf), "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-preset", "veryfast",
            "-crf", "30" if calidad == "preview" else "18", "-c:a", "aac", "-b:a", "128k", str(salida)]
    log("Renderizando el maquetado…")
    r = subprocess.run(cmd, capture_output=True, text=True)
    sf.unlink(missing_ok=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-400:])
    return salida
