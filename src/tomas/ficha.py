"""Ficha de un clip: todo lo que el motor mide una sola vez (se guarda en caché y la usan los tres servicios)."""
import hashlib
from pathlib import Path

from . import audio, habla, imagen
from .util import probe, read_json, write_json


def _clave(path: Path, modelo: str, idioma: str | None) -> str:
    st = path.stat()
    return hashlib.sha1(f"{path.resolve()}|{st.st_size}|{int(st.st_mtime)}|{modelo}|{idioma}".encode()).hexdigest()[:12]


def ficha(path: Path, cache: Path, transcribir: bool = True, modelo: str = "small", idioma: str | None = "es",
          log=print) -> dict:
    path = Path(path)
    f = cache / f"{path.stem}-{_clave(path, modelo, idioma)}.json"
    hit = read_json(f)
    if hit and (hit.get("habla") is not None or not transcribir):
        return hit
    log(f"· {path.name}: leyendo metadatos")
    meta = probe(path)
    dur = meta["duracion"]
    log(f"· {path.name}: imagen")
    img = imagen.analizar_imagen(path, dur, meta["alto"]) if dur > 0.3 else {}
    log(f"· {path.name}: audio")
    aud = audio.analizar_audio(path, dur, meta["tiene_audio"])
    aud.pop("_voz", None)
    data = {"archivo": str(path), "nombre": path.name, **meta, "criterios": {**img, **aud}, "habla": None}
    if transcribir and meta["tiene_audio"]:
        log(f"· {path.name}: transcribiendo")
        data["habla"] = habla.transcribir(path, idioma, modelo)
    elif transcribir:
        data["habla"] = {"idioma": idioma, "palabras": []}
    write_json(f, data)
    return data
