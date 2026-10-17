"""Genera archivos de proyecto de CapCut a partir del pipeline."""
import json
from pathlib import Path


def export_project(rough_cut: str, transcript_path: str = "pipeline/transcript.json",
                   output_dir: str = "out/capcut_project") -> Path:
    """Crea la carpeta de proyecto CapCut (draft_content.json) con pistas de video, audio y texto."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    draft = {"tracks": [], "materials": {}, "source": rough_cut}
    # TODO: mapear segmentos, subtítulos y SFX a la estructura de CapCut.
    (out / "draft_content.json").write_text(json.dumps(draft, indent=2), encoding="utf-8")
    return out


if __name__ == "__main__":
    print("capcut_exporter: stub — implementar export_project()")
