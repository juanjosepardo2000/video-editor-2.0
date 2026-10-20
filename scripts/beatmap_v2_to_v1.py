"""Convierte un beat map v2 (con B-roll y Zona) a v1 para los lectores que aún no aceptan v2.

Ejemplo: python3 scripts/beatmap_v2_to_v1.py pipeline/beatmap.v2.md pipeline/beatmap.md
No pierde datos del original (el v2 sigue siendo la fuente de verdad).
"""
import re
import sys
from pathlib import Path

DROP = ("B-roll", "Zona")


def convert(text: str) -> str:
    lines, out, drop_indexes = text.splitlines(), [], None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("|") and drop_indexes is None and "Inicio" in line and "Fin" in line:
            header = [c.strip() for c in stripped.strip("|").split("|")]
            drop_indexes = [header.index(name) for name in DROP if name in header]
        if drop_indexes and stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if re.fullmatch(r"[-: ]+", "".join(cells)):
                cells = ["---"] * (len(cells) - len(drop_indexes))
            else:
                cells = [c for i, c in enumerate(cells) if i not in drop_indexes]
            line = "| " + " | ".join(cells) + " |" if cells[0] != "---" else "|" + "---|" * len(cells)
        elif stripped.startswith("> Contrato: v2"):
            line = "> Contrato: v1 (convertido desde v2 con scripts/beatmap_v2_to_v1.py)"
        out.append(line)
    return "\n".join(out) + "\n"


def main() -> int:
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    source, target = Path(sys.argv[1]), Path(sys.argv[2])
    target.write_text(convert(source.read_text(encoding="utf-8")), encoding="utf-8")
    print(f"{source} -> {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
