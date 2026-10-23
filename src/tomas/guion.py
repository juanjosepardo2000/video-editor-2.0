"""Lectura del guion y fidelidad de una toma al guion (misma idea, aunque cambien palabras u orden).

El juez semántico es intercambiable: "difuso" (sin conexión, solapamiento de palabras con tolerancia a
variantes) o "claude" (opcional; usa la variable de entorno ANTHROPIC_API_KEY solo para los casos dudosos).
"""
import csv
import difflib
import io
import json
import os
import re
import urllib.request
import zipfile
from pathlib import Path

from .util import CONFIG, content_tokens, norm

U = CONFIG["umbrales"]
COLS_TEXTO = ("guion", "guión", "dialogo", "diálogo", "texto", "locucion", "locución", "audio", "narracion", "narración", "voz", "libreto")
COLS_ESCENA = ("escena", "esc", "n", "n°", "no", "numero", "número", "#")
MARCA_IMPORTANTE = re.compile(r"(\*\*|\bimportante\b|\bobligatori|\bdato clave\b|\bclave\b|!!)", re.I)


def leer_guion(path: Path) -> list[dict]:
    """Devuelve [{"n": 1, "escena": "1", "texto": "...", "importante": bool}] desde .txt/.md/.csv/.docx."""
    path = Path(path)
    suf = path.suffix.lower()
    if suf == ".docx":
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml").decode("utf-8")
        parrafos = [re.sub(r"<[^>]+>", "", p) for p in re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S)]
        lineas = [re.sub(r"&amp;", "&", p).strip() for p in parrafos if p.strip()]
        return _desde_lineas(lineas)
    texto = path.read_text(encoding="utf-8-sig", errors="replace")
    if suf in (".csv", ".tsv"):
        return _desde_tabla(texto, "\t" if suf == ".tsv" else None)
    return _desde_lineas([l.strip() for l in texto.splitlines()])


def _desde_lineas(lineas: list[str]) -> list[dict]:
    out, escena = [], ""
    for l in lineas:
        if not l:
            continue
        m = re.match(r"^(?:escena|esc\.?|sc)\s*(\d+)\b[:.\-\s]*(.*)$", l, re.I)
        if m:
            escena = m.group(1)
            l = m.group(2).strip()
            if not l:
                continue
        m = re.match(r"^(\d+)[.)\-:]\s+(.*)$", l)
        if m and not escena:
            escena = m.group(1)
        if m:
            l = m.group(2)
        out.append({"n": len(out) + 1, "escena": escena, "texto": l.strip(), "importante": bool(MARCA_IMPORTANTE.search(l))})
    return out


def _desde_tabla(texto: str, delim: str | None) -> list[dict]:
    dialect = csv.Sniffer().sniff(texto[:4096], delimiters=",;\t") if delim is None else None
    rows = list(csv.reader(io.StringIO(texto), dialect=dialect, delimiter=delim or ","))
    rows = [r for r in rows if any(c.strip() for c in r)]
    if not rows:
        return []
    def es_texto(h):
        return any(norm(c) in h for c in COLS_TEXTO)
    # la fila de encabezados puede no ser la primera (títulos antes de la tabla): se busca en las 10 primeras
    hi = next((i for i, r in enumerate(rows[:10]) if any(es_texto(norm(c)) for c in r if c.strip())), None)
    if hi is None:   # sin encabezado reconocible: la columna con más texto
        ti = max(range(len(rows[0])), key=lambda i: sum(len(r[i]) for r in rows if i < len(r)))
        cols_texto, ei, datos = [ti], None, rows
    else:
        head = [norm(c) for c in rows[hi]]
        cols_texto = [i for i, h in enumerate(head) if h and es_texto(h)]
        ei = next((i for i, h in enumerate(head) if h and (h in {norm(c) for c in COLS_ESCENA} or any(norm(c) == h for c in COLS_ESCENA))), None)
        datos = rows[hi + 1:]
    out = []
    for r in datos:
        for ti in cols_texto:
            if ti < len(r) and r[ti].strip():
                out.append({"n": len(out) + 1, "escena": r[ei].strip() if ei is not None and ei < len(r) else "",
                            "texto": r[ti].strip(), "importante": bool(MARCA_IMPORTANTE.search(r[ti]))})
    return out


# ---------------- comparación ----------------

def _coincide(a: str, b: str) -> float:
    """1.0 si las palabras son iguales; fracción parcial si comparten raíz o se parecen (variantes de transcripción)."""
    if a == b:
        return 1.0
    if len(a) >= 5 and len(b) >= 5 and a[:5] == b[:5]:
        return 0.85
    r = difflib.SequenceMatcher(None, a, b).ratio()
    return r if r >= 0.8 else 0.0


def solape(toma: list[str], ref: list[str]) -> tuple[float, float]:
    """(cobertura del guion, precisión de la toma) con emparejamiento voraz tolerante a variantes."""
    if not toma or not ref:
        return 0.0, 0.0
    libres = list(toma)
    acierto = 0.0
    for r in ref:
        mejor, j = 0.0, -1
        for k, t in enumerate(libres):
            s = _coincide(r, t)
            if s > mejor:
                mejor, j = s, k
                if s == 1.0:
                    break
        if j >= 0:
            acierto += mejor
            libres.pop(j)
    return acierto / len(ref), acierto / len(toma)


def mejor_tramo(texto_toma: str, guion: list[dict], max_lineas: int = 4) -> dict:
    """Busca el tramo de líneas consecutivas del guion más parecido a lo dicho en la toma."""
    t = content_tokens(texto_toma)
    mejor = {"f1": 0.0, "cobertura": 0.0, "precision": 0.0, "desde": None, "hasta": None}
    if not t:
        return mejor
    toks = [content_tokens(g["texto"]) for g in guion]
    for i in range(len(guion)):
        ref: list[str] = []
        for j in range(i, min(i + max_lineas, len(guion))):
            ref = ref + toks[j]
            cov, prec = solape(t, ref)
            f1 = 2 * cov * prec / (cov + prec) if cov + prec else 0.0
            if f1 > mejor["f1"]:
                mejor = {"f1": f1, "cobertura": cov, "precision": prec, "desde": i, "hasta": j}
    return mejor


def juez_claude(toma: str, ref: str, modelo: str = "claude-haiku-5-5") -> dict | None:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return None
    prompt = ("Compara lo que dijo un actor en una toma con la línea del guion. Responde SOLO un JSON: "
              '{"misma_idea": true|false, "completa": true|false, "score": 0..1, "motivo": "una frase en español"}. '
              "Cambiar palabras o el orden de las frases es válido si la idea es la misma.\n\n"
              f"GUION: {ref}\nTOMA: {toma}")
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", method="POST",
                                 data=json.dumps({"model": modelo, "max_tokens": 200,
                                                  "messages": [{"role": "user", "content": prompt}]}).encode(),
                                 headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            txt = json.loads(r.read())["content"][0]["text"]
        return json.loads(txt[txt.find("{"): txt.rfind("}") + 1])
    except Exception:
        return None


def fidelidad(texto_toma: str, guion: list[dict], juez: str = "difuso") -> dict:
    """Estado del criterio «Fiel al guion» para una toma, con motivo y la línea/escena detectada."""
    if not guion:
        return {"estado": "warn", "motivo": "sin guion cargado: no se puede comprobar", "valores": {}, "eventos": []}
    t = mejor_tramo(texto_toma, guion)
    if t["desde"] is None:
        return {"estado": "fail", "motivo": "no se detectó habla que coincida con el guion", "valores": {"cobertura": 0.0}, "eventos": []}
    lineas = guion[t["desde"]: t["hasta"] + 1]
    ref = " ".join(l["texto"] for l in lineas)
    cov, prec, f1 = t["cobertura"], t["precision"], t["f1"]
    motivo_juez = None
    if juez == "claude" and U["guion_dudoso"] <= f1 < U["guion_ok"] + 0.1:
        j = juez_claude(texto_toma, ref)
        if j:
            f1 = max(f1, float(j.get("score", f1))) if j.get("misma_idea") else min(f1, float(j.get("score", f1)))
            motivo_juez = j.get("motivo")
    if f1 >= U["guion_ok"]:
        estado, motivo = "pass", f"dice lo del guion (cobertura {cov*100:.0f}%)"
    elif f1 >= U["guion_dudoso"]:
        estado = "warn"
        motivo = (f"dice solo una parte del guion (cobertura {cov*100:.0f}%): posible frase a medias" if cov < prec
                  else f"añade o cambia bastante respecto al guion (precisión {prec*100:.0f}%): revisar si mantiene la idea")
    else:
        estado = "fail"
        motivo = (f"no se parece al guion (cobertura {cov*100:.0f}%, precisión {prec*100:.0f}%): se equivoca, divaga o es otra línea")
    if motivo_juez:
        motivo += f" · juez: {motivo_juez}"
    esc = next((l["escena"] for l in lineas if l["escena"]), "")
    return {"estado": estado, "motivo": motivo,
            "valores": {"cobertura": round(cov, 3), "precision": round(prec, 3), "f1": round(f1, 3),
                        "lineas": [l["n"] for l in lineas], "escena": esc,
                        "importante": any(l["importante"] for l in lineas)},
            "eventos": []}
