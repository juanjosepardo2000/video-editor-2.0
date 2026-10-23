"""Transcripción con tiempos y confianza por palabra (WhisperX) y detección de muletillas."""
from .util import CONFIG, norm

STRICT = set(CONFIG["muletillas"])
CONTEXT = set(CONFIG["muletillas_contextuales"])
_MODELS: dict = {}


def transcribir(path, idioma: str | None = "es", modelo: str = "small", device: str = "cpu") -> dict:
    """Devuelve {"idioma", "palabras": [{"w","start","end","score"}]}. Los modelos se reutilizan entre clips."""
    import whisperx
    audio = whisperx.load_audio(str(path))
    if len(audio) < 16000 * 0.4:
        return {"idioma": idioma, "palabras": []}
    key = (modelo, idioma, device)
    if key not in _MODELS:
        _MODELS[key] = whisperx.load_model(modelo, device, compute_type="int8", language=idioma)
    res = _MODELS[key].transcribe(audio, language=idioma)
    lang = res.get("language") or idioma or "es"
    akey = ("align", lang, device)
    if akey not in _MODELS:
        _MODELS[akey] = whisperx.load_align_model(language_code=lang, device=device)
    am, meta = _MODELS[akey]
    al = whisperx.align(res["segments"], am, meta, audio, device)
    palabras = []
    for seg in al["segments"]:
        for w in seg.get("words", []):
            if w.get("word") and w.get("start") is not None and w.get("end") is not None:
                palabras.append({"w": str(w["word"]).strip(), "start": round(float(w["start"]), 3),
                                 "end": round(float(w["end"]), 3), "score": round(float(w.get("score") or 0.0), 3)})
    return {"idioma": lang, "palabras": palabras}


def marcar_muletillas(palabras: list[dict]) -> list[bool]:
    """True en cada palabra que es muletilla. 'este', 'pues'... solo cuentan si van aisladas por una pausa."""
    flags = [False] * len(palabras)
    for i, p in enumerate(palabras):
        t = norm(p["w"]).replace(" ", "")
        if t in STRICT:
            flags[i] = True
            continue
        if t in CONTEXT:
            antes = p["start"] - palabras[i - 1]["end"] if i else 9
            despues = palabras[i + 1]["start"] - p["end"] if i + 1 < len(palabras) else 9
            if antes > 0.3 or despues > 0.3:
                flags[i] = True
        if t == "sea" and i and norm(palabras[i - 1]["w"]) == "o":
            flags[i] = flags[i - 1] = True
    return flags


def resumen_pronunciacion(palabras: list[dict]) -> dict:
    if not palabras:
        return {"n": 0, "muletillas": 0, "ratio_muletillas": 0.0, "baja_conf": 0.0, "conf_media": 0.0}
    mul = marcar_muletillas(palabras)
    sc = [p.get("score", 0.0) for p in palabras]
    return {"n": len(palabras), "muletillas": int(sum(mul)), "ratio_muletillas": sum(mul) / len(palabras),
            "baja_conf": sum(1 for s in sc if s < 0.5) / len(palabras), "conf_media": sum(sc) / len(sc)}
