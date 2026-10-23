"""Métricas de imagen de un clip: exposición/color, nitidez/ruido, estabilidad y encuadre.

Todo se calcula sobre fotogramas muestreados con ffmpeg (no se decodifica el clip entero) y se compara con los
umbrales de config/criterios.json. Son heurísticas: lo dudoso se marca "warn" para que lo revise una persona.
"""
import subprocess
from functools import lru_cache
from pathlib import Path

import numpy as np

from .util import CONFIG, probe

U = CONFIG["umbrales"]


def _frames(path, fps: float, width: int, gray: bool, ss: float = 0.0, t: float | None = None) -> np.ndarray:
    """Devuelve (n, h, w[, 3]) uint8. El alto se deduce con ffprobe del escalado (relación de aspecto real)."""
    vf = f"fps={fps},scale={width}:-2" + (",format=gray" if gray else ",format=rgb24")
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{ss:.2f}"] + (["-t", f"{t:.2f}"] if t else []) + \
          ["-i", str(path), "-an", "-vf", vf, "-f", "rawvideo", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    return raw


@lru_cache(maxsize=64)
def _size(path, width: int) -> tuple[int, int]:
    """Tamaño de los fotogramas tras escalar a `width` (respeta la rotación del clip)."""
    m = probe(Path(path))
    if not m["ancho"] or not m["alto"]:
        return width, int(width * 9 / 16) // 2 * 2
    return width, max(2, round(width * m["alto"] / m["ancho"] / 2) * 2)


def sample(path, dur: float, fps: float, width: int, gray: bool, max_frames: int = 90) -> np.ndarray:
    w, h = _size(path, width)
    eff = min(fps, max(max_frames / max(dur, 0.1), 0.05))
    raw = _frames(path, eff, width, gray)
    ch = 1 if gray else 3
    n = len(raw) // (w * h * ch)
    arr = np.frombuffer(raw[: n * w * h * ch], dtype=np.uint8)
    return arr.reshape((n, h, w) if gray else (n, h, w, 3))


def motion_windows(path, dur: float, width: int = 320) -> list[np.ndarray]:
    """Ventanas contiguas de fotogramas a 6 fps (hasta 5 ventanas de 20 s) para medir la estabilidad."""
    w, h = _size(path, width)
    if dur <= 100:
        starts, length = [0.0], None
    else:
        starts, length = [dur * k / 5 for k in range(5)], 20.0
    out = []
    for ss in starts:
        raw = _frames(path, 6, width, True, ss, length)
        n = len(raw) // (w * h)
        if n >= 3:
            out.append(np.frombuffer(raw[: n * w * h], dtype=np.uint8).reshape(n, h, w))
    return out


def _laplacian_var(g: np.ndarray) -> float:
    g = g.astype(np.float32)
    lap = g[1:-1, 1:-1] * 4 - g[:-2, 1:-1] - g[2:, 1:-1] - g[1:-1, :-2] - g[1:-1, 2:]
    return float(lap.var())


def _noise_sigma(g: np.ndarray) -> float:
    """Estimación de ruido de Immerkaer (sigma en niveles 0-255)."""
    g = g.astype(np.float32)
    k = (g[:-2, :-2] - 2 * g[:-2, 1:-1] + g[:-2, 2:] - 2 * g[1:-1, :-2] + 4 * g[1:-1, 1:-1]
         - 2 * g[1:-1, 2:] + g[2:, :-2] - 2 * g[2:, 1:-1] + g[2:, 2:])
    h, w = g.shape
    return float(np.sqrt(np.pi / 2) * np.abs(k).sum() / (6.0 * (w - 2) * (h - 2)))


def _status(value: float, warn: float, fail: float, higher_is_worse: bool = True) -> str:
    if higher_is_worse:
        return "fail" if value >= fail else "warn" if value >= warn else "pass"
    return "fail" if value <= fail else "warn" if value <= warn else "pass"


def exposicion_color(rgb: np.ndarray, times: list[float]) -> dict:
    f = rgb.astype(np.float32) / 255.0
    luma = 0.2126 * f[..., 0] + 0.7152 * f[..., 1] + 0.0722 * f[..., 2]
    mean_l = luma.mean(axis=(1, 2))
    med = float(np.median(mean_l))
    sat_hi = float((luma > 0.97).mean())
    sat_lo = float((luma < 0.03).mean())
    n, h, w = luma.shape
    cy0, cy1, cx0, cx1 = int(h * .25), int(h * .75), int(w * .25), int(w * .75)
    centro = luma[:, cy0:cy1, cx0:cx1].mean(axis=(1, 2))
    mask = np.ones((h, w), bool)
    mask[cy0:cy1, cx0:cx1] = False
    anillo = luma[:, mask].mean(axis=1)
    contraluz = float(np.median(centro / np.maximum(anillo, 1e-3)))
    means = f.mean(axis=(0, 1, 2))
    dom = float(max(abs(means[0] / max(means[1], 1e-3) - 1), abs(means[2] / max(means[1], 1e-3) - 1)))
    hsv_s = (f.max(axis=-1) - f.min(axis=-1)) / np.maximum(f.max(axis=-1), 1e-3)
    sat = float(hsv_s.mean())
    estados, motivos = [], []
    es = "fail" if med <= U["luma_sub_fail"] else "warn" if med <= U["luma_sub_warn"] else "pass"
    if es != "pass":
        estados.append(es); motivos.append(f"subexpuesta (luminosidad media {med:.2f})")
    es = "fail" if med >= U["luma_sobre_fail"] else "warn" if med >= U["luma_sobre_warn"] else "pass"
    if es != "pass":
        estados.append(es); motivos.append(f"sobreexpuesta (luminosidad media {med:.2f})")
    es = _status(sat_hi, U["clip_alto_warn"], U["clip_alto_fail"])
    if es != "pass":
        estados.append(es); motivos.append(f"{sat_hi*100:.0f}% de la imagen quemada (blancos recortados)")
    if anillo.mean() > 0.45:
        es = _status(contraluz, U["contraluz_ratio_warn"], U["contraluz_ratio_fail"], higher_is_worse=False)
        if es != "pass":
            estados.append(es); motivos.append(f"posible contraluz (centro {contraluz:.2f}× más oscuro que el entorno)")
    es = _status(dom, U["dominante_warn"], U["dominante_fail"])
    if es != "pass":
        estados.append("warn" if es == "fail" else es)   # una dominante puede ser intencional: nunca descarta sola
        motivos.append(f"dominante de color marcada ({dom*100:.0f}%)")
    # fotogramas puntuales con exposición extrema (para marcadores)
    eventos = [{"t": round(times[i], 2), "tipo": "exposicion", "detalle": f"luminosidad {mean_l[i]:.2f}"}
               for i in range(n) if mean_l[i] < U["luma_sub_fail"] or mean_l[i] > U["luma_sobre_fail"]][:6]
    return {"estado": _worst(estados), "motivo": "; ".join(motivos) or "exposición y color dentro de lo normal",
            "valores": {"luma": round(med, 3), "quemado": round(sat_hi, 3), "negro": round(sat_lo, 3),
                        "contraluz": round(contraluz, 2), "dominante": round(dom, 3), "saturacion": round(sat, 3)},
            "eventos": eventos}


def nitidez_ruido(gray: np.ndarray, alto: int, times: list[float]) -> dict:
    lv = np.array([_laplacian_var(g) for g in gray])
    med = float(np.median(lv))
    sig = float(np.median([_noise_sigma(g) for g in gray[:: max(1, len(gray) // 12)]]))
    relativo = float((lv < U["nitidez_rel_warn"] * max(med, 1e-3)).mean())
    estados, motivos = [], []
    es = _status(med, U["nitidez_abs_warn"], U["nitidez_abs_fail"], higher_is_worse=False)
    if es != "pass":
        estados.append(es); motivos.append(f"imagen blanda o desenfocada (nitidez {med:.1f})")
    if relativo > 0.35 and len(gray) >= 6:
        estados.append("warn"); motivos.append(f"el enfoque varía: {relativo*100:.0f}% de los fotogramas pierden nitidez")
    es = _status(sig, U["ruido_sigma_warn"], U["ruido_sigma_fail"])
    if es != "pass":
        estados.append(es); motivos.append(f"grano/ruido alto (σ {sig:.1f})")
    es = _status(alto, U["alto_min_warn"], U["alto_min_fail"], higher_is_worse=False)
    if es != "pass" and alto > 0:
        estados.append("warn" if es == "fail" and alto >= 720 else es); motivos.append(f"resolución baja ({alto}p)")
    eventos = [{"t": round(times[i], 2), "tipo": "desenfoque", "detalle": f"nitidez {lv[i]:.1f}"}
               for i in range(len(lv)) if lv[i] < max(U["nitidez_abs_fail"], 0.35 * med)][:6]
    return {"estado": _worst(estados), "motivo": "; ".join(motivos) or "nítida y limpia",
            "valores": {"nitidez": round(med, 2), "ruido_sigma": round(sig, 2), "alto": alto}, "eventos": eventos}


def _shift(a: np.ndarray, b: np.ndarray, win: np.ndarray) -> tuple[float, float]:
    fa, fb = np.fft.rfft2(a * win), np.fft.rfft2(b * win)
    r = fa * np.conj(fb)
    r /= np.maximum(np.abs(r), 1e-6)
    c = np.fft.irfft2(r, s=a.shape)
    iy, ix = np.unravel_index(np.argmax(c), c.shape)
    h, w = a.shape
    # refinamiento subpíxel con parábola
    def sub(arr, i, n):
        l, m, r_ = arr[(i - 1) % n], arr[i], arr[(i + 1) % n]
        d = l - 2 * m + r_
        return 0.0 if abs(d) < 1e-9 else 0.5 * (l - r_) / d
    dx = ix + sub(c[iy], ix, w)
    dy = iy + sub(c[:, ix], iy, h)
    return (dx - w if dx > w / 2 else dx), (dy - h if dy > h / 2 else dy)


def estabilidad(ventanas: list[np.ndarray], fps: float = 6.0) -> dict:
    if not ventanas:
        return {"estado": "warn", "motivo": "no se pudo medir el movimiento (clip muy corto)", "valores": {}, "eventos": []}
    jit, brusco, tot, eventos, offset = [], 0, 0, [], 0.0
    for v in ventanas:
        h, w = v.shape[1:]
        ph, pw = h // 3, w // 3
        win = np.outer(np.hanning(ph), np.hanning(pw)).astype(np.float32)
        # solo los bordes del cuadro (el hablante se mueve; el fondo delata la cámara): mediana de 6 parches
        parches = [(0, 0), (0, w - pw), (h - ph, 0), (h - ph, w - pw), (0, (w - pw) // 2), (h - ph, (w - pw) // 2)]
        fr = [f.astype(np.float32) for f in v]
        d = np.array([np.median([_shift(fr[i][y:y + ph, x:x + pw], fr[i + 1][y:y + ph, x:x + pw], win) for y, x in parches], axis=0)
                      for i in range(len(fr) - 1)]) / w
        if len(d) < 3:
            continue
        mag = np.hypot(d[:, 0], d[:, 1])
        k = min(5, len(d))
        liso = np.vstack([np.convolve(d[:, c], np.ones(k) / k, mode="same") for c in range(2)]).T
        jit.append(np.hypot(*(d - liso).T))
        sp = mag > 0.06
        brusco += int(sp.sum()); tot += len(d)
        eventos += [{"t": round(offset + (i + 1) / fps, 2), "tipo": "movimiento brusco", "detalle": f"desplazamiento {mag[i]*100:.0f}% del ancho"}
                    for i in np.where(sp)[0][:4]]
        offset += len(v) / fps
    if not tot:
        return {"estado": "warn", "motivo": "no se pudo medir el movimiento", "valores": {}, "eventos": []}
    j = float(np.sqrt(np.mean(np.concatenate(jit) ** 2)))
    fb = brusco / tot
    estados, motivos = [], []
    for val, key, txt in ((j, "jitter", f"cámara temblorosa (vibración {j*100:.2f}% del ancho)"),
                          (fb, "brusco", f"movimientos bruscos en {fb*100:.0f}% del tiempo")):
        es = _status(val, U[f"{key}_warn"], U[f"{key}_fail"])
        if es != "pass":
            estados.append(es); motivos.append(txt)
    return {"estado": _worst(estados), "motivo": "; ".join(motivos) or "cámara estable",
            "valores": {"vibracion": round(j, 5), "bruscos": round(fb, 3)}, "eventos": eventos[:8]}


_FACE = None


def _cascade():
    global _FACE
    if _FACE is None:
        import cv2
        _FACE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    return _FACE


def encuadre(rgb: np.ndarray, gray: np.ndarray) -> dict:
    """Sujeto = rostro (Haar) y, si no hay, el centro de masa de la energía de bordes. Se evalúan tercios y bordes."""
    sujetos, fuente = [], "rostro"
    try:
        import cv2
        det = _cascade()
        for g in gray[:: max(1, len(gray) // 10)]:
            r = det.detectMultiScale(g, 1.2, 5, minSize=(max(18, g.shape[1] // 14),) * 2)
            if len(r):
                x, y, w, h = max(r, key=lambda b: b[2] * b[3])
                H, W = g.shape
                sujetos.append(((x + w / 2) / W, (y + h / 2) / H, y / H, (y + h) / H, x / W, (x + w) / W))
    except ImportError:
        pass
    if len(sujetos) < max(2, len(gray[:: max(1, len(gray) // 10)]) // 4):
        fuente, sujetos = "zona más detallada", []
        for g in gray[:: max(1, len(gray) // 10)]:
            gf = g.astype(np.float32)
            e = np.abs(np.diff(gf, axis=0))[:, :-1] + np.abs(np.diff(gf, axis=1))[:-1, :]
            H, W = e.shape
            ys, xs = np.mgrid[0:H, 0:W]
            tot = e.sum() + 1e-6
            sujetos.append(((e * xs).sum() / tot / W, (e * ys).sum() / tot / H, 0, 1, 0, 1))
    cx, cy, top, bot, left, right = (float(np.median([s[i] for s in sujetos])) for i in range(6))
    d_x = min(abs(cx - 1 / 3), abs(cx - 2 / 3), abs(cx - 0.5))
    d_y = min(abs(cy - 1 / 3), abs(cy - 0.5))
    estados, motivos = [], []
    if fuente == "rostro":
        if top < 0.02:
            estados.append("fail"); motivos.append("cabeza cortada por el borde superior")
        elif top > 0.40:
            estados.append("warn"); motivos.append("demasiado espacio vacío encima del sujeto (mucho cielo/techo)")
        if left < U["borde_fail"] or right > 1 - U["borde_fail"]:
            estados.append("fail"); motivos.append("sujeto pegado al borde lateral")
        elif d_x > U["tercios_tol"]:
            estados.append("warn"); motivos.append(f"sujeto fuera de los tercios (x={cx:.2f})")
        if cy > 0.62:
            estados.append("warn"); motivos.append("sujeto muy bajo en el cuadro (mucho cielo, poco suelo)")
    else:
        if cx < U["borde_fail"] or cx > 1 - U["borde_fail"] or cy < U["borde_fail"] or cy > 1 - U["borde_fail"]:
            estados.append("warn"); motivos.append("lo más relevante parece pegado al borde del cuadro")
        elif d_x > U["tercios_tol"] + 0.05:
            estados.append("warn"); motivos.append("el punto de interés queda lejos de los tercios")
    return {"estado": _worst(estados), "motivo": "; ".join(motivos) or "encuadre equilibrado",
            "valores": {"fuente": fuente, "x": round(cx, 3), "y": round(cy, 3)}, "eventos": []}


def _worst(estados: list[str]) -> str:
    return "fail" if "fail" in estados else "warn" if "warn" in estados else "pass"


def analizar_imagen(path, dur: float, alto: int) -> dict:
    rgb = sample(path, dur, fps=1.0, width=320, gray=False, max_frames=60)
    times = [i * dur / max(len(rgb), 1) for i in range(len(rgb))]
    if not len(rgb):
        return {k: {"estado": "warn", "motivo": "no se pudo leer la imagen", "valores": {}, "eventos": []}
                for k in ("color", "imagen", "movimiento", "encuadre")}
    gray_hi = sample(path, dur, fps=1.0, width=640, gray=True, max_frames=30)
    gray_lo = sample(path, dur, fps=1.0, width=320, gray=True, max_frames=30)
    times_hi = [i * dur / max(len(gray_hi), 1) for i in range(len(gray_hi))]
    return {"color": exposicion_color(rgb, times),
            "imagen": nitidez_ruido(gray_hi, alto, times_hi),
            "movimiento": estabilidad(motion_windows(path, dur)),
            "encuadre": encuadre(rgb, gray_lo)}
