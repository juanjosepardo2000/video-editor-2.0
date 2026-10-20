import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chooseCaptionPlacement, chooseInsetPlacement, faceBoxesForInterval, normalizeBox } from "./placement.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../../..");
const argument = (name) => process.argv.find((item) => item.startsWith(`--${name}=`))?.slice(name.length + 3);
const localFaces = path.join(root, "pipeline/face_boxes.json");
const fixtureFaces = path.join(root, "pipeline/examples/face_boxes.fixture.json");
const facePath = path.resolve(root, argument("faces") ?? (fs.existsSync(localFaces) ? localFaces : fixtureFaces));
const beatMapPath = path.join(root, "src/graphics/beatmap/generated-beatmap.ts");
const outputPath = path.resolve(root, argument("output") ?? "src/graphics/layout/generated-layout.ts");
const reportPath = path.resolve(root, argument("report") ?? "pipeline/layout.json");

const readGeneratedBeatMap = () => {
  const source = fs.readFileSync(beatMapPath, "utf8");
  const match = source.match(/export const generatedBeatMap = ([\s\S]+) as const satisfies/);
  if (!match) throw new Error("No se pudo leer generated-beatmap.ts; ejecuta sync:beatmap primero.");
  return JSON.parse(match[1]);
};

const readFaces = () => {
  const data = JSON.parse(fs.readFileSync(facePath, "utf8"));
  if (!(Number(data.fps) > 0) || !(Number(data.width) > 0) || !(Number(data.height) > 0) || !Array.isArray(data.frames)) {
    throw new Error("face_boxes.json debe definir fps, width, height y frames.");
  }
  let previous = -1;
  for (const [frameIndex, frame] of data.frames.entries()) {
    if (!Number.isFinite(frame.t) || frame.t < previous || !Array.isArray(frame.boxes)) throw new Error(`face_boxes.json: frame ${frameIndex + 1} inválido.`);
    previous = frame.t;
    for (const [boxIndex, box] of frame.boxes.entries()) {
      if (![box.x, box.y, box.w, box.h, box.conf].every(Number.isFinite) || box.x < 0 || box.y < 0 || box.w <= 0 || box.h <= 0 || box.x + box.w > 1 || box.y + box.h > 1) {
        throw new Error(`face_boxes.json: caja ${boxIndex + 1} del frame ${frameIndex + 1} fuera de 0..1.`);
      }
    }
  }
  return data;
};

const beatMap = readGeneratedBeatMap();
const faces = readFaces();
const layers = [];
const warnings = [];
const add = (beat, kind, box, options = {}) => {
  if (!box) return;
  layers.push({
    beat: beat.index,
    kind,
    scene: beat.scene,
    startFrame: beat.startFrame,
    endFrame: beat.endFrame,
    box: normalizeBox(box),
    textColor: beatMap.config.textColor,
    backgroundColor: options.backgroundColor ?? "transparent",
    occludesSpeaker: options.occludesSpeaker ?? false,
    keyframes: [],
  });
};

for (const beat of beatMap.beats) {
  const beatFaces = faceBoxesForInterval(faces, beat.startSeconds, beat.endSeconds);
  const captionBox = beat.scene === "FULLSCREEN" ? null : chooseCaptionPlacement({faces: beatFaces, anchorY: beatMap.config.captionAnchorY});
  if (beat.scene !== "FULLSCREEN" && !captionBox) warnings.push(`Beat ${beat.index}: no hay una zona sin rostro para subtítulos.`);

  if (beat.scene === "CAPTIONS") add(beat, "caption", captionBox);
  if (beat.scene === "CAPTION_UI") {
    const graphicBox = beat.onScreenText
      ? chooseInsetPlacement({faces: beatFaces, preferredZone: beat.zone, avoid: captionBox ? [captionBox] : []})
      : null;
    if (beat.onScreenText && !graphicBox) warnings.push(`Beat ${beat.index}: se ocultó el gráfico porque ninguna zona evita el rostro.`);
    add(beat, "graphic", graphicBox, {backgroundColor: beatMap.config.theme.includes("light") ? "#F5FCF9" : "#07110F"});
    add(beat, "caption", captionBox);
  }
  if (beat.scene === "SPLIT") {
    add(beat, "graphic", {x: 0, y: 0, w: 1, h: 0.5}, {backgroundColor: beatMap.config.theme.includes("light") ? "#F5FCF9" : "#07110F", occludesSpeaker: true});
    add(beat, "speaker", {x: 0, y: 0.5, w: 1, h: 0.5});
    add(beat, "caption", captionBox);
  }
  if (beat.scene === "FULLSCREEN") {
    add(beat, "graphic", {x: 0, y: 0, w: 1, h: 1}, {backgroundColor: beatMap.config.theme.includes("light") ? "#F5FCF9" : "#07110F", occludesSpeaker: true});
  }
}

const payload = {
  fps: beatMap.fps,
  width: beatMap.config.width,
  height: beatMap.config.height,
  profile: beatMap.config.profile,
  faceSource: path.relative(root, facePath).replaceAll("\\", "/"),
  usedFixture: facePath === fixtureFaces,
  warnings,
  layers,
};
fs.mkdirSync(path.dirname(outputPath), {recursive: true});
fs.writeFileSync(outputPath, `import type { GeneratedLayout } from "./types";\n\nexport const generatedLayout = ${JSON.stringify(payload, null, 2)} as const satisfies GeneratedLayout;\n`, "utf8");
fs.mkdirSync(path.dirname(reportPath), {recursive: true});
fs.writeFileSync(reportPath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
console.log(`Layout sincronizado: ${layers.length} capas; rostro ${payload.faceSource}${payload.usedFixture ? " (fixture)" : ""}.`);
for (const warning of warnings) console.warn(`Aviso: ${warning}`);
