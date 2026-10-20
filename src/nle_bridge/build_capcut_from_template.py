"""Construye un proyecto CapCut (probado con 9.4.0 en macOS) usando un proyecto real como plantilla.

La plantilla es un proyecto tuyo de CapCut con dos pistas de video (base y overlay); solo se lee.
Este script NO escribe en la carpeta de CapCut: deja el proyecto en out/capcut_listo/ y los medios en
~/Movies/editor-ia/<proyecto>/. Motivo: macOS protege Escritorio, Documentos y Descargas, y CapCut solo puede
leer ahí los archivos que el usuario eligió con su selector; ~/Movies no está protegida y es donde CapCut guarda sus datos.
Para instalarlo: install_capcut_draft.py.

Ejemplo:
    python3 src/nle_bridge/build_capcut_from_template.py --name "Mi video" \
        --base out/entrega/base_con_audio.mp4 --overlay out/entrega/overlay_graficos.mov
"""
import argparse
import json
import re
import shutil
import subprocess
import time
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HOME = Path.home()
ROOT = HOME / "Movies/CapCut/User Data/Projects/com.lveditor.draft"   # ubicación final (solo para rutas)

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--name", default="Prueba Editor IA")
parser.add_argument("--base", type=Path, default=REPO / "out/entrega/base_con_audio.mp4", help="video base con audio mezclado")
parser.add_argument("--overlay", type=Path, default=REPO / "out/entrega/overlay_graficos.mov", help="overlay con transparencia")
parser.add_argument("--cover-video", type=Path, default=REPO / "out/entrega/video_editado_1080x1920.mp4")
parser.add_argument("--template", default="1017", help="nombre de un proyecto tuyo de CapCut con 2 pistas de video")
parser.add_argument("--template-dir", type=Path, help="carpeta de plantilla (p. ej. out/capcut_plantilla/dos-pistas); tiene prioridad")
parser.add_argument("--media-root", type=Path, default=HOME / "Movies/editor-ia")
args = parser.parse_args()

NAME = args.name
FINAL = ROOT / NAME
SRC = args.template_dir.resolve() if args.template_dir else ROOT / args.template
BUILD = REPO / "out/capcut_listo" / NAME
slug = re.sub(r"[^A-Za-z0-9]+", "-", NAME).strip("-").lower() or "proyecto"
MEDIA = args.media_root / slug
assert SRC.is_dir(), f"No existe la plantilla {SRC}"


def stage(path: Path) -> Path:
    """Deja una copia limpia del medio en ~/Movies/editor-ia (copyfile: sin atributos extendidos de macOS)."""
    MEDIA.mkdir(parents=True, exist_ok=True)
    target = MEDIA / path.name
    if target.exists():
        target.unlink()
    shutil.copyfile(path, target)
    return target


BASE, OVER = stage(args.base), stage(args.overlay)
if BUILD.exists():
    shutil.rmtree(BUILD)
BUILD.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(SRC, BUILD)


def probe(p):
    o = json.loads(subprocess.check_output(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(p)]))
    v = next(s for s in o["streams"] if s["codec_type"] == "video")
    return int(float(o["format"]["duration"]) * 1_000_000), v["width"], v["height"]


base_dur, bw, bh = probe(BASE)
over_dur, ow, oh = probe(OVER)
total = max(base_dur, over_dur)
print("base", base_dur, bw, bh, "| overlay", over_dur, ow, oh)

# datos de la plantilla: qué material es la base (pista 0) y cuál el overlay (pista 1)
t_info = json.loads((BUILD / "draft_info.json").read_text(encoding="utf-8"))
t_mats = {v["id"]: v for v in t_info["materials"]["videos"]}
t_segs = [t["segments"][0] for t in t_info["tracks"] if t["type"] == "video"]
assert len(t_segs) >= 2, "La plantilla debe tener dos pistas de video"
t_base, t_over = t_mats[t_segs[0]["material_id"]], t_mats[t_segs[1]["material_id"]]
T = {"base_name": t_base["material_name"], "over_name": t_over["material_name"], "base_path": t_base["path"],
     "over_path": t_over["path"], "base_dur": t_base["duration"], "base_w": t_base["width"], "base_h": t_base["height"],
     "base_src": t_segs[0]["source_timerange"]["duration"], "base_tgt": t_segs[0]["target_timerange"]["duration"],
     "base_speed": t_segs[0]["speed"], "total": t_info["duration"], "over_dur": t_over["duration"]}

proj0 = json.loads((BUILD / "Timelines/project.json").read_text(encoding="utf-8"))
meta0 = json.loads((BUILD / "draft_meta_info.json").read_text(encoding="utf-8"))

UUID = re.compile(r"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}")
texts = {f: f.read_text(encoding="utf-8") for f in BUILD.rglob("*") if f.is_file() and f.suffix in {".json", ".bak", ".tmp"}}
found = set()
for t in texts.values():
    found |= set(UUID.findall(t))
mapping = {u: (str(uuid.uuid4()).upper() if u.upper() == u else str(uuid.uuid4())) for u in found}
remap = lambda t: UUID.sub(lambda m: mapping.get(m.group(0), m.group(0)), t)

old_tl = proj0["main_timeline_id"]
new_tl = mapping[old_tl]
repl = [(T["base_path"], str(BASE)), (T["over_path"], str(OVER)), (T["base_name"], BASE.name), (T["over_name"], OVER.name),
        (str(SRC), str(FINAL)), (f'"{args.template}"', f'"{NAME}"'), (f'"{SRC.name}"', f'"{NAME}"')]
for f, t in texts.items():
    t = remap(t)
    for a, b in repl:
        t = t.replace(a, b)
    f.write_text(t, encoding="utf-8")
(BUILD / "Timelines" / old_tl).rename(BUILD / "Timelines" / new_tl)


def edit_info(path):
    d = json.loads(path.read_text(encoding="utf-8"))
    vids = d["materials"]["videos"]
    b = next(v for v in vids if v["material_name"] == BASE.name)
    o = next(v for v in vids if v["material_name"] == OVER.name)
    b.update(duration=base_dur, width=bw, height=bh, has_audio=True)
    o.update(duration=over_dur, width=ow, height=oh, has_audio=False)
    seg_b = next(s for t in d["tracks"] for s in t["segments"] if s["material_id"] == b["id"])
    seg_o = next(s for t in d["tracks"] for s in t["segments"] if s["material_id"] == o["id"])
    for seg, dur in ((seg_b, base_dur - 1000), (seg_o, over_dur)):
        seg["source_timerange"] = {"start": 0, "duration": dur}
        seg["target_timerange"] = {"start": 0, "duration": dur}
        seg["speed"] = 1.0
    fill = max(1080 / bw, 1920 / bh)            # escala "llenar" relativa al ajuste "contener" del lienzo 1080x1920
    contain = min(1080 / bw, 1920 / bh)
    seg_b["clip"]["scale"] = {"x": round(fill / contain, 4), "y": round(fill / contain, 4)}
    refs = set(seg_b.get("extra_material_refs", [])) | set(seg_o.get("extra_material_refs", []))
    for sp in d["materials"]["speeds"]:
        if sp["id"] in refs:
            sp["speed"] = 1.0
    d["duration"] = total
    path.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


for p in [BUILD / "draft_info.json", BUILD / "draft_info.json.bak", BUILD / "template-2.tmp",
          BUILD / "Timelines" / new_tl / "draft_info.json", BUILD / "Timelines" / new_tl / "draft_info.json.bak",
          BUILD / "Timelines" / new_tl / "template-2.tmp"]:
    if p.exists():
        edit_info(p)

now_us, now_s = int(time.time() * 1_000_000), int(time.time())
m = json.loads((BUILD / "draft_meta_info.json").read_text(encoding="utf-8"))
m.update(draft_name=NAME, draft_fold_path=str(FINAL), draft_root_path=str(ROOT), tm_draft_create=now_us, tm_draft_modified=now_us,
         tm_duration=total, draft_id=mapping.get(meta0["draft_id"], str(uuid.uuid4()).upper()))
for grp in m["draft_materials"]:
    for e in grp["value"]:
        if e["extra_info"] == BASE.name:
            e.update(duration=base_dur - 1000, width=bw, height=bh, file_Path=str(BASE), metetype="video")
            e["roughcut_time_range"] = {"start": 0, "duration": base_dur - 1000}
        if e["extra_info"] == OVER.name:
            e.update(duration=over_dur, width=ow, height=oh, file_Path=str(OVER), metetype="video")
            e["roughcut_time_range"] = {"start": 0, "duration": over_dur}
        e["create_time"] = e["import_time"] = now_s
        e["import_time_ms"] = now_us
(BUILD / "draft_meta_info.json").write_text(json.dumps(m, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

pj = json.loads((BUILD / "Timelines/project.json").read_text(encoding="utf-8"))
pj["create_time"] = pj["update_time"] = now_us
for t in pj["timelines"]:
    t["create_time"] = t["update_time"] = now_us
for f in ("project.json", "project.json.bak"):
    p = BUILD / "Timelines" / f
    if p.exists():
        p.write_text(json.dumps(pj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

if args.cover_video.is_file():
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", "1.5", "-i", str(args.cover_video), "-frames:v", "1", "-q:v", "3",
                    str(BUILD / "draft_cover.jpg")], check=True)


def fix_mini(path):
    """Instantánea auxiliar: mismos valores que el draft_info."""
    d = json.loads(path.read_text(encoding="utf-8"))

    def walk(x):
        if isinstance(x, dict):
            if x.get("width") == T["base_w"] and x.get("height") == T["base_h"]:
                x["width"], x["height"] = bw, bh
            for k, v in list(x.items()):
                if k == "duration" and v == T["base_dur"]:
                    x[k] = base_dur
                elif k == "duration" and v in (T["base_src"], T["base_tgt"]):
                    x[k] = base_dur - 1000
                elif k == "duration" and v in (T["total"], T["over_dur"]):
                    x[k] = total
                elif k == "speed" and v == T["base_speed"]:
                    x[k] = 1.0
                else:
                    walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(d)
    path.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


mini = BUILD / "Timelines" / new_tl / "attachment/patch/mini_draft.json"
if mini.is_file():
    fix_mini(mini)

root = json.loads((ROOT / "root_meta_info.json").read_text(encoding="utf-8"))
tpl = next((e for e in root["all_draft_store"] if e["draft_name"] == args.template), root["all_draft_store"][0])
entry = json.loads(json.dumps(tpl))
entry.update(draft_id=m["draft_id"], draft_name=NAME, draft_fold_path=str(FINAL), draft_root_path=str(ROOT),
             draft_json_file=str(FINAL / "draft_info.json"), draft_cover=str(FINAL / "draft_cover.jpg"),
             tm_draft_create=now_us, tm_draft_modified=now_us, tm_duration=total)
(BUILD.parent / f"{NAME}.root_entry.json").write_text(json.dumps(entry, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"Construido: {BUILD}\nMedios en:  {MEDIA}\nSiguiente:  python3 src/nle_bridge/install_capcut_draft.py \"{BUILD.relative_to(REPO)}\"")
