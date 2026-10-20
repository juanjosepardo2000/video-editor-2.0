import fs from "node:fs";
import path from "node:path";
import {fileURLToPath} from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../../..");
const argument = (name) => process.argv.find((item) => item.startsWith(`--${name}=`))?.slice(name.length + 3);
const creditsPath = path.resolve(root, argument("credits") ?? "pipeline/broll_credits.json");
const outputPath = path.resolve(root, argument("output") ?? "src/graphics/broll/generated-broll.ts");
const publicDir = path.resolve(root, argument("public-dir") ?? "out/remotion-public");

const beatMapSourcePath = path.resolve(root, argument("beatmap-source") ?? "src/graphics/beatmap/generated-beatmap.ts");
const source = fs.readFileSync(beatMapSourcePath, "utf8");
const match = source.match(/export const generatedBeatMap = ([\s\S]+) as const satisfies/);
if (!match) throw new Error("No se pudo leer generated-beatmap.ts; ejecuta sync:beatmap primero.");
const beatMap = JSON.parse(match[1]);
const credits = fs.existsSync(creditsPath) ? JSON.parse(fs.readFileSync(creditsPath, "utf8")) : [];
if (!Array.isArray(credits)) throw new Error("pipeline/broll_credits.json debe ser una lista.");

const allowedRoots = [path.join(root, "assets"), path.join(root, "pipeline/broll")].map((item) => path.resolve(item));
const safeMediaPath = (candidate) => {
  const resolved = path.resolve(root, candidate);
  if (!allowedRoots.some((allowed) => resolved === allowed || resolved.startsWith(`${allowed}${path.sep}`))) {
    throw new Error(`B-roll fuera de assets/ o pipeline/broll/: ${candidate}`);
  }
  return resolved;
};

const resolveBeatFile = (beat) => {
  if (beat.broll.source === "own") {
    const relative = beat.broll.value.startsWith("assets/") ? beat.broll.value : `assets/${beat.broll.value}`;
    return safeMediaPath(relative);
  }
  const credit = credits.find((item) => Number(item.beat) === beat.index || item.query === beat.broll.value);
  if (!credit?.file) throw new Error(`Beat ${beat.index}: falta un archivo en pipeline/broll_credits.json para ${beat.broll.source}:${beat.broll.value}.`);
  return safeMediaPath(credit.file);
};

const requested = beatMap.beats.filter((beat) => beat.broll.source !== "none");
const destination = path.join(publicDir, "broll");
fs.mkdirSync(destination, {recursive: true});
const assets = requested.map((beat) => {
  const input = resolveBeatFile(beat);
  if (!fs.existsSync(input)) throw new Error(`Beat ${beat.index}: no existe el B-roll ${path.relative(root, input)}.`);
  const extension = path.extname(input).toLowerCase() || ".mp4";
  const filename = `beat-${String(beat.index).padStart(2, "0")}${extension}`;
  fs.copyFileSync(input, path.join(destination, filename));
  return {beat: beat.index, source: beat.broll.source, value: beat.broll.value, publicFile: `broll/${filename}`};
});

fs.mkdirSync(path.dirname(outputPath), {recursive: true});
fs.writeFileSync(outputPath, `import type {GeneratedBrollManifest} from "./types";\n\nexport const generatedBroll = ${JSON.stringify({assets}, null, 2)} as const satisfies GeneratedBrollManifest;\n`, "utf8");
console.log(`B-roll sincronizado: ${assets.length} clip(s).`);
