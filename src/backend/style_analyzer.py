"""Mide un video de referencia para extraer reglas de estilo (ritmo, silencios, audio, habla) con FFmpeg.

Primera versión (Juan/Claude); Carlos la revisa y la mejora. Los videos no se guardan: solo métricas.

Ejemplo:
    python3 src/backend/style_analyzer.py ref.mp4 --kind narrativo --out profiles/perfil-1/metrics/narrativo/n1.json \
        --frames-dir /tmp/frames --transcribe --language es
"""
import argparse
import json
import math
import re
import statistics
import subprocess
import sys
from pathlib import Path


def _run(command: list[str]) -> str:
    result = subprocess.run(command, capture_output=True, text=True)
    return result.stderr + result.stdout


def probe(path: Path) -> dict:
    info = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(path)]))
    video = next(s for s in info["streams"] if s["codec_type"] == "video")
    num, den = (int(x) for x in video["r_frame_rate"].split("/"))
    return {"duration_s": round(float(info["format"]["duration"]), 2), "width": video["width"], "height": video["height"],
            "fps": round(num / den, 2), "has_audio": any(s["codec_type"] == "audio" for s in info["streams"])}


def scene_cuts(path: Path, duration: float, threshold: float = 0.3) -> dict:
    """Cortes de plano por cambio de escena; devuelve estadísticas de duración de plano."""
    out = _run(["ffmpeg", "-hide_banner", "-nostdin", "-i", str(path), "-vf", f"select='gt(scene,{threshold})',showinfo", "-an", "-f", "null", "-"])
    times = [float(t) for t in re.findall(r"pts_time:([0-9.]+)", out)]
    bounds = [0.0, *times, duration]
    shots = [b - a for a, b in zip(bounds, bounds[1:]) if b - a > 0.05]
    return {"threshold": threshold, "count": len(times), "per_minute": round(len(times) / duration * 60, 1),
            "mean_shot_s": round(statistics.mean(shots), 2), "median_shot_s": round(statistics.median(shots), 2),
            "min_shot_s": round(min(shots), 2), "max_shot_s": round(max(shots), 2), "times_s": [round(t, 2) for t in times]}


def silence(path: Path, duration: float, noise_db: int = -35, min_s: float = 0.3) -> dict:
    out = _run(["ffmpeg", "-hide_banner", "-nostdin", "-i", str(path), "-vn", "-af", f"silencedetect=noise={noise_db}dB:d={min_s}", "-f", "null", "-"])
    lengths = [float(x) for x in re.findall(r"silence_duration:\s*([0-9.]+)", out)]
    return {"noise_db": noise_db, "min_s": min_s, "count": len(lengths), "total_s": round(sum(lengths), 2),
            "percent_of_video": round(sum(lengths) / duration * 100, 1), "longest_s": round(max(lengths), 2) if lengths else 0.0}


def loudness(path: Path) -> dict:
    out = _run(["ffmpeg", "-hide_banner", "-nostdin", "-i", str(path), "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"])
    summary = out[out.rfind("Summary:"):] if "Summary:" in out else ""
    grab = lambda pattern: (lambda m: float(m.group(1)) if m else None)(re.search(pattern, summary))
    vol = _run(["ffmpeg", "-hide_banner", "-nostdin", "-i", str(path), "-vn", "-af", "volumedetect", "-f", "null", "-"])
    mean = re.search(r"mean_volume:\s*(-?[0-9.]+) dB", vol)
    return {"integrated_lufs": grab(r"I:\s+(-?[0-9.]+) LUFS"), "range_lu": grab(r"LRA:\s+([0-9.]+) LU"),
            "true_peak_dbfs": grab(r"Peak:\s+(-?[0-9.]+) dBFS"), "mean_volume_db": float(mean.group(1)) if mean else None}


def contact_sheet(path: Path, duration: float, output: Path, max_frames: int = 32, columns: int = 8) -> float:
    """Hoja de contactos con a lo sumo max_frames fotogramas uniformes; devuelve el intervalo en segundos."""
    step = max(1.0, math.ceil(duration / max_frames))
    rows = math.ceil(min(max_frames, math.ceil(duration / step)) / columns)
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(path), "-vf", f"fps=1/{step},scale=216:-1,tile={columns}x{rows}",
                    "-frames:v", "1", str(output)], check=True)
    return step


def speech(path: Path, language: str | None, model: str = "small") -> dict:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from src.backend.transcriber import transcribe
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        data = transcribe(str(path), Path(tmp) / "t.json", language=language, model_name=model)
    words = data["words"]
    if not words:
        return {"language": data["language"], "words": 0}
    span = words[-1]["end"] - words[0]["start"]
    gaps = [b["start"] - a["end"] for a, b in zip(words, words[1:])]
    return {"language": data["language"], "words": len(words), "first_word_s": round(words[0]["start"], 2),
            "speaking_span_s": round(span, 2), "words_per_minute": round(len(words) / span * 60) if span > 0 else None,
            "pauses_over_0_3s": sum(1 for g in gaps if g > 0.3), "longest_pause_s": round(max(gaps), 2) if gaps else 0.0,
            "hook_text": " ".join(w["word"] for w in words[:14])}


def analyze(path: Path, kind: str, frames_dir: Path | None, transcribe_speech: bool, language: str | None) -> dict:
    meta = probe(path)
    result = {"kind": kind, **meta, "cuts": scene_cuts(path, meta["duration_s"]), "silence": silence(path, meta["duration_s"])}
    if meta["has_audio"]:
        result["loudness"] = loudness(path)
    if frames_dir:
        sheet = frames_dir / f"{path.stem}.png"
        result["contact_sheet"] = {"seconds_per_frame": contact_sheet(path, meta["duration_s"], sheet), "path": str(sheet)}
    if transcribe_speech and meta["has_audio"]:
        result["speech"] = speech(path, language)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("video", type=Path)
    parser.add_argument("--kind", choices=("narrativo", "visual"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--frames-dir", type=Path)
    parser.add_argument("--transcribe", action="store_true")
    parser.add_argument("--language", default=None, help="código de idioma; omitir para detección automática")
    args = parser.parse_args()
    data = analyze(args.video, args.kind, args.frames_dir, args.transcribe, args.language)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{args.video.name}: {data['duration_s']} s, {data['cuts']['count']} cortes, {data['silence']['count']} silencios -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
