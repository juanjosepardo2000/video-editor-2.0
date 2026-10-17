"""Lee pipeline/transcript.json y ejecuta cortes con FFmpeg."""
import json
import sys
from pathlib import Path

TRANSCRIPT_PATH = Path("pipeline/transcript.json")
PAD_MIN_MS = 20
PAD_MAX_MS = 150


def load_segments(transcript_path: Path = TRANSCRIPT_PATH, pad_ms: int = 80) -> list[tuple[float, float]]:
    """Agrupa palabras en segmentos a conservar, aplicando padding (20-150 ms)."""
    pad_ms = max(PAD_MIN_MS, min(PAD_MAX_MS, pad_ms))
    data = json.loads(transcript_path.read_text(encoding="utf-8"))
    # TODO: fusionar palabras contiguas y descartar silencios/muletillas.
    return [(max(0.0, w["start"] - pad_ms / 1000), w["end"] + pad_ms / 1000) for w in data["words"]]


def cut(video_path: str, segments: list[tuple[float, float]], output_path: str = "pipeline/rough_cut.mp4") -> None:
    # TODO: usar ffmpeg-python para recortar y concatenar los segmentos.
    raise NotImplementedError


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Uso: python rough_cutter.py <video>")
    cut(sys.argv[1], load_segments())
