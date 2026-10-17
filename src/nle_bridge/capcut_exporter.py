"""Genera un borrador CapCut autocontenido a partir del contrato BeatMap.

No toca la biblioteca de CapCut: escribe una carpeta transportable en ``out/``.
El esquema de CapCut no es oficial ni estable, por lo que la validación local no
sustituye la prueba final con una copia en la versión macOS objetivo.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


US = 1_000_000
BEAT_HEADER = ["#", "Inicio", "Fin", "Speech", "Escena", "Visual", "Transición", "SFX", "Caption"]
SCENES = {"CAPTIONS", "CAPTION_UI", "SPLIT", "FULLSCREEN"}
MATERIAL_KEYS = [
    "videos", "audios", "texts", "stickers", "video_effects", "transitions",
    "masks", "chromas", "audio_fades", "audio_effects", "canvases", "speeds",
    "sound_channel_mappings", "vocal_separations", "placeholders", "common_mask",
]


@dataclass(frozen=True)
class Beat:
    number: int
    start: float
    end: float
    speech: str
    scene: str
    visual: str
    transition: str
    sfx: str
    caption: str


@dataclass(frozen=True)
class Word:
    text: str
    start: float
    end: float


def _uid() -> str:
    return str(uuid.uuid4()).upper()


def _seconds(value: str) -> float:
    match = re.fullmatch(r"(\d{2,}):(\d{2})\.(\d)", value.strip())
    if not match:
        raise ValueError(f"Tiempo inválido '{value}'; usa mm:ss.s")
    minutes, seconds, tenths = map(int, match.groups())
    if seconds >= 60:
        raise ValueError(f"Tiempo inválido '{value}'; los segundos deben ser < 60")
    return minutes * 60 + seconds + tenths / 10


def parse_beatmap(path: Path) -> list[Beat]:
    lines = path.read_text(encoding="utf-8").splitlines()
    header_index = next((i for i, line in enumerate(lines) if line.strip().startswith("| # | Inicio | Fin |")), None)
    if header_index is None:
        raise ValueError("BeatMap: no se encontró la tabla ## Beats con el contrato nuevo")
    header = [part.strip() for part in lines[header_index].strip().strip("|").split("|")]
    if header != BEAT_HEADER:
        raise ValueError(f"BeatMap: columnas inválidas. Esperadas: {' | '.join(BEAT_HEADER)}")
    beats: list[Beat] = []
    for line in lines[header_index + 2:]:
        if not line.strip().startswith("|"):
            break
        cells = [part.strip() for part in line.strip().strip("|").split("|")]
        if len(cells) != len(BEAT_HEADER):
            raise ValueError(f"BeatMap: fila con {len(cells)} columnas; se esperaban {len(BEAT_HEADER)}")
        start, end = _seconds(cells[1]), _seconds(cells[2])
        if end <= start:
            raise ValueError(f"BeatMap: beat {cells[0]} termina antes de comenzar")
        if beats and start < beats[-1].end:
            raise ValueError(f"BeatMap: beat {cells[0]} se solapa con el anterior")
        if cells[4] not in SCENES:
            raise ValueError(f"BeatMap: escena desconocida '{cells[4]}' en beat {cells[0]}")
        speech = cells[3].strip('"')
        if not speech:
            raise ValueError(f"BeatMap: Speech vacío en beat {cells[0]}")
        beats.append(Beat(int(cells[0]), start, end, speech, cells[4], cells[5], cells[6], cells[7], cells[8]))
    if not beats:
        raise ValueError("BeatMap: la tabla no contiene beats")
    return beats


def _uniform_words(beats: Iterable[Beat]) -> list[Word]:
    result: list[Word] = []
    for beat in beats:
        tokens = re.findall(r"\S+", beat.speech)
        if not tokens:
            continue
        step = (beat.end - beat.start) / len(tokens)
        result.extend(Word(token, beat.start + i * step, beat.start + (i + 1) * step) for i, token in enumerate(tokens))
    return result


def load_words(transcript: Path | None, beats: list[Beat]) -> tuple[list[Word], str]:
    if transcript and transcript.exists():
        data = json.loads(transcript.read_text(encoding="utf-8"))
        raw = data.get("words") if isinstance(data, dict) else None
        if not isinstance(raw, list):
            raise ValueError("Transcript: se esperaba un objeto con una lista 'words'")
        words = [Word(str(item["word"]).strip(), float(item["start"]), float(item["end"])) for item in raw]
        if any(not word.text or word.end <= word.start for word in words):
            raise ValueError("Transcript: palabra vacía o intervalo inválido")
        return words, "transcript"
    return _uniform_words(beats), "uniform-fallback"


def _copy_asset(source: Path, destination: Path) -> Path:
    if not source.is_file():
        raise FileNotFoundError(f"No existe el recurso: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return destination


def _clip() -> dict[str, Any]:
    return {"alpha": 1.0, "rotation": 0.0, "scale": {"x": 1.0, "y": 1.0},
            "transform": {"x": 0.0, "y": 0.0}, "flip": {"horizontal": False, "vertical": False}}


def _keyframes(duration_us: int) -> list[dict[str, Any]]:
    return [{"id": _uid(), "property_type": "UNIFORM_SCALE", "keyframe_list": [
        {"id": _uid(), "time_offset": 0, "values": [1.0], "curveType": "Line"},
        {"id": _uid(), "time_offset": duration_us, "values": [1.06], "curveType": "Line"},
    ]}]


def _segment(material_id: str, start_us: int, duration_us: int, *, source_us: int = 0,
             audio: bool = False, render_index: int = 0, zoom: bool = False) -> dict[str, Any]:
    return {
        "id": _uid(), "material_id": material_id,
        "target_timerange": {"start": start_us, "duration": duration_us},
        "source_timerange": {"start": source_us, "duration": duration_us},
        "speed": 1.0, "volume": 1.0, "visible": True, "reverse": False,
        "clip": None if audio else _clip(), "render_index": render_index,
        "track_render_index": 0, "track_attribute": 0, "extra_material_refs": [],
        "common_keyframes": _keyframes(duration_us) if zoom else [], "keyframe_refs": [],
        "uniform_scale": {"on": True, "value": 1.0},
    }


def _word_is_accent(word: Word, beats: list[Beat]) -> bool:
    beat = next((item for item in beats if item.start <= word.start < item.end), None)
    if not beat or beat.caption == "-":
        return False
    clean = re.sub(r"[^\wáéíóúüñ]", "", word.text.casefold())
    keywords = {re.sub(r"[^\wáéíóúüñ]", "", item.casefold()) for item in beat.caption.split()}
    return bool(clean and clean in keywords)


def _text_material(word: Word, beats: list[Beat]) -> dict[str, Any]:
    accent = _word_is_accent(word, beats)
    color = [0.851, 0.510, 0.333] if accent else [0.96, 0.96, 0.95]
    content = {"text": word.text, "styles": [{"range": [0, len(word.text)], "size": 12,
        "bold": True, "italic": False, "underline": False,
        "fill": {"alpha": 1, "content": {"render_type": "solid", "solid": {"alpha": 1, "color": color}}}}],
        "layer_weight": 1, "effect": []}
    return {"id": _uid(), "type": "text", "content": json.dumps(content, ensure_ascii=False, separators=(",", ":")),
            "font_name": "Inter", "font_size": 12, "text_color": "#D98255FF" if accent else "#F5F5F2FF",
            "text_alpha": 1.0, "border_color": "#000000FF", "border_width": 0.0,
            "background_color": "#171717CC", "background_alpha": 0.8,
            "background_style": 1, "background_round_radius": 0.12,
            "has_shadow": True, "shadow_alpha": 0.35, "shadow_color": "#000000FF",
            "text_alignment": 1, "vertical": False, "fixed_width": -1.0, "fixed_height": -1.0,
            "letter_spacing": 0.0, "line_spacing": 0.02, "is_rich_text": False}


def build_draft(project_name: str, beats: list[Beat], words: list[Word], video_path: str,
                overlay_path: str, audio_path: str, duration_us: int) -> dict[str, Any]:
    materials = {key: [] for key in MATERIAL_KEYS}
    video_id, overlay_id, audio_id = _uid(), _uid(), _uid()
    materials["videos"] = [
        {"id": video_id, "type": "video", "material_name": Path(video_path).name, "path": video_path,
         "duration": duration_us, "width": 1080, "height": 1920, "has_audio": False},
        {"id": overlay_id, "type": "video", "material_name": Path(overlay_path).name, "path": overlay_path,
         "duration": duration_us, "width": 1080, "height": 1920, "has_audio": False},
    ]
    materials["audios"] = [{"id": audio_id, "type": "record", "name": Path(audio_path).name,
        "path": audio_path, "duration": duration_us, "wave_points": [], "category_name": "local"}]
    base_segments = []
    for beat in beats:
        start_us, beat_duration = round(beat.start * US), round((beat.end - beat.start) * US)
        base_segments.append(_segment(video_id, start_us, beat_duration, source_us=start_us, zoom=True))
    overlay_segment = _segment(overlay_id, 0, duration_us, render_index=10000)
    audio_segment = _segment(audio_id, 0, duration_us, audio=True)
    text_segments = []
    for word in words:
        start_us, word_duration = round(word.start * US), max(1, round((word.end - word.start) * US))
        material = _text_material(word, beats)
        materials["texts"].append(material)
        segment = _segment(material["id"], start_us, word_duration, render_index=15000)
        segment["clip"]["transform"]["y"] = -0.62
        text_segments.append(segment)
    return {"id": _uid(), "name": project_name, "duration": duration_us, "fps": 30,
        "canvas_config": {"width": 1080, "height": 1920, "ratio": "9:16"},
        "platform": {"app_source": "cc", "app_version": "latest-unverified", "os": "mac"},
        "tracks": [
            {"id": _uid(), "type": "video", "name": "rough-cut", "attribute": 0, "segments": base_segments},
            {"id": _uid(), "type": "video", "name": "remotion-overlays", "attribute": 0, "segments": [overlay_segment]},
            {"id": _uid(), "type": "audio", "name": "voiceover", "attribute": 0, "segments": [audio_segment]},
            {"id": _uid(), "type": "text", "name": "word-captions", "attribute": 0, "segments": text_segments},
        ], "materials": materials,
        "extra_info": {"created_via": "minthy-capcut-exporter", "schema_status": "experimental"}}


def _material_registration(material: dict[str, Any], now_s: int) -> dict[str, Any]:
    is_video = material.get("type") == "video"
    return {"ai_group_type": "", "create_time": now_s, "duration": material["duration"], "enter_from": 0,
        "extra_info": material.get("material_name", material.get("name", "")), "file_Path": material["path"],
        "height": material.get("height", 0), "id": material["local_material_id"], "import_time": now_s,
        "import_time_ms": now_s * US, "item_source": 1, "md5": "", "metetype": "video" if is_video else "audio",
        "roughcut_time_range": {"duration": material["duration"], "start": 0},
        "sub_time_range": {"duration": -1, "start": -1}, "type": 0, "width": material.get("width", 0)}


def validate_draft(draft: dict[str, Any], project_dir: Path) -> dict[str, Any]:
    errors: list[str] = []
    material_ids: set[str] = set()
    for group in draft["materials"].values():
        if isinstance(group, list):
            for material in group:
                if material["id"] in material_ids:
                    errors.append(f"material_id duplicado: {material['id']}")
                material_ids.add(material["id"])
                if "path" in material and not (project_dir / Path(material["path"])).is_file():
                    errors.append(f"medio ausente: {material['path']}")
    segment_count = 0
    for track in draft["tracks"]:
        previous_end = -1
        for segment in sorted(track["segments"], key=lambda item: item["target_timerange"]["start"]):
            segment_count += 1
            timerange = segment["target_timerange"]
            if segment["material_id"] not in material_ids:
                errors.append(f"segmento referencia material inexistente: {segment['material_id']}")
            if timerange["duration"] <= 0 or timerange["start"] < previous_end:
                errors.append(f"intervalo inválido/solapado en pista {track['name']}")
            if timerange["start"] + timerange["duration"] > draft["duration"]:
                errors.append(f"segmento fuera de la duración del proyecto en pista {track['name']}")
            previous_end = timerange["start"] + timerange["duration"]
            for group in segment["common_keyframes"]:
                offsets = [keyframe["time_offset"] for keyframe in group["keyframe_list"]]
                if offsets != sorted(offsets) or any(offset < 0 or offset > timerange["duration"] for offset in offsets):
                    errors.append(f"keyframes fuera del segmento {segment['id']}")
    return {"valid": not errors, "errors": errors, "tracks": len(draft["tracks"]),
            "segments": segment_count, "materials": len(material_ids), "duration_us": draft["duration"]}


def export_project(rough_cut: Path, overlay: Path, audio: Path, beatmap: Path,
                   transcript: Path | None, output_dir: Path, project_name: str) -> Path:
    beats = parse_beatmap(beatmap)
    words, caption_source = load_words(transcript, beats)
    duration_us = round(max(beat.end for beat in beats) * US)
    output_dir.mkdir(parents=True, exist_ok=True)
    copied_video = _copy_asset(rough_cut, output_dir / "assets" / "video" / rough_cut.name)
    copied_overlay = _copy_asset(overlay, output_dir / "assets" / "overlays" / overlay.name)
    copied_audio = _copy_asset(audio, output_dir / "assets" / "audio" / audio.name)
    relative = lambda path: path.relative_to(output_dir).as_posix()
    draft = build_draft(project_name, beats, words, relative(copied_video), relative(copied_overlay),
                        relative(copied_audio), duration_us)
    now_s = int(time.time())
    registered = [*draft["materials"]["videos"], *draft["materials"]["audios"]]
    for material in registered:
        material["local_material_id"] = _uid()
    meta = {"draft_id": draft["id"], "draft_name": project_name,
        "draft_fold_path": str(output_dir.resolve()), "draft_root_path": str(output_dir.parent.resolve()),
        "draft_json_file": str((output_dir / "draft_info.json").resolve()), "draft_cover": "",
        "draft_materials": [{"type": 0, "value": [_material_registration(item, now_s) for item in registered]}],
        "tm_draft_create": now_s * US, "tm_draft_modified": now_s * US, "tm_duration": duration_us,
        "draft_is_invisible": False, "draft_need_rename_folder": False}
    report = validate_draft(draft, output_dir)
    report.update({"project": project_name, "caption_source": caption_source,
                   "beat_count": len(beats), "word_captions": len(words),
                   "warning": "Esquema CapCut no oficial; requiere prueba en una copia con la versión macOS objetivo."})
    if not report["valid"]:
        raise ValueError("Proyecto inválido: " + "; ".join(report["errors"]))
    for filename in ("draft_info.json", "draft_content.json"):
        (output_dir / filename).write_text(json.dumps(draft, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (output_dir / "draft_meta_info.json").write_text(json.dumps(meta, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (output_dir / "validation-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera un borrador CapCut experimental y autocontenido")
    parser.add_argument("--rough-cut", type=Path, required=True)
    parser.add_argument("--overlay", type=Path, required=True)
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--beatmap", type=Path, default=Path("pipeline/beatmap.md"))
    parser.add_argument("--transcript", type=Path, default=Path("pipeline/transcript.json"))
    parser.add_argument("--output", type=Path, default=Path("out/capcut_project"))
    parser.add_argument("--project-name", default="Minthy Fixture")
    args = parser.parse_args()
    try:
        result = export_project(args.rough_cut, args.overlay, args.audio, args.beatmap,
                                args.transcript if args.transcript.exists() else None,
                                args.output, args.project_name)
    except (FileNotFoundError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR CapCut exporter: {error}", file=sys.stderr)
        return 1
    print(f"CapCut project: {result.resolve()}")
    print((result / "validation-report.json").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
