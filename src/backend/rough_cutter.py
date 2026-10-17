"""Remove long silences and make an accurate FFmpeg rough cut.

Example: ``python src/backend/rough_cutter.py assets/raw/video.mp4 --padding-ms 20``.
"""
import argparse
import json
import re
from pathlib import Path

import ffmpeg

TRANSCRIPT_PATH = Path("pipeline/transcript.json")
PAD_MIN_MS, PAD_MAX_MS, SILENCE_SECONDS = 20, 150, 0.5
_UNAMBIGUOUS_FILLERS = {"um", "uh", "umm", "uhh", "mmm", "mm", "ehh"}
MIN_REPEATED_PHRASE_WORDS = 3
MAX_WORD_SECONDS = 1.5  # el alineador puede estirar una palabra sobre un silencio largo


def _normalise(word: str) -> str:
    return re.sub(r"[^\w]+", "", word.lower(), flags=re.UNICODE)


def _repeated_phrase_indices(words: list[dict]) -> set[int]:
    """Find adjacent, exact retakes of at least three words; retain the last take.

    This deliberately avoids semantic guesses: a phrase such as ``"este"`` is not
    removed merely because it could be a filler.  The review/manual modes retain all
    words so an editor can override this conservative heuristic.
    """
    normalized = [_normalise(str(word.get("word", ""))) for word in words]
    discarded: set[int] = set()
    for start in range(len(words)):
        max_length = min(12, (len(words) - start) // 2)
        for length in range(max_length, MIN_REPEATED_PHRASE_WORDS - 1, -1):
            first, second = normalized[start:start + length], normalized[start + length:start + 2 * length]
            if first == second and all(first):
                gap = float(words[start + length]["start"]) - float(words[start + length - 1]["end"])
                if gap <= SILENCE_SECONDS:
                    discarded.update(range(start, start + length))
                    break
    return discarded


def retained_words(words: list[dict], mode: str = "auto") -> list[dict]:
    """Remove unambiguous fillers and direct repeated takes in automatic mode."""
    if mode not in {"auto", "review", "manual"}:
        raise ValueError("mode must be auto, review, or manual")
    if mode != "auto":
        return list(words)
    no_fillers = [word for word in words if _normalise(str(word.get("word", ""))) not in _UNAMBIGUOUS_FILLERS]
    repeated = _repeated_phrase_indices(no_fillers)
    result: list[dict] = []
    for index, word in enumerate(no_fillers):
        if index in repeated:
            continue
        normalized = _normalise(str(word.get("word", "")))
        if normalized in _UNAMBIGUOUS_FILLERS:
            continue
        if result and normalized and normalized == _normalise(str(result[-1].get("word", ""))):
            result[-1] = word  # preserve the latest take
        else:
            result.append(word)
    return result


def build_cut_plan(words: list[dict], pad_ms: int = 20, mode: str = "auto") -> tuple[list[tuple[float, float]], list[dict]]:
    """Return padded ranges and retained words; gaps over 0.5 seconds are removed."""
    if not PAD_MIN_MS <= pad_ms <= PAD_MAX_MS:
        raise ValueError(f"padding must be between {PAD_MIN_MS} and {PAD_MAX_MS} ms")
    ordered = [dict(item, end=min(float(item["end"]), float(item["start"]) + MAX_WORD_SECONDS))
               for item in sorted(words, key=lambda item: float(item["start"]))]
    kept = retained_words(ordered, mode)
    if not kept:
        return [], []
    retained_ids, pad, segments = {id(word) for word in kept}, pad_ms / 1000, []
    start = end = None
    for word in ordered:
        # A removed filler/repeated take always creates a cut, even inside an
        # otherwise continuous spoken phrase.
        if id(word) not in retained_ids:
            if start is not None:
                segments.append((start, end))
                start = end = None
            continue
        word_start, word_end = float(word["start"]), float(word["end"])
        if start is None:
            start, end = max(0.0, word_start - pad), word_end + pad
        elif word_start - (end - pad) > SILENCE_SECONDS:
            segments.append((start, end))
            start = max(0.0, word_start - pad)
        end = max(end, word_end + pad)
    if start is not None:
        segments.append((start, end))
    return segments, kept


def load_segments(transcript_path: Path = TRANSCRIPT_PATH, pad_ms: int = 20, mode: str = "auto") -> list[tuple[float, float]]:
    """Load source transcript and calculate ranges retained by the rough cut."""
    return build_cut_plan(json.loads(transcript_path.read_text(encoding="utf-8")).get("words", []), pad_ms, mode)[0]


def remap_words(words: list[dict], segments: list[tuple[float, float]]) -> list[dict]:
    """Map source word times to the concatenated rough-cut timeline."""
    mapped, offset = [], 0.0
    for start, end in segments:
        for word in words:
            word_start, word_end = float(word["start"]), float(word["end"])
            if word_start >= start and word_end <= end:
                mapped.append({"word": word["word"], "start": round(offset + word_start - start, 6), "end": round(offset + word_end - start, 6)})
        offset += end - start
    return mapped


def cut(video_path: str, segments: list[tuple[float, float]], output_path: str = "pipeline/rough_cut.mp4") -> None:
    """Precisely recut video/audio (re-encoding deliberately preserves synchrony)."""
    if not segments:
        raise ValueError("no segments to cut")
    source, streams = ffmpeg.input(video_path), []
    for start, end in segments:
        streams += [source.video.trim(start=start, end=end).setpts("PTS-STARTPTS"),
                    source.audio.filter("atrim", start=start, end=end).filter("asetpts", "PTS-STARTPTS")]
    # ``ffmpeg-python`` represents a multi-output concat filter as a node;
    # address its video/audio pads explicitly instead of unpacking the node.
    concat = ffmpeg.concat(*streams, v=1, a=1).node
    video, audio = concat[0], concat[1]
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    try:
        ffmpeg.output(video, audio, output_path, vcodec="libx264", acodec="aac", movflags="+faststart").overwrite_output().run()
    except ffmpeg.Error as exc:
        detail = exc.stderr.decode(errors="replace") if exc.stderr else str(exc)
        raise RuntimeError(f"FFmpeg rough cut failed: {detail}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video"); parser.add_argument("--transcript", type=Path, default=TRANSCRIPT_PATH)
    parser.add_argument("--output", default="pipeline/rough_cut.mp4"); parser.add_argument("--padding-ms", type=int, default=20)
    parser.add_argument("--mode", choices=("auto", "review", "manual"), default="auto")
    args = parser.parse_args()
    transcript = json.loads(args.transcript.read_text(encoding="utf-8"))
    is_source = args.transcript.name.endswith(".source.json")
    output_transcript = args.transcript.with_name(args.transcript.name.replace(".source.json", ".json")) if is_source else args.transcript
    if transcript.get("video") == args.output:
        raise SystemExit(f"{args.transcript} ya fue remapeado al rough cut; usa {args.transcript.with_suffix('.source.json')} como --transcript")
    if not is_source:
        source_copy = args.transcript.with_suffix(".source.json")
        if not source_copy.exists():
            source_copy.write_text(json.dumps(transcript, ensure_ascii=False, indent=2), encoding="utf-8")
    segments, words = build_cut_plan(transcript.get("words", []), args.padding_ms, args.mode)
    cut(args.video, segments, args.output)
    transcript.update(video=args.output, words=remap_words(words, segments))
    output_transcript.write_text(json.dumps(transcript, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
