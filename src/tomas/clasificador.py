"""Servicio 1: clasificador de tomas (semáforo + motivo + marcadores + carpetas) según los criterios de la productora."""
import os
import re
import shutil
from pathlib import Path

from . import guion as G
from . import habla
from .ficha import ficha
from .util import CONFIG, DATA, list_clips, read_json, write_json

U = CONFIG["umbrales"]
CRITERIOS = {c["id"]: c for c in CONFIG["criterios"]}
ESTADO_TXT = {"pass": "cumple", "warn": "dudoso", "fail": "no cumple"}


def _pronunciacion(h: dict | None) -> dict:
    if not h or not h["palabras"]:
        return {"estado": "warn", "motivo": "no se detectó habla para evaluar la pronunciación", "valores": {}, "eventos": []}
    r = habla.resumen_pronunciacion(h["palabras"])
    est, mot = [], []
    if r["ratio_muletillas"] >= U["muletillas_fail"]:
        est.append("fail"); mot.append(f"exceso de muletillas ({r['muletillas']} en {r['n']} palabras)")
    elif r["ratio_muletillas"] >= U["muletillas_warn"]:
        est.append("warn"); mot.append(f"varias muletillas ({r['muletillas']} en {r['n']} palabras)")
    if r["baja_conf"] >= U["baja_conf_fail"]:
        est.append("warn"); mot.append(f"{r['baja_conf']*100:.0f}% de las palabras se entienden con poca claridad (revisar)")
    elif r["baja_conf"] >= U["baja_conf_warn"]:
        est.append("warn"); mot.append(f"algunas palabras poco claras ({r['baja_conf']*100:.0f}%)")
    mul = habla.marcar_muletillas(h["palabras"])
    ev = [{"t": p["start"], "tipo": "muletilla", "detalle": p["w"]} for p, m in zip(h["palabras"], mul) if m][:10]
    est_f = "fail" if "fail" in est else "warn" if "warn" in est else "pass"
    return {"estado": est_f, "motivo": "; ".join(mot) or "dicción clara, sin exceso de muletillas",
            "valores": {k: round(v, 3) if isinstance(v, float) else v for k, v in r.items()}, "eventos": ev}


def _marcadores(f: dict, crit: dict, gui: dict) -> list[dict]:
    m = []
    pal = (f.get("habla") or {}).get("palabras", [])
    nombre = Path(f["archivo"]).stem
    if len(pal) >= 3:
        m.append({"t": pal[0]["start"], "tipo": "Inicio de escena", "texto": "empieza a hablar"})
        m.append({"t": pal[-1]["end"], "tipo": "Fin de escena", "texto": "termina de hablar"})
    esc = gui.get("valores", {}).get("escena")
    coincide = gui.get("estado") != "fail"   # solo se asigna escena/importancia si la toma realmente es esa línea
    if esc and coincide:
        m.append({"t": pal[0]["start"] if pal else 0.0, "tipo": "Número de escena", "texto": f"escena {esc} del guion"})
    if gui.get("valores", {}).get("importante") and pal and coincide:
        m.append({"t": pal[0]["start"], "tipo": "Información valiosa", "texto": "línea marcada como clave en el guion"})
    cod = re.match(r"^([A-Za-z]{0,4}\d{1,4}[A-Za-z]?)(?=[_\-\s.])", nombre)
    if cod:
        m.append({"t": 0.0, "tipo": "Código de video", "texto": cod.group(1)})
    if len(pal) < 3 or re.search(r"(?i)(^|[_\-\s])(tp|paso)([_\-\s]|$)", nombre):
        m.append({"t": 0.0, "tipo": "Toma de paso", "texto": "sin diálogo: plano de apoyo (B-roll)"})
    for cid, c in crit.items():
        if c["estado"] == "pass":
            continue
        for e in c.get("eventos", []):
            m.append({"t": float(e["t"]), "tipo": f"Problema · {CRITERIOS[cid]['nombre']}", "texto": f"{e['tipo']}: {e['detalle']}"})
    return sorted(m, key=lambda x: x["t"])


def semaforo(crit: dict) -> tuple[str, float]:
    """Rojo si falla un criterio de importancia alta; amarillo si hay dudas o falla uno medio; verde si todo cumple."""
    altas_fail = [c for c, v in crit.items() if v["estado"] == "fail" and CRITERIOS[c]["importancia"] == "alta"]
    medias_fail = [c for c, v in crit.items() if v["estado"] == "fail" and CRITERIOS[c]["importancia"] != "alta"]
    warns = [c for c, v in crit.items() if v["estado"] == "warn"]
    if altas_fail:
        return "rojo", 0.9 if len(altas_fail) > 1 or not warns else 0.75
    if medias_fail or len(warns) >= 2 or any(CRITERIOS[c]["importancia"] == "alta" for c in warns):
        return "amarillo", 0.6
    return "verde", 0.9 if not warns else 0.7


def motivo_texto(sem: str, crit: dict) -> str:
    peor = {"rojo": "fail", "amarillo": "warn", "verde": "pass"}[sem]
    partes = []
    for cid in ("sonido", "guion", "color", "movimiento", "imagen", "pronunciacion", "encuadre"):
        v = crit.get(cid)
        if not v:
            continue
        if v["estado"] == "fail" or (sem != "rojo" and v["estado"] == "warn"):
            partes.append(f"{CRITERIOS[cid]['nombre']}: {v['motivo']}")
    if not partes and sem != "verde":
        partes = [f"{CRITERIOS[c]['nombre']}: {v['motivo']}" for c, v in crit.items() if v["estado"] == "warn"]
    return " | ".join(partes[:3]) if partes else "Cumple todos los criterios (imagen, audio y guion)."


def clasificar_clip(path: Path, proy: Path, gui: list[dict], opciones: dict, log=print) -> dict:
    f = ficha(path, proy / "fichas", True, opciones.get("modelo", "small"), opciones.get("idioma", "es"), log)
    crit = {k: v for k, v in f["criterios"].items()}
    crit["pronunciacion"] = _pronunciacion(f.get("habla"))
    texto = " ".join(p["w"] for p in (f.get("habla") or {}).get("palabras", []))
    paso = len((f.get("habla") or {}).get("palabras", [])) < 3
    if paso:   # toma de apoyo (B-roll, plano de paso): no hay diálogo que comparar con el guion
        nota = "toma de paso (sin diálogo): no aplica"
        crit["guion"] = {"estado": "pass", "motivo": nota, "valores": {}, "eventos": []}
        crit["pronunciacion"] = {"estado": "pass", "motivo": nota, "valores": {}, "eventos": []}
        if not f["tiene_audio"]:
            crit["sonido"] = {"estado": "pass", "motivo": "sin pista de audio (toma de apoyo): no aplica", "valores": {}, "eventos": []}
        elif crit["sonido"]["estado"] != "pass" and crit["sonido"]["valores"]:
            crit["sonido"] = {**crit["sonido"], "estado": "warn" if crit["sonido"]["estado"] == "fail" else crit["sonido"]["estado"],
                              "motivo": crit["sonido"]["motivo"] + " (sin diálogo: se avisa pero no descarta)"}
    else:
        crit["guion"] = G.fidelidad(texto, gui, opciones.get("juez", "difuso"))
    sem, conf = semaforo(crit)
    return {"tipo": "paso" if paso else "dialogo", "archivo": f["archivo"], "nombre": f["nombre"], "duracion": round(f["duracion"], 2), "ancho": f["ancho"],
            "alto": f["alto"], "semaforo": sem, "confianza": conf, "motivo": motivo_texto(sem, crit),
            "criterios": crit, "marcadores": _marcadores(f, crit, crit["guion"]), "texto": texto}


def clasificar_carpeta(proyecto: str, carpeta: Path, guion_path: Path | None, opciones: dict, log=print) -> dict:
    proy = DATA / proyecto
    gui = G.leer_guion(guion_path) if guion_path else []
    log(f"Guion: {len(gui)} líneas" if gui else "Sin guion: el criterio «Fiel al guion» quedará como dudoso")
    clips = list_clips(carpeta)
    log(f"{len(clips)} clips en {carpeta}")
    resultados = []
    for i, c in enumerate(clips, 1):
        log(f"[{i}/{len(clips)}] {c.name}")
        try:
            resultados.append(clasificar_clip(c, proy, gui, opciones, log))
        except Exception as e:   # un clip dañado no debe parar el lote
            log(f"  ✗ {c.name}: {e}")
            resultados.append({"archivo": str(c), "nombre": c.name, "semaforo": "amarillo", "confianza": 0.2,
                               "motivo": f"No se pudo analizar el archivo ({e}). Revisar a mano.", "criterios": {}, "marcadores": [],
                               "duracion": 0, "texto": ""})
    salida = {"proyecto": proyecto, "carpeta": str(carpeta), "guion": str(guion_path) if guion_path else None,
              "guion_lineas": gui, "opciones": opciones, "tomas": resultados}
    write_json(proy / "clasificacion.json", salida)
    return salida


def aplicar_revision(proyecto: str, nombre: str, semaforo_humano: str, nota: str = "") -> dict:
    """Guarda la decisión de la persona: sirve para calibrar los umbrales con su criterio."""
    p = DATA / proyecto / "revision.json"
    rev = read_json(p, {})
    rev[nombre] = {"semaforo": semaforo_humano, "nota": nota}
    write_json(p, rev)
    return rev


def exportar_carpetas(proyecto: str, destino: Path | None = None) -> dict:
    """Crea buenas / malas / por_revisar con enlaces duros (no ocupan espacio) a los clips originales."""
    proy = DATA / proyecto
    datos = read_json(proy / "clasificacion.json", {})
    rev = read_json(proy / "revision.json", {})
    destino = destino or proy / "salida"
    if destino.exists():
        shutil.rmtree(destino)
    cuenta = {"buenas": 0, "malas": 0, "por_revisar": 0}
    for t in datos.get("tomas", []):
        sem = rev.get(t["nombre"], {}).get("semaforo", t["semaforo"])
        carpeta = {"verde": "buenas", "rojo": "malas"}.get(sem, "por_revisar")
        d = destino / carpeta
        d.mkdir(parents=True, exist_ok=True)
        src = Path(t["archivo"])
        try:
            os.link(src, d / src.name)
        except OSError:
            (d / src.name).symlink_to(src)
        cuenta[carpeta] += 1
    return {"destino": str(destino), **cuenta}


def concordancia(proyecto: str) -> dict:
    """Cuántas veces la persona coincide con la IA (para mostrar la calibración en la demo)."""
    proy = DATA / proyecto
    datos, rev = read_json(proy / "clasificacion.json", {}), read_json(proy / "revision.json", {})
    pares = [(t["semaforo"], rev[t["nombre"]]["semaforo"]) for t in datos.get("tomas", []) if t["nombre"] in rev]
    ok = sum(1 for a, b in pares if a == b)
    return {"revisadas": len(pares), "coinciden": ok, "pct": round(100 * ok / len(pares)) if pares else None}
