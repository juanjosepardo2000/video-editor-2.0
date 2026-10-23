import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from tomas import guion as G  # noqa: E402
from tomas import multicam as M  # noqa: E402

GUION = [{"n": 1, "escena": "1", "texto": "Hoy vamos a explicar cómo funciona el sistema de control de tomas", "importante": False},
         {"n": 2, "escena": "2", "texto": "El precio final es de cien dólares al mes", "importante": True}]


def test_fidelidad_acepta_palabras_y_orden_distintos():
    r = G.fidelidad("el sistema de control de tomas, hoy vamos a explicar cómo funciona", GUION)
    assert r["estado"] == "pass" and r["valores"]["escena"] == "1"


def test_fidelidad_rechaza_otra_cosa():
    assert G.fidelidad("ayer fui al mercado a comprar manzanas y peras", GUION)["estado"] == "fail"


def test_fidelidad_detecta_frase_a_medias():
    assert G.fidelidad("el precio final es de", GUION)["estado"] in ("warn", "fail")


def test_leer_guion_txt(tmp_path):
    f = tmp_path / "g.txt"
    f.write_text("Escena 3\nPrimera línea importante **\n\nSegunda línea\n", encoding="utf-8")
    g = G.leer_guion(f)
    assert [x["escena"] for x in g] == ["3", "3"] and g[0]["importante"]


def test_gcc_phat_recupera_el_desfase():
    rng = np.random.default_rng(1)
    s = rng.standard_normal(M.SR * 30).astype(np.float32)
    a, b = s[: M.SR * 20], 0.4 * s[M.SR * 12: M.SR * 30]       # b empieza 12 s después de a
    d, conf, _ = M.gcc_phat(a, b)
    assert abs(d - 12.0) < 0.01 and conf > M.CONF_OK
