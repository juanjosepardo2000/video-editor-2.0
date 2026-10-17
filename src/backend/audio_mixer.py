"""Add BeatMap-driven SFX and one global music bed with FFmpeg.

Example: ``python src/backend/audio_mixer.py pipeline/rough_cut.mp4``.
"""
import argparse
import logging
import re
from pathlib import Path

import ffmpeg

SFX_DIR = Path("assets/sfx")
MUSIC_DIR = Path("assets/music")
MUSIC_DB_RANGE = (-23, -20)
VALID_SFX = {"whoosh", "pop", "click", "draw", "riser", "hit"}
LOGGER = logging.getLogger(__name__)


def parse_time(value: str) -> float:
    """Parse the BeatMap's ``mm:ss.s`` time format."""
    match = re.fullmatch(r"\s*(\d+):(\d{2}(?:\.\d+)?)\s*", value)
    if not match:
        raise ValueError(f"invalid BeatMap time: {value!r}")
    minutes, seconds = int(match.group(1)), float(match.group(2))
    if seconds >= 60:
        raise ValueError(f"seconds must be below 60 in BeatMap time: {value!r}")
    return minutes * 60 + seconds


def parse_beatmap(beatmap_path: str | Path) -> list[dict]:
    """Parse current BeatMap columns, returning only SFX events and their beat time."""
    lines = Path(beatmap_path).read_text(encoding="utf-8").splitlines()
    header = next((line for line in lines if line.strip().startswith("|") and "Inicio" in line and "SFX" in line), None)
    if header is None:
        raise ValueError("BeatMap table with Inicio and SFX columns was not found")
    columns = [cell.strip() for cell in header.strip().strip("|").split("|")]
    result, collecting = [], False
    for line in lines:
        if line == header:
            collecting = True
            continue
        if not collecting or not line.strip().startswith("|") or re.fullmatch(r"[|\- :]+", line.strip()):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != len(columns):
            continue
        row = dict(zip(columns, cells))
        for spec in row.get("SFX", "-").split(","):
            spec = spec.strip()
            if not spec or spec == "-":
                continue
            sound_type, separator, filename = spec.partition(":")
            if sound_type not in VALID_SFX:
                raise ValueError(f"unsupported SFX type {sound_type!r}; expected one of {sorted(VALID_SFX)}")
            result.append({"time": parse_time(row["Inicio"]), "type": sound_type, "file": filename.strip() if separator else None})
    return result


def _resolve_sfx(event: dict, sfx_dir: Path | None = None) -> Path:
    """Resolve a requested SFX without allowing paths outside the SFX directory."""
    sfx_dir = sfx_dir or SFX_DIR
    if event["file"]:
        candidate = sfx_dir / event["file"]
        if sfx_dir.resolve() not in candidate.resolve().parents or not candidate.is_file():
            raise FileNotFoundError(f"BeatMap requests missing SFX: {candidate}")
        return candidate
    candidates = sorted(path for path in sfx_dir.iterdir() if path.is_file() and path.stem.lower().startswith(event["type"].lower()))
    if not candidates:
        raise FileNotFoundError(f"no SFX file for type {event['type']!r} in {sfx_dir}")
    if len(candidates) > 1:
        LOGGER.warning("Multiple %s SFX candidates; using deterministic choice %s", event["type"], candidates[0])
    return candidates[0]


def _music_file(beatmap_path: Path, music_dir: Path | None = None) -> Path:
    music_dir = music_dir or MUSIC_DIR
    match = re.search(r"Música:\s*([^\s]+)", beatmap_path.read_text(encoding="utf-8"))
    requested = Path(match.group(1)) if match else None
    if requested and requested.name.upper() != "TODO.MP3":
        if requested.is_file():
            return requested
        candidate = music_dir / requested.name
        if candidate.is_file():
            return candidate
        raise FileNotFoundError(f"BeatMap music does not exist: {requested}")
    candidates = sorted(path for path in music_dir.iterdir() if path.is_file())
    if not candidates:
        raise FileNotFoundError(f"no music file found in {music_dir}")
    if len(candidates) > 1:
        LOGGER.warning("BeatMap supports one global music bed; using deterministic choice %s", candidates[0])
    return candidates[0]


def mix(video_path: str, beatmap_path: str = "pipeline/beatmap.md", output_path: str = "pipeline/mixed.mp4") -> None:
    """Mix voice, -22 dB global music, and delayed/reverbed BeatMap SFX into MP4."""
    beatmap = Path(beatmap_path)
    events = parse_beatmap(beatmap)
    video = ffmpeg.input(video_path)
    music = ffmpeg.input(str(_music_file(beatmap)), stream_loop=-1).audio.filter("volume", "-22dB")
    inputs = [video.audio, music]
    for index, event in enumerate(events):
        # ffmpeg-python fusiona nodos idénticos; el mismo SFX repetido rompería el grafo (varias salidas
        # de un mismo filtro). Un valor distinto por evento mantiene cada instancia independiente.
        sound = ffmpeg.input(str(_resolve_sfx(event)), thread_queue_size=512 + index).audio
        inputs.append(sound.filter("aecho", "0.8", "0.9", "1000", "0.7").filter("afade", t="out", st=0, d=0.08).filter("adelay", f"{round(event['time'] * 1000)}:all=1"))
    mixed = ffmpeg.filter(inputs, "amix", inputs=len(inputs), duration="first", normalize=0)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    try:
        ffmpeg.output(video.video, mixed, output_path, vcodec="copy", acodec="aac", movflags="+faststart").overwrite_output().run()
    except ffmpeg.Error as exc:
        detail = exc.stderr.decode(errors="replace") if exc.stderr else str(exc)
        raise RuntimeError(f"FFmpeg audio mix failed: {detail}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", nargs="?", default="pipeline/rough_cut.mp4")
    parser.add_argument("--beatmap", default="pipeline/beatmap.md"); parser.add_argument("--output", default="pipeline/mixed.mp4")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    mix(args.video, args.beatmap, args.output)


if __name__ == "__main__":
    main()
