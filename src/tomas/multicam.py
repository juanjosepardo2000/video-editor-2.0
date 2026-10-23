"""Servicio 2: orden multicámara. Coloca clips de varias cámaras (desordenados) en una línea de tiempo común.

Método: correlación cruzada del audio (GCC-PHAT) entre clips de cámaras distintas; como todas oyen la misma voz,
el pico de correlación da el desfase exacto. Con los desfases se arma un árbol de sincronización. Los clips sin audio
no se pueden sincronizar por sonido: se ubican de forma estimada por su hora de creación y se marcan como tales.
"""
import re
from pathlib import Path

import numpy as np

from . import audio as A
from .util import DATA, list_clips, probe, write_json

SR = 4000
CONF_OK, CONF_DUDOSA = 9.0, 5.0     # relación pico/ruido de la correlación
MIN_SOLAPE = 2.0                    # s de audio común mínimos para fiarse


def _camara(path: Path, raiz: Path, meta: dict) -> str:
    rel = path.relative_to(raiz)
    if len(rel.parts) > 1:
        return rel.parts[0]
    m = re.match(r"^([A-Za-z]+)", path.stem)
    if meta.get("camara"):
        return str(meta["camara"])
    return m.group(1).upper() if m else "CAM"


def _pre(x: np.ndarray) -> np.ndarray:
    """Normaliza el audio para correlacionar: sin media, con compresión suave (la ganancia de cada micro varía)."""
    x = x - x.mean()
    return np.sign(x) * np.sqrt(np.abs(x))


def gcc_phat(a: np.ndarray, b: np.ndarray) -> tuple[float, float, float]:
    """Desfase d = inicio(b) − inicio(a) en segundos, confianza (pico/mediana) y valor del pico."""
    from scipy.fft import irfft, next_fast_len, rfft
    n = next_fast_len(len(a) + len(b))
    fa, fb = rfft(_pre(a), n), rfft(_pre(b), n)
    r = fa * np.conj(fb)
    r /= np.maximum(np.abs(r), 1e-9)
    # solo frecuencias de voz (150–1800 Hz)
    f = np.fft.rfftfreq(n, 1 / SR)
    r[(f < 150) | (f > 1800)] = 0
    c = irfft(r, n)
    c = np.abs(c)
    i = int(np.argmax(c))
    lag = i if i < n // 2 else i - n
    # confianza: pico frente al nivel típico del resto de la correlación
    resto = np.delete(c, slice(max(i - 20, 0), i + 20)) if i + 20 < n else c[:i - 20]
    conf = float(c[i] / (np.median(resto) * 4.5 + 1e-12))
    return lag / SR, conf, float(c[i])


def analizar(proyecto: str, carpeta: Path, opciones: dict | None = None, log=print) -> dict:
    opciones = opciones or {}
    proy = DATA / proyecto
    clips = list_clips(carpeta)
    if len(clips) < 2:
        raise ValueError("Hacen falta al menos 2 clips en la carpeta.")
    info = []
    for p in clips:
        m = probe(p)
        cam = opciones.get("camaras", {}).get(p.name) or _camara(p, carpeta, m)
        info.append({**m, "archivo": str(p), "nombre": p.name, "camara": cam})
    nombres = sorted({i["camara"] for i in info})
    for i in info:
        i["camara"] = f"Cámara {nombres.index(i['camara']) + 1}" if len(nombres) <= 9 else i["camara"]
    log(f"{len(info)} clips · {len(nombres)} cámaras detectadas ({', '.join(nombres)})")
    for i in info:
        if i["tiene_audio"] and i["duracion"] > 1:
            i["_x"] = A.leer(i["archivo"], 0, min(i["duracion"], 1800), SR)
        else:
            i["_x"] = None
    # desfases entre clips de cámaras distintas (o entre clips de la misma si no hay otra forma)
    aristas = []
    for a in range(len(info)):
        for b in range(a + 1, len(info)):
            if info[a]["camara"] == info[b]["camara"] or info[a]["_x"] is None or info[b]["_x"] is None:
                continue
            d, conf, _ = gcc_phat(info[a]["_x"], info[b]["_x"])
            ta, tb = info[a]["duracion"], info[b]["duracion"]
            solape = min(ta, d + tb) - max(0.0, d)
            ok = solape >= MIN_SOLAPE and conf >= CONF_DUDOSA
            log(f"  {info[a]['nombre']} ↔ {info[b]['nombre']}: desfase {d:+.2f} s, confianza {conf:.1f}, solape {solape:.1f} s" + ("" if ok else " (descartado)"))
            if ok:
                aristas.append({"a": a, "b": b, "d": d, "conf": conf, "solape": solape})
    # árbol de sincronización: se parte del clip con más enlaces y se añaden los enlaces más fiables
    pos: dict[int, float] = {}
    comp: dict[int, int] = {}
    conf_clip: dict[int, float] = {}
    pendientes = set(range(len(info)))
    cid = 0
    while pendientes:
        grado = {i: sum(1 for e in aristas if i in (e["a"], e["b"])) for i in pendientes if info[i]["_x"] is not None}
        if not grado or max(grado.values()) == 0:
            break
        raiz = max(grado, key=lambda i: (grado[i], info[i]["duracion"]))
        pos[raiz], comp[raiz], conf_clip[raiz] = 0.0, cid, 99.0
        pendientes.discard(raiz)
        creciendo = True
        while creciendo:
            creciendo = False
            cand = [e for e in aristas if (e["a"] in pos) != (e["b"] in pos) and comp.get(e["a"], comp.get(e["b"])) == cid]
            if cand:
                e = max(cand, key=lambda e: e["conf"])
                if e["a"] in pos:
                    pos[e["b"]], comp[e["b"]], conf_clip[e["b"]] = pos[e["a"]] + e["d"], cid, e["conf"]
                    pendientes.discard(e["b"])
                else:
                    pos[e["a"]], comp[e["a"]], conf_clip[e["a"]] = pos[e["b"]] - e["d"], cid, e["conf"]
                    pendientes.discard(e["a"])
                creciendo = True
        cid += 1
    # clips sin enlace por audio: se estiman por hora de creación respecto a un clip ya colocado de otra cámara
    from datetime import datetime
    def hora(i):
        try:
            return datetime.fromisoformat(info[i]["creado"].replace("Z", "+00:00")).timestamp() if info[i].get("creado") else None
        except ValueError:
            return None
    sin_sincronizar = []
    for i in sorted(pendientes):
        ref = next((j for j in pos if hora(j) is not None and hora(i) is not None), None)
        if ref is not None:
            pos[i], comp[i], conf_clip[i] = pos[ref] + (hora(i) - hora(ref)), comp[ref], 0.0
            info[i]["metodo"] = "estimado por hora de creación (poco fiable)"
        else:
            sin_sincronizar.append(i)
    # cada componente empieza en 0; los componentes sueltos se apilan uno tras otro
    lineas, cursor = [], 0.0
    for c in sorted(set(comp.values())):
        miembros = [i for i in comp if comp[i] == c]
        base = min(pos[i] for i in miembros)
        fin = max(pos[i] - base + info[i]["duracion"] for i in miembros)
        for i in miembros:
            info[i]["inicio"] = round(pos[i] - base + cursor, 3)
            info[i]["grupo"] = c + 1
            info[i]["confianza"] = round(conf_clip[i], 1)
            info[i].setdefault("metodo", "audio (GCC-PHAT)" if conf_clip[i] >= CONF_OK else "audio (confianza media)" if conf_clip[i] >= CONF_DUDOSA else "estimado")
        cursor += fin + 5.0
    for i in sin_sincronizar:
        info[i]["inicio"] = round(cursor, 3)
        info[i]["grupo"] = None
        info[i]["confianza"] = 0.0
        info[i]["metodo"] = "sin audio y sin hora: colocar a mano" if not info[i]["tiene_audio"] else "sin solape con otros clips"
        cursor += info[i]["duracion"] + 2.0
    for i in info:
        i.pop("_x", None)
        i["fin"] = round(i["inicio"] + i["duracion"], 3)
    orden = sorted(info, key=lambda i: (i["inicio"], i["camara"]))
    pistas: dict[str, list] = {}
    for i in orden:
        pistas.setdefault(i["camara"], []).append(i["nombre"])
    res = {"proyecto": proyecto, "carpeta": str(carpeta), "camaras": sorted(pistas), "clips": orden, "pistas": pistas,
           "resumen": {"clips": len(info), "camaras": len(pistas),
                       "sincronizados_por_audio": sum(1 for i in info if i["metodo"].startswith("audio")),
                       "estimados": sum(1 for i in info if i["metodo"].startswith("estimado")),
                       "manual": sum(1 for i in info if i["metodo"].startswith("sin")),
                       "duracion_total": round(max(i["fin"] for i in info), 1)},
           "aristas": [{"a": info[e["a"]]["nombre"], "b": info[e["b"]]["nombre"], "desfase": round(e["d"], 3),
                        "confianza": round(e["conf"], 1)} for e in aristas]}
    write_json(proy / "multicam/multicam.json", res)
    return res
