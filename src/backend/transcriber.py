"""Transcribe un video con WhisperX y genera pipeline/transcript.json con timestamps por palabra."""
import json
import sys
from pathlib import Path

OUTPUT_PATH = Path("pipeline/transcript.json")


def transcribe(video_path: str, output_path: Path = OUTPUT_PATH, language: str = "es") -> dict:
    """Devuelve y guarda el transcript.

    Estructura de salida:
    {"video": str, "language": str,
     "words": [{"word": str, "start": float, "end": float}]}
    """
    # TODO: cargar modelo whisperx, transcribir y alinear a nivel de palabra.
    transcript = {"video": video_path, "language": language, "words": []}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(transcript, ensure_ascii=False, indent=2), encoding="utf-8")
    return transcript


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Uso: python transcriber.py <video>")
    transcribe(sys.argv[1])
