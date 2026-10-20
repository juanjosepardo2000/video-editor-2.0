"""Control de calidad geométrico para overlays 9:16 de Minthy."""
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import subprocess
import struct
import tempfile
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SAFE = {"left": 60 / 1080, "top": 150 / 1920, "right": 1 - 120 / 1080, "bottom": 1 - 380 / 1920}
REPO = Path(__file__).resolve().parents[2]


def _binary(name: str) -> str:
    system = shutil.which(name)
    if system:
        return system
    suffix = ".exe" if __import__("os").name == "nt" else ""
    bundled = list((REPO / "node_modules/@remotion").glob(f"compositor-*/{name}{suffix}"))
    if bundled:
        return str(bundled[0])
    raise FileNotFoundError(f"No se encontró {name}; instala FFmpeg o ejecuta npm install para usar el binario de Remotion.")


def overlap(a: dict[str, float], b: dict[str, float]) -> bool:
    return a["x"] < b["x"] + b["w"] and a["x"] + a["w"] > b["x"] and a["y"] < b["y"] + b["h"] and a["y"] + a["h"] > b["y"]


def _hex_rgb(value: str) -> tuple[float, float, float] | None:
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", value or ""):
        return None
    return tuple(int(value[index:index + 2], 16) / 255 for index in (1, 3, 5))


def contrast_ratio(foreground: str, background: str) -> float | None:
    colors = (_hex_rgb(foreground), _hex_rgb(background))
    if None in colors:
        return None
    def luminance(rgb: tuple[float, float, float]) -> float:
        values = [channel / 12.92 if channel <= .04045 else ((channel + .055) / 1.055) ** 2.4 for channel in rgb]
        return .2126 * values[0] + .7152 * values[1] + .0722 * values[2]
    first, second = (luminance(color) for color in colors)  # type: ignore[arg-type]
    return (max(first, second) + .05) / (min(first, second) + .05)


def _faces_for_frames(face_data: dict[str, Any], start_frame: int, end_frame: int, fps: float) -> list[tuple[float, dict[str, float]]]:
    start, end = start_frame / fps, end_frame / fps
    return [(float(frame["t"]), box) for frame in face_data.get("frames", []) if start <= float(frame["t"]) <= end for box in frame.get("boxes", [])]


def _check(identifier: str, status: str, detail: str, timestamps: list[float], value: float | None, limit: float | None) -> dict[str, Any]:
    return {"id": identifier, "status": status, "detail": detail, "timestamps": sorted(set(round(item, 3) for item in timestamps)), "value": value, "limit": limit}


def audit_layout(layout: dict[str, Any], faces: dict[str, Any], max_layers: int = 1) -> list[dict[str, Any]]:
    fps = float(layout["fps"])
    overlap_times: list[float] = []
    unsafe: list[int] = []
    weak_contrast: list[int] = []
    unknown_contrast: list[int] = []
    for layer in layout.get("layers", []):
        box = layer["box"]
        if layer.get("kind") != "speaker" and not layer.get("occludesSpeaker", False):
            overlap_times.extend(t for t, face in _faces_for_frames(faces, layer["startFrame"], layer["endFrame"], fps) if overlap(box, face))
            tolerance = .001
            inside = box["x"] >= SAFE["left"] - tolerance and box["y"] >= SAFE["top"] - tolerance and box["x"] + box["w"] <= SAFE["right"] + tolerance and box["y"] + box["h"] <= SAFE["bottom"] + tolerance
            if not inside:
                unsafe.append(int(layer["beat"]))
        ratio = contrast_ratio(layer.get("textColor", ""), layer.get("backgroundColor", ""))
        if layer.get("kind") in {"caption", "graphic"}:
            if ratio is None:
                unknown_contrast.append(int(layer["beat"]))
            elif ratio < 4.5:
                weak_contrast.append(int(layer["beat"]))

    events: list[tuple[int, int]] = []
    for layer in layout.get("layers", []):
        if layer.get("kind") == "graphic":
            events.extend([(int(layer["startFrame"]), 1), (int(layer["endFrame"]), -1)])
    active = peak = 0
    for _, delta in sorted(events, key=lambda item: (item[0], item[1])):
        active += delta
        peak = max(peak, active)

    return [
        _check("face_overlap", "fail" if overlap_times else "pass", f"{len(overlap_times)} muestras de capa sobre el rostro.", overlap_times, float(len(overlap_times)), 0),
        _check("safe_zone", "fail" if unsafe else "pass", f"Beats fuera de zona segura: {sorted(set(unsafe)) or 'ninguno'}.", [], float(len(set(unsafe))), 0),
        _check("contrast", "fail" if weak_contrast else "warn" if unknown_contrast else "pass", f"Contraste bajo: {sorted(set(weak_contrast)) or 'ninguno'}; no medible: {sorted(set(unknown_contrast)) or 'ninguno'}.", [], float(len(set(weak_contrast))), 4.5),
        _check("simultaneous_layers", "fail" if peak > max_layers else "pass", f"Máximo de gráficos simultáneos: {peak}.", [], float(peak), float(max_layers)),
    ]


def _probe_size(video: Path) -> tuple[int, int]:
    result = subprocess.run([_binary("ffprobe"), "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "json", str(video)], check=True, capture_output=True, text=True)
    stream = json.loads(result.stdout)["streams"][0]
    return int(stream["width"]), int(stream["height"])


def rendered_bounds(video: Path, second: float) -> dict[str, float] | None:
    width, height = _probe_size(video)
    with tempfile.TemporaryDirectory(prefix="minthy-alpha-") as folder:
        frame = Path(folder) / "frame.png"
        subprocess.run([_binary("ffmpeg"), "-hide_banner", "-loglevel", "error", "-ss", str(max(second, 0)), "-i", str(video), "-frames:v", "1", "-pix_fmt", "rgba", "-y", str(frame)], check=True)
        if not frame.exists():
            return None
        bounds = _png_alpha_bounds(frame)
    if bounds is None:
        return None
    x1, y1, x2, y2 = bounds
    return {"x": x1 / width, "y": y1 / height, "w": (x2 - x1 + 1) / width, "h": (y2 - y1 + 1) / height}


def _png_alpha_bounds(path: Path) -> tuple[int, int, int, int] | None:
    """Lee el canal alfa de un PNG RGBA de 8 bits usando solo la stdlib."""
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("FFmpeg no produjo un PNG válido.")
    offset, compressed = 8, bytearray()
    width = height = color_type = bit_depth = 0
    while offset < len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + length]
        offset += 12 + length
        if kind == b"IHDR":
            width, height, bit_depth, color_type = struct.unpack(">IIBB", payload[:10])
        elif kind == b"IDAT":
            compressed.extend(payload)
        elif kind == b"IEND":
            break
    if bit_depth != 8 or color_type not in (4, 6):
        raise ValueError(f"PNG no soportado para QC: bit_depth={bit_depth}, color_type={color_type}.")
    channels = 4 if color_type == 6 else 2
    stride = width * channels
    raw = zlib.decompress(bytes(compressed))
    previous = bytearray(stride)
    x1, y1, x2, y2 = width, height, -1, -1
    cursor = 0
    for y in range(height):
        filter_type, cursor = raw[cursor], cursor + 1
        scan = bytearray(raw[cursor:cursor + stride])
        cursor += stride
        for index in range(stride):
            left = scan[index - channels] if index >= channels else 0
            up = previous[index]
            upper_left = previous[index - channels] if index >= channels else 0
            if filter_type == 1:
                scan[index] = (scan[index] + left) & 255
            elif filter_type == 2:
                scan[index] = (scan[index] + up) & 255
            elif filter_type == 3:
                scan[index] = (scan[index] + ((left + up) // 2)) & 255
            elif filter_type == 4:
                estimate = left + up - upper_left
                distances = (abs(estimate - left), abs(estimate - up), abs(estimate - upper_left))
                predictor = left if distances[0] <= distances[1] and distances[0] <= distances[2] else up if distances[1] <= distances[2] else upper_left
                scan[index] = (scan[index] + predictor) & 255
            elif filter_type != 0:
                raise ValueError(f"Filtro PNG desconocido: {filter_type}.")
        for x in range(width):
            if scan[x * channels + channels - 1] > 0:
                x1, y1, x2, y2 = min(x1, x), min(y1, y), max(x2, x), max(y2, y)
        previous = scan
    return None if x2 < 0 else (x1, y1, x2, y2)


def audit_render(layout: dict[str, Any], overlay: Path | None, tolerance: float = .02) -> dict[str, Any]:
    if overlay is None:
        return _check("layout_vs_render", "warn", "No se proporcionó --overlay; comparación alfa pendiente.", [], None, tolerance)
    mismatches: list[float] = []
    beats = sorted({int(layer["beat"]) for layer in layout.get("layers", [])})
    for beat in beats:
        layers = [layer for layer in layout["layers"] if int(layer["beat"]) == beat and layer.get("kind") != "speaker"]
        if not layers:
            continue
        second = ((layers[0]["startFrame"] + layers[0]["endFrame"]) / 2) / float(layout["fps"])
        actual = rendered_bounds(overlay, second)
        if actual is None:
            mismatches.append(second)
            continue
        expected = {"x": min(layer["box"]["x"] for layer in layers), "y": min(layer["box"]["y"] for layer in layers)}
        expected["w"] = max(layer["box"]["x"] + layer["box"]["w"] for layer in layers) - expected["x"]
        expected["h"] = max(layer["box"]["y"] + layer["box"]["h"] for layer in layers) - expected["y"]
        delta = max(abs(actual[key] - expected[key]) for key in ("x", "y", "w", "h"))
        if delta > tolerance:
            mismatches.append(second)
    return _check("layout_vs_render", "warn" if mismatches else "pass", f"Diferencia > {tolerance:.0%} en {len(mismatches)} muestra(s).", mismatches, float(len(mismatches)), tolerance)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layout", type=Path, default=Path("pipeline/layout.json"))
    parser.add_argument("--faces", type=Path, default=Path("pipeline/face_boxes.json"))
    parser.add_argument("--overlay", type=Path)
    parser.add_argument("--output", type=Path, default=Path("pipeline/qc_geometry.json"))
    parser.add_argument("--max-layers", type=int, default=1)
    args = parser.parse_args()
    layout = json.loads(args.layout.read_text(encoding="utf-8"))
    faces = json.loads(args.faces.read_text(encoding="utf-8"))
    checks = audit_layout(layout, faces, args.max_layers)
    checks.append(audit_render(layout, args.overlay))
    summary = {status: sum(check["status"] == status for check in checks) for status in ("pass", "warn", "fail")}
    report = {"generated": datetime.now(timezone.utc).isoformat(), "video": str(args.overlay or ""), "checks": checks, "summary": summary}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"QC geometría: {summary['pass']} pass, {summary['warn']} warn, {summary['fail']} fail -> {args.output}")
    return 1 if summary["fail"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
