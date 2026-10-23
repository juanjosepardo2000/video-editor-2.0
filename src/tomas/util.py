"""Utilidades comunes: ffprobe/ffmpeg, texto normalizado, JSON y rutas de trabajo."""
import json
import re
import subprocess
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "tomas_data"
CONFIG = json.loads((Path(__file__).parent / "config/criterios.json").read_text(encoding="utf-8"))
VIDEO_EXT = {".mp4", ".mov", ".avi", ".mkv", ".m4v", ".mts"}
STOPWORDS = set("""a al algo como con cual cuando de del desde donde e el ella ellos en entre era es esa ese eso esta este esto
fue ha han hay la las le les lo los me mi mas mis muy ni no nos o os otra otro para pero por que se si sin sobre su sus te
ti tu tus un una uno unos unas y ya yo""".split())


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, **kw)


def probe(path: Path) -> dict:
    """Metadatos básicos de un clip (duración, tamaño real tras rotación, audio, fecha de creación)."""
    out = run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(path)])
    info = json.loads(out.stdout or "{}")
    streams = info.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"), {})
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)
    w, h = int(v.get("width", 0)), int(v.get("height", 0))
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(sd["rotation"])
    rot = int(v.get("tags", {}).get("rotate", rot) or rot)
    if abs(rot) in (90, 270):
        w, h = h, w
    fmt = info.get("format", {})
    fps_txt = v.get("avg_frame_rate", "0/1")
    try:
        n, d = fps_txt.split("/")
        fps = float(n) / float(d) if float(d) else 0.0
    except ValueError:
        fps = 0.0
    tags = {**fmt.get("tags", {}), **v.get("tags", {})}
    return {"duracion": float(fmt.get("duration") or v.get("duration") or 0), "ancho": w, "alto": h, "fps": round(fps, 2),
            "tiene_audio": a is not None, "creado": tags.get("creation_time"),
            "camara": tags.get("com.apple.quicktime.model") or tags.get("model") or tags.get("encoder"),
            "codec": v.get("codec_name")}


def norm(text: str) -> str:
    """Minúsculas, sin tildes ni signos: para comparar texto."""
    t = unicodedata.normalize("NFD", text.lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9ñ\s]", " ", t.replace("ñ", "n")).strip()


def tokens(text: str) -> list[str]:
    return norm(text).split()


def content_tokens(text: str) -> list[str]:
    return [t for t in tokens(text) if t not in STOPWORDS and len(t) > 1]


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)


def read_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def list_clips(folder: Path) -> list[Path]:
    return sorted(p for p in folder.rglob("*") if p.suffix.lower() in VIDEO_EXT and not p.name.startswith("."))


def fmt_t(seconds: float) -> str:
    m, s = divmod(max(seconds, 0), 60)
    return f"{int(m):02d}:{s:05.2f}"
