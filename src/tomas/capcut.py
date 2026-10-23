"""Exporta a CapCut: el maquetado (una pista con los cortes) o el orden multicámara (una pista por cámara).

Parte de la plantilla real de CapCut `out/capcut_plantilla/dos-pistas` (como `src/nle_bridge/build_capcut_from_template.py`),
conserva todo su esqueleto y regenera pistas, segmentos y materiales. No escribe en la carpeta de CapCut: deja el
proyecto en out/capcut_listo/<nombre>/ y los medios en ~/Movies/editor-ia/<slug>/ (macOS no deja a CapCut leer el
Escritorio). Se instala con `python3 src/nle_bridge/install_capcut_draft.py "out/capcut_listo/<nombre>"` con CapCut cerrado.
"""
import copy
import json
import re
import shutil
import subprocess
import time
import uuid
from pathlib import Path

from .util import DATA, REPO, probe, read_json

HOME = Path.home()
ROOT = HOME / "Movies/CapCut/User Data/Projects/com.lveditor.draft"
PLANTILLA = REPO / "out/capcut_plantilla/dos-pistas"
UUID = re.compile(r"[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}")
EXTRAS = ["speeds", "placeholder_infos", "canvases", "sound_channel_mappings", "material_colors", "vocal_separations"]
US = 1_000_000


def _uid() -> str:
    return str(uuid.uuid4()).upper()


def construir(nombre: str, pistas: list[dict], plantilla: Path = PLANTILLA, media_root: Path = HOME / "Movies/editor-ia",
              log=print) -> Path:
    """pistas: [{"nombre", "silenciar": bool, "segmentos": [{"archivo", "origen": s, "dur": s, "destino": s}]}]"""
    slug = re.sub(r"[^A-Za-z0-9]+", "-", nombre).strip("-").lower() or "proyecto"
    final, build, media = ROOT / nombre, REPO / "out/capcut_listo" / nombre, media_root / slug
    if not plantilla.is_dir():
        raise FileNotFoundError(f"Falta la plantilla de CapCut: {plantilla}")
    if build.exists():
        shutil.rmtree(build)
    build.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(plantilla, build)

    # 1) identificadores nuevos en todo el esqueleto y nombre del proyecto
    textos = {f: f.read_text(encoding="utf-8") for f in build.rglob("*") if f.is_file() and f.suffix in {".json", ".bak", ".tmp"}}
    ids = set().union(*(set(UUID.findall(t)) for t in textos.values()))
    mapping = {u: (_uid() if u.upper() == u else str(uuid.uuid4())) for u in ids}
    proj0 = json.loads((plantilla / "Timelines/project.json").read_text(encoding="utf-8"))
    old_tl = proj0["main_timeline_id"]
    new_tl = mapping[old_tl]
    for f, t in textos.items():
        t = UUID.sub(lambda m: mapping.get(m.group(0), m.group(0)), t)
        t = t.replace(str(plantilla.resolve()), str(final)).replace(f'"{plantilla.name}"', f'"{nombre}"')
        f.write_text(t, encoding="utf-8")
    (build / "Timelines" / old_tl).rename(build / "Timelines" / new_tl)

    # 2) medios: copia limpia en ~/Movies/editor-ia (sin atributos extendidos de macOS)
    media.mkdir(parents=True, exist_ok=True)
    unicos: dict[str, dict] = {}
    for p in pistas:
        for s in p["segmentos"]:
            a = str(Path(s["archivo"]).resolve())
            if a not in unicos:
                dest = media / Path(a).name
                n = 1
                while dest.exists() and any(u["destino"] == str(dest) for u in unicos.values()):
                    dest = media / f"{Path(a).stem}_{n}{Path(a).suffix}"
                    n += 1
                log(f"Copiando {Path(a).name} a {media}")
                shutil.copyfile(a, dest)
                unicos[a] = {"destino": str(dest), "meta": probe(Path(a))}
    primero = next(iter(unicos.values()))["meta"]
    ancho, alto = primero["ancho"] or 1920, primero["alto"] or 1080

    # 3) nuevo draft_info a partir de la plantilla
    d = json.loads((build / "draft_info.json").read_text(encoding="utf-8"))
    mats = d["materials"]
    tv, tseg, ttrack = copy.deepcopy(mats["videos"][0]), copy.deepcopy(d["tracks"][0]["segments"][0]), copy.deepcopy(d["tracks"][0])
    t_extras = {k: copy.deepcopy(mats[k][0]) for k in EXTRAS}
    ref_kind = {r: k for k in EXTRAS for r in tseg["extra_material_refs"] if any(m["id"] == r for m in mats[k])}
    for k in ["videos"] + EXTRAS:
        mats[k] = []
    id_video: dict[str, str] = {}
    for a, u in unicos.items():
        v = copy.deepcopy(tv)
        v.update(id=_uid(), unique_id=uuid.uuid4().hex, path=u["destino"], material_name=Path(u["destino"]).name,
                 duration=int(u["meta"]["duracion"] * US), width=u["meta"]["ancho"], height=u["meta"]["alto"],
                 has_audio=u["meta"]["tiene_audio"])
        mats["videos"].append(v)
        id_video[a] = v["id"]
    tracks, total, idx = [], 0, 0
    for ti, p in enumerate(pistas):
        tr = copy.deepcopy(ttrack)
        tr.update(id=_uid(), flag=0 if ti == 0 else 2, name=p.get("nombre", ""), is_default_name=not p.get("nombre"), segments=[])
        for s in sorted(p["segmentos"], key=lambda s: s["destino"]):
            sg = copy.deepcopy(tseg)
            refs = []
            for r in tseg["extra_material_refs"]:
                e = copy.deepcopy(t_extras[ref_kind[r]])
                e["id"] = _uid()
                mats[ref_kind[r]].append(e)
                refs.append(e["id"])
            dur, ini = int(round(s["dur"] * US)), int(round(s["origen"] * US))
            dest = int(round(s["destino"] * US))
            sg.update(id=_uid(), material_id=id_video[str(Path(s["archivo"]).resolve())], extra_material_refs=refs,
                      source_timerange={"start": ini, "duration": dur}, target_timerange={"start": dest, "duration": dur},
                      speed=1.0, render_index=idx, track_render_index=idx, volume=0.0 if p.get("silenciar") else 1.0,
                      last_nonzero_volume=1.0)
            tr["segments"].append(sg)
            total = max(total, dest + dur)
        tracks.append(tr)
        idx += 1
    d["tracks"] = tracks
    d["duration"] = total
    d["canvas_config"].update(width=ancho, height=alto, ratio="original")
    d["name"] = nombre
    for f in [build / "draft_info.json", build / "draft_info.json.bak", build / "template-2.tmp",
              build / "Timelines" / new_tl / "draft_info.json", build / "Timelines" / new_tl / "draft_info.json.bak",
              build / "Timelines" / new_tl / "template-2.tmp"]:
        if f.exists():
            f.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    # 4) instantánea auxiliar: se deja vacía para que CapCut la regenere al abrir
    mini = build / "Timelines" / new_tl / "attachment/patch/mini_draft.json"
    if mini.is_file():
        m = json.loads(mini.read_text(encoding="utf-8"))
        md = m["mini_draft_data"]
        md["draft"].update(tracks=[], duration=0)
        md["segments"], md["material_drafts"], m["base_mini_draft_has_ack"] = [], [], False
        mini.write_text(json.dumps(m, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    # 5) metadatos del proyecto
    now_us, now_s = int(time.time() * US), int(time.time())
    meta_p = build / "draft_meta_info.json"
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    meta.update(draft_name=nombre, draft_fold_path=str(final), draft_root_path=str(ROOT), tm_draft_create=now_us,
                tm_draft_modified=now_us, tm_duration=total)
    for grp in meta["draft_materials"]:
        vids = [e for e in grp["value"] if e.get("metetype") == "video"]
        if not vids:
            continue
        tmpl = copy.deepcopy(vids[0])
        grp["value"] = [e for e in grp["value"] if e.get("metetype") != "video"]
        for u in unicos.values():
            e = copy.deepcopy(tmpl)
            dur = int(u["meta"]["duracion"] * US)
            e.update(id=str(uuid.uuid4()), extra_info=Path(u["destino"]).name, file_Path=u["destino"], duration=dur,
                     width=u["meta"]["ancho"], height=u["meta"]["alto"], metetype="video",
                     roughcut_time_range={"start": 0, "duration": dur}, create_time=now_s, import_time=now_s, import_time_ms=now_us)
            grp["value"].append(e)
    meta_p.write_text(json.dumps(meta, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    pj_files = [build / "Timelines/project.json", build / "Timelines/project.json.bak"]
    for f in pj_files:
        if f.exists():
            pj = json.loads(f.read_text(encoding="utf-8"))
            pj["create_time"] = pj["update_time"] = now_us
            for t in pj["timelines"]:
                t["create_time"] = t["update_time"] = now_us
            f.write_text(json.dumps(pj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    primero_path = Path(next(iter(unicos)))
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", "1", "-i", str(primero_path), "-frames:v", "1", "-q:v", "3",
                    str(build / "draft_cover.jpg")], check=False)

    root = json.loads((ROOT / "root_meta_info.json").read_text(encoding="utf-8")) if (ROOT / "root_meta_info.json").exists() else None
    base = root["all_draft_store"][0] if root and root.get("all_draft_store") else {}
    entry = {**copy.deepcopy(base), "draft_id": meta["draft_id"], "draft_name": nombre, "draft_fold_path": str(final),
             "draft_root_path": str(ROOT), "draft_json_file": str(final / "draft_info.json"), "draft_cover": str(final / "draft_cover.jpg"),
             "tm_draft_create": now_us, "tm_draft_modified": now_us, "tm_duration": total}
    (build.parent / f"{nombre}.root_entry.json").write_text(json.dumps(entry, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"Proyecto CapCut listo: {build}")
    return build


def desde_maquetado(proyecto: str, nombre: str | None = None, log=print) -> Path:
    m = read_json(DATA / proyecto / "maquetado/maquetado.json")
    if not m or not m["segmentos"]:
        raise ValueError("Primero ejecuta el maquetado.")
    segs, t = [], 0.0
    for s in m["segmentos"]:
        segs.append({"archivo": m["clips"][s["clip"]], "origen": s["start"], "dur": s["end"] - s["start"], "destino": t})
        t += s["end"] - s["start"]
    return construir(nombre or f"Maquetado {proyecto}", [{"nombre": "Maquetado", "segmentos": segs}], log=log)


def desde_multicam(proyecto: str, nombre: str | None = None, log=print) -> Path:
    m = read_json(DATA / proyecto / "multicam/multicam.json")
    if not m:
        raise ValueError("Primero ordena los clips multicámara.")
    pistas = []
    for cam in m["camaras"]:
        clips = [c for c in m["clips"] if c["camara"] == cam]
        pistas.append({"nombre": cam, "segmentos": [{"archivo": c["archivo"], "origen": 0.0, "dur": c["duracion"], "destino": c["inicio"]} for c in clips],
                       "_audio": sum(c["duracion"] for c in clips if c["tiene_audio"])})
    mejor = max(range(len(pistas)), key=lambda i: pistas[i]["_audio"])
    for i, p in enumerate(pistas):
        p["silenciar"] = i != mejor        # solo suena una cámara: evita eco entre micrófonos
        p.pop("_audio")
    log(f"Suena solo «{pistas[mejor]['nombre']}»; las demás pistas están en silencio (se puede cambiar en CapCut).")
    return construir(nombre or f"Multicamara {proyecto}", pistas, log=log)
