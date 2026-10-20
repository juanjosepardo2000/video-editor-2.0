import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import {fileURLToPath} from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const source = fs.readFileSync(path.join(here, "BeatGraphic.tsx"), "utf8");

for (const tag of ["contador", "cifra", "comparacion", "lista", "interludio", "titular", "busqueda"]) {
  assert.match(source, new RegExp(`tag === ["']${tag}["']`), `Falta selector para [${tag}].`);
}
assert.match(source, /DynamicNumberCounter/);
assert.match(source, /LiquidGlassCardV2/);
assert.doesNotMatch(source, /Contexto|Ver detalle|Dato destacado|Resultado/);

const captionSource = fs.readFileSync(path.join(here, "WordByWordCaptions.tsx"), "utf8");
assert.match(captionSource, /fontSize:\s*isAccented\s*\?/);
assert.match(captionSource, /accentFontFamily/);

console.log("Beat graphic selector tests: 12/12 OK");
