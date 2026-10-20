import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import {spawnSync} from "node:child_process";
import {fileURLToPath} from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../../..");
const temporary = fs.mkdtempSync(path.join(os.tmpdir(), "minthy-broll-"));
const media = path.join(root, "pipeline/broll/.g4-test.mp4");
const beatMap = path.join(temporary, "generated.ts");
const credits = path.join(temporary, "credits.json");
const output = path.join(temporary, "manifest.ts");
const publicDir = path.join(temporary, "public");

try {
  fs.mkdirSync(path.dirname(media), {recursive: true});
  fs.writeFileSync(media, "fixture");
  fs.writeFileSync(beatMap, `export const generatedBeatMap = ${JSON.stringify({beats: [{index: 3, broll: {source: "stock", value: "edicion"}}]})} as const satisfies unknown;\n`);
  fs.writeFileSync(credits, JSON.stringify([{beat: 3, query: "edicion", file: "pipeline/broll/.g4-test.mp4"}]));
  const result = spawnSync(process.execPath, [path.join(here, "sync-broll.mjs"), `--beatmap-source=${beatMap}`, `--credits=${credits}`, `--output=${output}`, `--public-dir=${publicDir}`], {cwd: root, encoding: "utf8"});
  assert.equal(result.status, 0, result.stderr);
  assert.ok(fs.existsSync(path.join(publicDir, "broll/beat-03.mp4")));
  assert.match(fs.readFileSync(output, "utf8"), /"source": "stock"/);

  fs.writeFileSync(credits, "[]");
  const missing = spawnSync(process.execPath, [path.join(here, "sync-broll.mjs"), `--beatmap-source=${beatMap}`, `--credits=${credits}`, `--output=${output}`, `--public-dir=${publicDir}`], {cwd: root, encoding: "utf8"});
  assert.notEqual(missing.status, 0);
  assert.match(missing.stderr, /falta un archivo/);
  console.log("B-roll sync tests: 4/4 OK");
} finally {
  fs.rmSync(media, {force: true});
  fs.rmSync(temporary, {recursive: true, force: true});
}
