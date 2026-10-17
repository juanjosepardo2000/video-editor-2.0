"""Compone video del hablante + overlay alfa en un MP4 liviano de revisión."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _compose_with_remotion(
    video: Path, overlay: Path, output: Path, width: int, height: int,
) -> None:
    if (width, height) != (540, 960):
        raise RuntimeError(
            "Sin un FFmpeg completo, la composición Remotion admite únicamente 540x960",
        )
    root = Path(__file__).resolve().parents[3]
    cli = root / "node_modules" / "@remotion" / "cli" / "remotion-cli.js"
    if not cli.is_file():
        raise RuntimeError("No se encontró el CLI de Remotion para la composición alternativa")
    with tempfile.TemporaryDirectory(prefix="minthy-preview-") as temporary:
        public_dir = Path(temporary)
        shutil.copy2(video, public_dir / "speaker.mp4")
        shutil.copy2(overlay, public_dir / "overlay.mov")
        command = [
            shutil.which("node") or "node", str(cli), "render", "src/graphics/index.ts",
            "CompositeReview", str(output), "--codec=h264", "--crf=23",
            f"--public-dir={public_dir}",
        ]
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"Remotion no pudo componer la vista previa:\n{result.stderr}\n{result.stdout}")


def compose_preview(video: Path, overlay: Path, output: Path, width: int, height: int) -> None:
    if not video.is_file():
        raise FileNotFoundError(f"No existe el video del hablante: {video}")
    if not overlay.is_file():
        raise FileNotFoundError(f"No existe el overlay: {overlay}")
    output.parent.mkdir(parents=True, exist_ok=True)
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        _compose_with_remotion(video, overlay, output, width, height)
        return
    filter_graph = (
        f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height}[speaker];"
        f"[1:v]scale={width}:{height}[graphics];"
        "[speaker][graphics]overlay=x=0:y=0:format=auto:shortest=1,format=yuv420p[review]"
    )
    command = [
        ffmpeg, "-y", "-i", str(video), "-i", str(overlay),
        "-filter_complex", filter_graph,
        "-map", "[review]", "-map", "0:a?", "-c:v", "libx264",
        "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart", "-shortest", str(output),
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg no pudo componer la vista previa:\n{result.stderr}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Combina el rough cut y el overlay Remotion para QC visual",
    )
    parser.add_argument("--video", type=Path, required=True)
    parser.add_argument("--overlay", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("out/qc/composite-preview.mp4"))
    parser.add_argument("--width", type=int, default=540)
    parser.add_argument("--height", type=int, default=960)
    args = parser.parse_args()
    if args.width <= 0 or args.height <= 0:
        print("ERROR preview: width y height deben ser positivos", file=sys.stderr)
        return 1
    try:
        compose_preview(args.video, args.overlay, args.output, args.width, args.height)
    except (FileNotFoundError, RuntimeError) as error:
        print(f"ERROR preview: {error}", file=sys.stderr)
        return 1
    print(f"Vista previa QC: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

