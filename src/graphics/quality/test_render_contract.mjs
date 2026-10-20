import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const composition = fs.readFileSync(path.resolve(here, "../compositions/BeatMapComposition.tsx"), "utf8");
const card = fs.readFileSync(path.resolve(here, "../components/LiquidGlassCardV2.tsx"), "utf8");

assert.doesNotMatch(composition, /beat\.onScreenText\s*\|\|\s*beat\.speech/);
assert.doesNotMatch(composition, /beat\.speech\s*\|\|\s*beat\.onScreenText/);
assert.doesNotMatch(composition, /Búsqueda asistida|Dato destacado|Evolución positiva|Actualidad|Minthy BeatMap/);
assert.match(composition, /bottom:\s*safeArea\.bottom\s*\+\s*150/);
assert.match(card, /actionLabel,\s*\n/);
assert.doesNotMatch(card, /actionLabel\s*=\s*["']Ver detalle["']/);

console.log("Graphics render contract tests: 6/6 OK");
