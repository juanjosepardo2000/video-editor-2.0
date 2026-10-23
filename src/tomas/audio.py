"""Métricas de audio de un clip: volumen, saturación, ruido de fondo (SNR) y golpes graves (viento/popping)."""
import re
import subprocess

import numpy as np

from .util import CONFIG

U = CONFIG["umbrales"]
SR = 16000
MAX_SEG = 1200  # se analizan como máximo 20 min por clip


def leer(path, ss: float = 0.0, t: float | None = None, sr: int = SR) -> np.ndarray:
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{ss:.2f}"] + (["-t", f"{t:.2f}"] if t else []) + \
          ["-i", str(path), "-vn", "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    return np.frombuffer(raw[: len(raw) // 2 * 2], dtype=np.int16).astype(np.float32) / 32768.0


def _lufs(path, t: float | None) -> tuple[float | None, float | None]:
    cmd = ["ffmpeg", "-nostats", "-i", str(path)] + (["-t", f"{t:.0f}"] if t else []) + \
          ["-vn", "-af", "ebur128=peak=true", "-f", "null", "-"]
    err = subprocess.run(cmd, capture_output=True, text=True).stderr
    i = re.search(r"I:\s+(-?\d+\.?\d*) LUFS", err[err.rfind("Summary"):] if "Summary" in err else "")
    p = re.search(r"Peak:\s+(-?\d+\.?\d*) dBFS", err[err.rfind("Summary"):] if "Summary" in err else "")
    return (float(i.group(1)) if i else None, float(p.group(1)) if p else None)


def _worst(estados):
    return "fail" if "fail" in estados else "warn" if "warn" in estados else "pass"


def analizar_audio(path, dur: float, tiene_audio: bool) -> dict:
    if not tiene_audio:
        return {"sonido": {"estado": "fail", "motivo": "el clip no tiene pista de audio", "valores": {}, "eventos": []},
                "_voz": np.zeros(0, dtype=np.float32)}
    x = leer(path, 0, min(dur, MAX_SEG))
    if len(x) < SR // 2:
        return {"sonido": {"estado": "warn", "motivo": "audio demasiado corto para medirlo", "valores": {}, "eventos": []}, "_voz": x}
    win = SR // 20
    n = len(x) // win
    fr = x[: n * win].reshape(n, win)
    rms = np.sqrt((fr ** 2).mean(axis=1) + 1e-12)
    db = 20 * np.log10(rms)
    vivo = db > -80
    piso = float(np.percentile(db[vivo], 10)) if vivo.any() else -90.0
    voz = float(np.percentile(db[vivo], 90)) if vivo.any() else -90.0
    snr = voz - piso
    activo = db > piso + 10
    # saturación: muestras al tope + tramos planos
    tope = float((np.abs(x) >= 0.985).mean())
    lufs, pico = _lufs(path, MAX_SEG if dur > MAX_SEG else None)
    # golpes graves: energía < 120 Hz dominante en una ventana con nivel alto (viento, popping, roces)
    spec = np.abs(np.fft.rfft(fr * np.hanning(win), axis=1)) ** 2
    freqs = np.fft.rfftfreq(win, 1 / SR)
    bajos = spec[:, (freqs >= 20) & (freqs <= 120)].sum(axis=1)
    ratio = bajos / np.maximum(spec.sum(axis=1), 1e-12)
    graves = (ratio > 0.65) & (db > piso + 14)
    frac_graves = float(graves.sum() / max(activo.sum(), 1))
    estados, motivos = [], []
    if snr < U["snr_fail"]:
        estados.append("fail"); motivos.append(f"mucho ruido de fondo (relación señal/ruido {snr:.0f} dB)")
    elif snr < U["snr_warn"]:
        estados.append("warn"); motivos.append(f"ruido de fondo perceptible (relación señal/ruido {snr:.0f} dB)")
    if voz < U["voz_baja_fail_db"]:
        estados.append("fail"); motivos.append(f"volumen muy bajo (voz a {voz:.0f} dBFS)")
    elif voz < U["voz_baja_warn_db"]:
        estados.append("warn"); motivos.append(f"volumen bajo (voz a {voz:.0f} dBFS)")
    if tope >= U["clip_audio_fail"] or (pico is not None and pico > U["pico_fail_dbtp"] and tope >= U["clip_audio_warn"]):
        estados.append("fail"); motivos.append(f"audio saturado ({tope*100:.2f}% de muestras al tope)")
    elif tope >= U["clip_audio_warn"] or (pico is not None and pico > -0.1):
        estados.append("warn"); motivos.append(f"picos al límite (pico {pico} dBFS)")
    if frac_graves >= U["graves_fail"]:
        estados.append("fail"); motivos.append(f"golpes graves (viento, roces o popping) en {frac_graves*100:.0f}% del habla")
    elif frac_graves >= U["graves_warn"]:
        estados.append("warn"); motivos.append(f"algunos golpes graves (viento/popping) en {frac_graves*100:.0f}% del habla")
    eventos = [{"t": round(i * 0.05, 2), "tipo": "golpe grave", "detalle": "viento/roce/popping"} for i in np.where(graves)[0]]
    eventos = _agrupar(eventos)[:8]
    return {"sonido": {"estado": _worst(estados), "motivo": "; ".join(motivos) or "sonido limpio y estable",
                       "valores": {"snr_db": round(snr, 1), "voz_dbfs": round(voz, 1), "piso_dbfs": round(piso, 1),
                                   "lufs": lufs, "pico_dbfs": pico, "saturado": round(tope, 5), "graves": round(frac_graves, 3)},
                       "eventos": eventos},
            "_voz": x}


def _agrupar(ev: list[dict], gap: float = 0.5) -> list[dict]:
    out = []
    for e in ev:
        if out and e["t"] - out[-1]["t"] <= gap:
            out[-1]["t"] = max(out[-1]["t"], e["t"])
            continue
        out.append(dict(e))
    return out


def energia_entre(x: np.ndarray, a: float, b: float, piso_db: float) -> float:
    """Nivel (dB sobre el piso) en el hueco [a, b]; sirve para distinguir silencio de respiración fuerte."""
    seg = x[int(a * SR): int(b * SR)]
    if len(seg) < SR // 100:
        return -99.0
    return float(20 * np.log10(np.sqrt((seg ** 2).mean()) + 1e-9) - piso_db)
