import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import {fileURLToPath} from "node:url";
import {boxesOverlap, faceBoxesForInterval} from "./placement.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../../..");
const readGenerated = (file, marker) => {
  const source = fs.readFileSync(file, "utf8");
  const match = source.match(new RegExp(`${marker} = ([\\s\\S]+) as const satisfies`));
  if (!match) throw new Error(`No se pudo leer ${path.basename(file)}.`);
  return JSON.parse(match[1]);
};

const layout = readGenerated(path.join(here, "generated-layout.ts"), "generatedLayout");
const beatMap = readGenerated(path.join(root, "src/graphics/beatmap/generated-beatmap.ts"), "generatedBeatMap");
const faces = JSON.parse(fs.readFileSync(path.resolve(root, layout.faceSource), "utf8"));

assert.equal(layout.width, beatMap.config.width);
assert.equal(layout.height, beatMap.config.height);
assert.equal(layout.fps, beatMap.fps);

for (const layer of layout.layers.filter((item) => item.kind !== "speaker" && !item.occludesSpeaker)) {
  const beat = beatMap.beats.find((item) => item.index === layer.beat);
  assert.ok(beat, `La capa referencia un beat inexistente: ${layer.beat}.`);
  const beatFaces = faceBoxesForInterval(faces, beat.startSeconds, beat.endSeconds);
  assert.ok(
    beatFaces.every((face) => !boxesOverlap(layer.box, face)),
    `La capa ${layer.kind} del beat ${layer.beat} invade el rostro.`,
  );
}

const fullscreen = layout.layers.find((layer) => layer.scene === "FULLSCREEN" && layer.kind === "graphic");
assert.deepEqual(fullscreen?.box, {x: 0, y: 0, w: 1, h: 1});
assert.equal(fullscreen?.occludesSpeaker, true);
assert.notEqual(fullscreen?.backgroundColor, "transparent");

const splitGraphic = layout.layers.find((layer) => layer.scene === "SPLIT" && layer.kind === "graphic");
const splitSpeaker = layout.layers.find((layer) => layer.scene === "SPLIT" && layer.kind === "speaker");
assert.deepEqual(splitGraphic?.box, {x: 0, y: 0, w: 1, h: 0.5});
assert.deepEqual(splitSpeaker?.box, {x: 0, y: 0.5, w: 1, h: 0.5});

console.log("Generated layout contract tests: OK");
