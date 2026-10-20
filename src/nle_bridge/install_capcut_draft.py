"""Instala (o desinstala) en CapCut un proyecto construido con build_capcut_from_template.py.

Seguridad: exige CapCut cerrado, no sobrescribe, guarda una copia de root_meta_info.json y permite deshacer.

Ejemplo:
    python3 src/nle_bridge/install_capcut_draft.py "out/capcut_listo/Prueba Editor IA"
    python3 src/nle_bridge/install_capcut_draft.py "out/capcut_listo/Prueba Editor IA" --uninstall
"""
import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path.home() / "Movies/CapCut/User Data/Projects/com.lveditor.draft"


def capcut_running() -> bool:
    return bool(subprocess.run(["pgrep", "-ix", "CapCut"], capture_output=True, text=True).stdout.strip())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("project", type=Path, help="carpeta del proyecto construido")
    parser.add_argument("--entry", type=Path, help="root_entry.json (por defecto «<proyecto>.root_entry.json», junto a la carpeta)")
    parser.add_argument("--uninstall", action="store_true")
    args = parser.parse_args()
    name = args.project.name
    entry_path = args.entry or args.project.parent / f"{name}.root_entry.json"
    destination = ROOT / name
    index_path = ROOT / "root_meta_info.json"

    if sys.platform != "darwin" or not index_path.is_file():
        sys.exit(f"No se encontró el índice de CapCut en {index_path}")
    if capcut_running():
        sys.exit("CapCut está abierto. Ciérralo por completo (Cmd+Q) y vuelve a ejecutar.")

    index = json.loads(index_path.read_text(encoding="utf-8"))
    backup = index_path.with_name(f"root_meta_info.json.bak-{int(time.time())}")
    shutil.copy2(index_path, backup)
    print(f"Copia del índice: {backup}")

    if args.uninstall:
        index["all_draft_store"] = [e for e in index["all_draft_store"] if e.get("draft_name") != name]
        index["draft_ids"] = len(index["all_draft_store"])
        if destination.is_dir():
            shutil.rmtree(destination)
        index_path.write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        print(f"Desinstalado: {name}")
        return 0

    if destination.exists():
        sys.exit(f"Ya existe {destination}; no se sobrescribe.")
    if not args.project.is_dir() or not entry_path.is_file():
        sys.exit("Faltan la carpeta del proyecto o root_entry.json")
    entry = json.loads(entry_path.read_text(encoding="utf-8"))
    if any(e.get("draft_id") == entry["draft_id"] for e in index["all_draft_store"]):
        sys.exit("El proyecto ya está registrado en el índice.")
    shutil.copytree(args.project, destination)
    index["all_draft_store"].insert(0, entry)
    if isinstance(index.get("draft_ids"), int):
        index["draft_ids"] += 1
    index_path.write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Instalado: {destination}\nAbre CapCut y busca el proyecto «{name}».")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
