"""Ficha de un clip: todo lo que el motor mide una sola vez (se guarda en caché y la usan los tres servicios)."""
import hashlib
from pathlib import Path

from . import audio, habla, imagen
from .util import probe, read_json, write_json


VERSION = 3   # 2: rostros del hablante y sacudidas; 3: rostros también de perfil


def _clave(path: Path, modelo: str, idioma: str | None) -> str:
    st = path.stat()
    return hashlib.sha1(f"{path.resolve()}|{st.st_size}|{int(st.st_mtime)}|{modelo}|{idioma}".encode()).hexdigest()[:12]


def ficha(path: Path, cache: Path, transcribir: bool = True, modelo: str = "small", idioma: str | None = "es",
          log=print) -> dict:
    path = Path(path)
    f = cache / f"{path.stem}-{_clave(path, modelo, idioma)}.json"
    hit = read_json(f)
    if hit and (hit.get("habla") is not None or not transcribir):
        v = hit.get("version", 1)
        if v < VERSION and hit["duracion"] > 0.3:   # análisis de imagen más nuevo: se rehace solo lo que cambió (la transcripción se conserva)
            if v >= 2:
                log(f"· {path.name}: actualizando la detección de rostros")
                enc = hit["criterios"]["encuadre"]
                enc["valores"]["caras"] = imagen.deteccion_caras(path, hit["duracion"])
            else:
                log(f"· {path.name}: actualizando el análisis de imagen")
                hit["criterios"].update(imagen.analizar_imagen(path, hit["duracion"], hit["alto"]))
            hit["version"] = VERSION
            write_json(f, hit)
        return hit
    log(f"· {path.name}: leyendo metadatos")
    meta = probe(path)
    dur = meta["duracion"]
    log(f"· {path.name}: imagen")
    img = imagen.analizar_imagen(path, dur, meta["alto"]) if dur > 0.3 else {}
    log(f"· {path.name}: audio")
    aud = audio.analizar_audio(path, dur, meta["tiene_audio"])
    aud.pop("_voz", None)
    data = {"archivo": str(path), "nombre": path.name, **meta, "criterios": {**img, **aud}, "habla": None, "version": VERSION}
    if transcribir and meta["tiene_audio"]:
        log(f"· {path.name}: transcribiendo")
        data["habla"] = habla.transcribir(path, idioma, modelo)
    elif transcribir:
        data["habla"] = {"idioma": idioma, "palabras": []}
    write_json(f, data)
    return data
