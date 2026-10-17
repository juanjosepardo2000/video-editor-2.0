"""Validador técnico de renders de Gonzalo (PNG, MOV/MP4/WebM y audio)."""

from __future__ import annotations

import argparse
import json
import shutil
import struct
import subprocess
import sys
import re
from pathlib import Path
from typing import Any


ALPHA_PIXEL_FORMATS = ("yuva", "rgba", "argb", "bgra", "abgr", "gbrap")


def _ffprobe() -> str:
    system = shutil.which("ffprobe")
    if system:
        return system
    root = Path(__file__).resolve().parents[3]
    candidates = sorted((root / "node_modules" / "@remotion").glob("compositor-*/ffprobe*"))
    if not candidates:
        raise FileNotFoundError("No se encontró ffprobe en PATH ni en las dependencias de Remotion")
    return str(candidates[0])


def _fraction(value: str) -> float:
    numerator, denominator = value.split("/", 1)
    return float(numerator) / float(denominator)


def _png_info(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()[:33]
    if len(raw) < 33 or raw[:8] != b"\x89PNG\r\n\x1a\n" or raw[12:16] != b"IHDR":
        raise ValueError("El archivo no es un PNG válido")
    width, height, bit_depth, color_type = struct.unpack(">IIBB", raw[16:26])
    return {"format": "png", "width": width, "height": height, "bit_depth": bit_depth,
            "pixel_format": f"png-color-type-{color_type}", "has_alpha": color_type in (4, 6)}


def _media_info(path: Path) -> dict[str, Any]:
    command = [_ffprobe(), "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise ValueError(f"ffprobe no pudo leer el archivo: {result.stderr.strip()}")
    data = json.loads(result.stdout)
    streams = data.get("streams", [])
    video = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
    audio = next((stream for stream in streams if stream.get("codec_type") == "audio"), None)
    selected = video or audio or {}
    pixel_format = selected.get("pix_fmt", "")
    result_info = {
        "format": data.get("format", {}).get("format_name", "unknown"),
        "duration": float(data.get("format", {}).get("duration", 0)),
        "codec": selected.get("codec_name"),
        "profile": selected.get("profile"),
        "width": selected.get("width"),
        "height": selected.get("height"),
        "pixel_format": pixel_format,
        "has_alpha": pixel_format.startswith(ALPHA_PIXEL_FORMATS),
    }
    if video and video.get("r_frame_rate"):
        result_info["fps"] = _fraction(video["r_frame_rate"])
    if audio:
        result_info["sample_rate"] = int(audio.get("sample_rate", 0))
        result_info["channels"] = audio.get("channels")
    return result_info


def _beatmap_duration(path: Path) -> float:
    if not path.is_file():
        raise FileNotFoundError(f"No existe el BeatMap: {path}")
    ends: list[float] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\|\s*\d+\s*\|\s*\d{2,}:\d{2}\.\d+\s*\|\s*(\d{2,}):(\d{2})\.(\d+)\s*\|", line)
        if match:
            minutes, seconds, fraction = match.groups()
            ends.append(int(minutes) * 60 + int(seconds) + float(f"0.{fraction}"))
    if not ends:
        raise ValueError("El BeatMap no contiene filas de beats válidas")
    return max(ends)


def validate(path: Path, *, width: int | None, height: int | None, fps: float | None,
             duration: float | None, alpha: bool, codec: str | None) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(f"No existe el render: {path}")
    info = _png_info(path) if path.suffix.lower() == ".png" else _media_info(path)
    errors: list[str] = []
    if width is not None and info.get("width") != width:
        errors.append(f"ancho {info.get('width')} != {width}")
    if height is not None and info.get("height") != height:
        errors.append(f"alto {info.get('height')} != {height}")
    if fps is not None and abs(float(info.get("fps", 0)) - fps) > 0.01:
        errors.append(f"fps {info.get('fps')} != {fps}")
    if duration is not None and abs(float(info.get("duration", 0)) - duration) > 0.05:
        errors.append(f"duración {info.get('duration')} != {duration}")
    if alpha and not info.get("has_alpha"):
        errors.append(f"el formato de píxel {info.get('pixel_format')} no contiene alfa")
    if codec is not None and info.get("codec") != codec:
        errors.append(f"codec {info.get('codec')} != {codec}")
    return {"valid": not errors, "file": str(path.resolve()), "errors": errors, **info}


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida resolución, FPS, duración, codec y alfa")
    parser.add_argument("file", type=Path)
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--fps", type=float)
    parser.add_argument("--duration", type=float)
    parser.add_argument("--beatmap", type=Path, help="Usa el final del último beat como duración esperada")
    parser.add_argument("--alpha", action="store_true")
    parser.add_argument("--codec")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        if args.duration is not None and args.beatmap is not None:
            raise ValueError("Usa --duration o --beatmap, no ambos")
        expected_duration = _beatmap_duration(args.beatmap) if args.beatmap else args.duration
        report = validate(args.file, width=args.width, height=args.height, fps=args.fps,
                          duration=expected_duration, alpha=args.alpha, codec=args.codec)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR QC: {error}", file=sys.stderr)
        return 1
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
