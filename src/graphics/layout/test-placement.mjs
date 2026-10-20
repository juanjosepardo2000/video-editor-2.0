import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { boxesOverlap, chooseCaptionPlacement, chooseInsetPlacement, faceBoxesForInterval } from "./placement.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../../..");
const fixture = JSON.parse(fs.readFileSync(path.join(root, "pipeline/examples/face_boxes.fixture.json"), "utf8"));
const faces = faceBoxesForInterval(fixture, 3.2, 8.3);
const caption = chooseCaptionPlacement({faces, anchorY: 0.65});
const inset = chooseInsetPlacement({faces, preferredZone: "abajo", avoid: caption ? [caption] : []});

assert.ok(faces.length > 0);
assert.ok(caption);
assert.ok(inset);
assert.ok(faces.every((face) => !boxesOverlap(caption, face)));
assert.ok(faces.every((face) => !boxesOverlap(inset, face)));
assert.equal(chooseInsetPlacement({faces: [{x: 0, y: 0, w: 1, h: 1}]}), null);

console.log("Adaptive placement tests: 6/6 OK");
