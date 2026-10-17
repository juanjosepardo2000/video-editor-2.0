"""Create a word-timed transcript locally with WhisperX.

Example: ``python src/backend/transcriber.py assets/raw/video.mp4 --language es``.
"""
import argparse
import json
from pathlib import Path
from typing import Literal

OUTPUT_PATH = Path("pipeline/transcript.json")
Device = Literal["auto", "cpu", "cuda"]


def available_device(requested: Device = "auto") -> str:
    """Return the usable device, degrading an unavailable CUDA request to CPU."""
    if requested not in {"auto", "cpu", "cuda"}:
        raise ValueError("device must be 'auto', 'cpu', or 'cuda'")
    if requested == "cpu":
        return "cpu"
    try:
        import torch
        has_cuda = torch.cuda.is_available()
    except ImportError:
        has_cuda = False
    if has_cuda:
        return "cuda"
    if requested == "cuda":
        print("CUDA was requested but no compatible GPU is available; using CPU.")
    return "cpu"


def transcribe(video_path: str, output_path: Path = OUTPUT_PATH, language: str | None = "es",
               device: Device = "auto", model_name: str = "small") -> dict:
    """Transcribe and align a video, saving the stable project transcript contract.

    Spanish is the default. Pass ``language=None`` for WhisperX language detection.
    WhisperX is imported lazily so parser-only workflows do not need a GPU setup.
    """
    try:
        import whisperx
    except ImportError as exc:
        raise RuntimeError("WhisperX is required: pip install -r requirements.txt") from exc
    selected_device = available_device(device)
    audio = whisperx.load_audio(video_path)
    model = whisperx.load_model(model_name, selected_device,
                                compute_type="float16" if selected_device == "cuda" else "int8",
                                language=language)
    result = model.transcribe(audio, language=language)
    detected_language = result.get("language") or language
    if not detected_language:
        raise RuntimeError("WhisperX did not return a detected language")
    align_model, metadata = whisperx.load_align_model(language_code=detected_language, device=selected_device)
    aligned = whisperx.align(result["segments"], align_model, metadata, audio, selected_device)
    words = [
        {"word": str(word["word"]).strip(), "start": float(word["start"]), "end": float(word["end"])}
        for segment in aligned["segments"] for word in segment.get("words", [])
        if word.get("word") and word.get("start") is not None and word.get("end") is not None
    ]
    transcript = {"video": str(video_path), "language": detected_language, "words": words}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(transcript, ensure_ascii=False, indent=2), encoding="utf-8")
    return transcript


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video")
    parser.add_argument("--language", default="es", help="language code; use auto for detection")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--model", default="small")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    transcribe(args.video, args.output, None if args.language == "auto" else args.language, args.device, args.model)


if __name__ == "__main__":
    main()
