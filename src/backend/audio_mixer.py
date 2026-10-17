"""Add BeatMap-driven SFX and one global music bed with FFmpeg.

Example: ``python src/backend/audio_mixer.py pipeline/rough_cut.mp4``.
"""
import argparse
import logging
import re
import subprocess
from pathlib import Path

import ffmpeg

SFX_DIR = Path("assets/sfx")
MUSIC_DIR = Path("assets/music")
MUSIC_DB_RANGE = (-23, -20)
AUDIO_SUFFIXES = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
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
    candidates = sorted(path for path in sfx_dir.iterdir() if path.is_file() and path.suffix.lower() in AUDIO_SUFFIXES and path.stem.lower().startswith(event["type"].lower()))
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
    candidates = sorted(path for path in music_dir.iterdir() if path.is_file() and not path.name.startswith(".") and path.suffix.lower() in AUDIO_SUFFIXES)
    if not candidates:
        raise FileNotFoundError(f"no music file found in {music_dir}")
    if len(candidates) > 1:
        LOGGER.warning("BeatMap supports one global music bed; using deterministic choice %s", candidates[0])
    return candidates[0]


def sfx_duration(path: Path) -> float:
    """Duration in seconds of an SFX file (needed to place the fade-out at its end)."""
    return float(ffmpeg.probe(str(path))["format"]["duration"])


def sfx_fade_out(duration: float, fade_seconds: float = 0.08) -> tuple[float, float]:
    """Return (start, length) of a short fade-out at the *end* of an SFX."""
    length = min(fade_seconds, duration)
    return max(0.0, duration - length), length


def mean_volume(path: str | Path, seconds: float | None = None) -> float | None:
    """Mean volume (dB) of the first audio stream via FFmpeg volumedetect; None if unavailable."""
    command = ["ffmpeg", "-hide_banner", "-nostdin"]
    if seconds:
        command += ["-t", str(seconds)]
    command += ["-i", str(path), "-vn", "-af", "volumedetect", "-f", "null", "-"]
    output = subprocess.run(command, capture_output=True, text=True).stderr
    match = re.search(r"mean_volume:\s*(-?\d+(?:\.\d+)?) dB", output)
    return float(match.group(1)) if match else None


def gain_to_target(current: float | None, target: float, low: float = -40.0, high: float = 25.0) -> float:
    """dB of gain that moves ``current`` to ``target``, clamped; 0 when the level is unknown."""
    return 0.0 if current is None else max(low, min(high, target - current))


MUSIC_GAIN_DB = -22.0         # claude.md: música a -20/-23 dB (referencia -22)
MUSIC_MIN_HEADROOM_DB = 8.0   # la música nunca debe quedar a menos de 8 dB de la voz
SFX_BELOW_VOICE_DB = 4.0      # perceptibles sin tapar la voz
MIN_VOICE_DB = -60.0          # por debajo se considera que no hay voz de referencia


def mix(video_path: str, beatmap_path: str = "pipeline/beatmap.md", output_path: str = "pipeline/mixed.mp4") -> None:
    """Mix voice, -22 dB global music, and delayed/reverbed BeatMap SFX into MP4."""
    beatmap = Path(beatmap_path)
    events = parse_beatmap(beatmap)
    video = ffmpeg.input(video_path)
    music_path = _music_file(beatmap)
    voice_db = mean_volume(video_path)
    has_voice = voice_db is not None and voice_db > MIN_VOICE_DB
    music_gain = min(MUSIC_GAIN_DB, gain_to_target(mean_volume(music_path, 30), voice_db - MUSIC_MIN_HEADROOM_DB)) if has_voice else MUSIC_GAIN_DB
    music = ffmpeg.input(str(music_path), stream_loop=-1).audio.filter("volume", f"{music_gain:.1f}dB")
    inputs = [video.audio, music]
    for index, event in enumerate(events):
        # ffmpeg-python fusiona nodos idénticos; el mismo SFX repetido rompería el grafo (varias salidas
        # de un mismo filtro). Un valor distinto por evento mantiene cada instancia independiente.
        sfx_path = _resolve_sfx(event)
        fade_start, fade_duration = sfx_fade_out(sfx_duration(sfx_path))
        sound = ffmpeg.input(str(sfx_path), thread_queue_size=512 + index).audio
        if has_voice:
            sound = sound.filter("volume", f"{gain_to_target(mean_volume(sfx_path), voice_db - SFX_BELOW_VOICE_DB, -30.0, 10.0):.1f}dB")
        inputs.append(sound.filter("aecho", "0.8", "0.9", "1000", "0.7").filter("afade", t="out", st=fade_start, d=fade_duration).filter("adelay", f"{round(event['time'] * 1000)}:all=1"))
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
