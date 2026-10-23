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
    """Rojo si falla un criterio de importancia alta o uno crítico; amarillo si hay dudas o falla uno medio; verde si todo cumple."""
    altas_fail = [c for c, v in crit.items() if v["estado"] == "fail" and (CRITERIOS[c]["importancia"] == "alta" or v.get("critico"))]
    medias_fail = [c for c, v in crit.items() if v["estado"] == "fail" and c not in altas_fail]
    warns = [c for c, v in crit.items() if v["estado"] == "warn"]
    if altas_fail:
        return "rojo", 0.9 if len(altas_fail) > 1 or not warns else 0.75
    if medias_fail or len(warns) >= 2 or any(CRITERIOS[c]["importancia"] == "alta" for c in warns):
        return "amarillo", 0.6
    return "verde", 0.9 if not warns else 0.7


ORDEN = ("completa", "guion", "encuadre", "sonido", "color", "movimiento", "imagen", "pronunciacion")


def motivo_texto(sem: str, crit: dict) -> str:
    partes = []
    for cid in ORDEN:
        v = crit.get(cid)
        if v and (v["estado"] == "fail" or (sem != "rojo" and v["estado"] == "warn")):
            partes.append(f"{CRITERIOS[cid]['nombre']}: {v['motivo']}")
    if not partes and sem != "verde":
        partes = [f"{CRITERIOS[c]['nombre']}: {v['motivo']}" for c, v in crit.items() if v["estado"] == "warn"]
    return " | ".join(partes[:3]) if partes else "Cumple todos los criterios (imagen, audio y guion)."


def _encuadre_hablante(base: dict) -> dict:
    """Con diálogo, lo primero es que se vea al hablante: rostro en la mayoría de los fotogramas, de buen tamaño y sin cortar."""
    c = (base.get("valores") or {}).get("caras") or {}
    if c.get("ratio") is None:
        return base
    ratio, n = c["ratio"], c["n"]
    vistos = round(ratio * n)
    val = {**base["valores"]}
    if ratio < U["cara_ratio_fail"]:
        return {"estado": "fail", "critico": True, "valores": val, "eventos": base.get("eventos", []),
                "motivo": f"no se ve al hablante: su rostro aparece solo en {vistos} de {n} fotogramas (cámara mal apuntada, hablante fuera de cuadro o de espaldas)"}
    avisos = []
    if ratio < U["cara_ratio_warn"]:
        avisos.append(f"el hablante sale de cuadro o gira la cara ({vistos} de {n} fotogramas con rostro)")
    if c["h"] < U["cara_h_warn"]:
        avisos.append(f"hablante muy lejos (rostro de {c['h']*100:.1f}% de la altura)")
    if c["top"] is not None and c["top"] < U["cara_top_warn"]:
        avisos.append("cabeza pegada al borde superior")
    if c["cx"] is not None and (c["cx"] < 0.2 or c["cx"] > 0.8):
        avisos.append("hablante muy desplazado a un lado")
    if avisos:
        return {"estado": "warn", "valores": val, "eventos": base.get("eventos", []), "motivo": "; ".join(avisos)}
    return {"estado": "pass", "valores": val, "eventos": base.get("eventos", []),
            "motivo": f"hablante visible y bien encuadrado ({vistos} de {n} fotogramas)"}


def _completa(f: dict, cov: float | None) -> dict:
    """Duración útil y que la toma no se corte a media frase ni termine en conversación de rodaje."""
    dur = f["duracion"]
    pal = (f.get("habla") or {}).get("palabras", [])
    est, mot, ev = "pass", [], []
    if dur < U["dur_fail"]:
        est = "fail"; mot.append(f"dura solo {dur:.1f} s: demasiado corta para usarla")
    elif dur < U["dur_warn"]:
        est = "warn"; mot.append(f"dura solo {dur:.1f} s")
    if len(pal) >= 3:
        ult = pal[-1]
        cortada = (dur - ult["end"]) < 0.3 and not ult["w"].rstrip().endswith((".", "?", "!", "…"))
        if cortada:
            ev.append({"t": round(ult["end"], 2), "tipo": "corte", "detalle": "la toma termina hablando"})
            if cov is not None and cov < U["cob_corte"]:
                est = "fail"; mot.append("la frase se corta a la mitad: el actor no termina de decirla")
            elif est != "fail":
                est = "warn"; mot.append("termina cortada: la grabación para mientras habla")
    if dur > U["dur_larga"] and est == "pass":
        est = "warn"; mot.append(f"toma muy larga ({dur:.0f} s): probablemente varias tomas juntas")
    return {"estado": est, "motivo": "; ".join(mot) or "dura lo suficiente y termina limpia", "valores": {"duracion": round(dur, 2)}, "eventos": ev}


def clasificar_clip(path: Path, proy: Path, gui: list[dict], opciones: dict, log=print) -> dict:
    f = ficha(path, proy / "fichas", True, opciones.get("modelo", "small"), opciones.get("idioma", "es"), log)
    crit = {k: v for k, v in f["criterios"].items()}
    pal = (f.get("habla") or {}).get("palabras", [])
    texto = " ".join(p["w"] for p in pal)
    tipo, cov = "dialogo", None
    if len(pal) < 3:
        tipo = "paso"                       # sin diálogo: plano de apoyo (B-roll)
    else:
        g = G.fidelidad(texto, gui, opciones.get("juez", "difuso")) if gui else None
        cov = g["valores"].get("cobertura") if g and g["valores"] else None
        if g and (cov or 0) < U["habla_ajena_cob"]:
            tipo = "paso_inferido"          # hay voz, pero no es del guion: conversación de rodaje sobre un plano de apoyo
        crit["pronunciacion"] = _pronunciacion(f.get("habla"))
        crit["guion"] = g or {"estado": "pass", "motivo": "sin guion cargado: no se evalúa", "valores": {}, "eventos": []}
    if tipo in ("paso", "paso_inferido"):
        nota = "toma de paso (sin diálogo del guion): no aplica" if tipo == "paso" else "habla ajena al guion (conversación de rodaje): se trata como plano de apoyo"
        crit["guion"] = {"estado": "pass", "motivo": nota, "valores": {}, "eventos": []}
        crit["pronunciacion"] = {"estado": "pass", "motivo": nota, "valores": {}, "eventos": []}
        if not f["tiene_audio"]:
            crit["sonido"] = {"estado": "pass", "motivo": "sin pista de audio (toma de apoyo): no aplica", "valores": {}, "eventos": []}
        elif crit["sonido"]["estado"] == "fail" and crit["sonido"]["valores"]:
            crit["sonido"] = {**crit["sonido"], "estado": "warn", "motivo": crit["sonido"]["motivo"] + " (plano de apoyo: se avisa pero no descarta)"}
    else:
        crit["encuadre"] = _encuadre_hablante(crit["encuadre"])
    crit["completa"] = _completa(f, cov if tipo == "dialogo" else None)
    sem, conf = semaforo(crit)
    motivo = motivo_texto(sem, crit)
    if tipo == "paso_inferido":
        if sem == "verde":
            sem, conf = "amarillo", 0.5
        motivo = "Plano de apoyo con conversación de rodaje: revisar si sirve como B-roll. " + (motivo if sem != "verde" and not motivo.startswith("Cumple") else "")
    return {"tipo": tipo, "archivo": f["archivo"], "nombre": f["nombre"], "duracion": round(f["duracion"], 2), "ancho": f["ancho"],
            "alto": f["alto"], "semaforo": sem, "confianza": conf, "motivo": motivo.strip(),
            "criterios": crit, "marcadores": _marcadores(f, crit, crit["guion"]), "texto": texto}


PESO = {"alta": 2.0, "media": 1.0}
PUNTOS = {"pass": 1.0, "warn": 0.5, "fail": 0.0}


def _ranking(tomas: list[dict]) -> None:
    """Entre varias tomas de la misma línea del guion, marca cuál es la mejor (las demás son alternativas)."""
    grupos: dict[int, list[dict]] = {}
    for t in tomas:
        if t.get("tipo") == "dialogo" and t["criterios"].get("guion", {}).get("valores", {}).get("lineas"):
            grupos.setdefault(t["criterios"]["guion"]["valores"]["lineas"][0], []).append(t)
    for linea, ts in grupos.items():
        def puntaje(t):
            return sum(PUNTOS[v["estado"]] * PESO.get(CRITERIOS[k]["importancia"], 1.0) for k, v in t["criterios"].items()) \
                + 2 * t["criterios"]["guion"]["valores"].get("cobertura", 0)
        ordenadas = sorted(ts, key=puntaje, reverse=True)
        for i, t in enumerate(ordenadas):
            t["ranking"] = {"linea": linea, "puesto": i + 1, "de": len(ts), "mejor": ordenadas[0]["nombre"]}
            if len(ts) > 1 and t["semaforo"] != "rojo":
                t["motivo"] += (f"  ★ Mejor de {len(ts)} tomas de la línea {linea}." if i == 0
                                else f"  Hay una toma mejor de esta línea: {ordenadas[0]['nombre']}.")


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
    _ranking([t for t in resultados if "criterios" in t and t["criterios"]])
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
