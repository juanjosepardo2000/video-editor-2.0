export const DEFAULT_SAFE_BOUNDS = Object.freeze({left: 60 / 1080, top: 150 / 1920, right: 1 - 120 / 1080, bottom: 1 - 380 / 1920});

const clamp = (value, minimum, maximum) => Math.min(maximum, Math.max(minimum, value));
const round = (value) => Number(value.toFixed(4));
export const normalizeBox = (box) => ({x: round(box.x), y: round(box.y), w: round(box.w), h: round(box.h)});

export const boxesOverlap = (left, right) =>
  left.x < right.x + right.w && left.x + left.w > right.x && left.y < right.y + right.h && left.y + left.h > right.y;

export const faceBoxesForInterval = (faceData, start, end) => {
  const margin = 1 / Math.max(Number(faceData.fps) || 10, 1);
  let frames = faceData.frames.filter((frame) => frame.t >= start - margin && frame.t <= end + margin);
  if (frames.length === 0 && faceData.frames.length > 0) {
    const middle = (start + end) / 2;
    frames = [[...faceData.frames].sort((a, b) => Math.abs(a.t - middle) - Math.abs(b.t - middle))[0]];
  }
  return frames.flatMap((frame) => frame.boxes ?? []).map(normalizeBox);
};

const distance = (left, right) => {
  const horizontal = Math.max(left.x - (right.x + right.w), right.x - (left.x + left.w), 0);
  const vertical = Math.max(left.y - (right.y + right.h), right.y - (left.y + left.h), 0);
  return Math.hypot(horizontal, vertical);
};

const candidatesFor = (width, height, safe) => {
  const centeredX = safe.left + ((safe.right - safe.left) - width) / 2;
  const centeredY = safe.top + ((safe.bottom - safe.top) - height) / 2;
  return [
    {zone: "arriba", box: {x: centeredX, y: safe.top + 0.018, w: width, h: height}},
    {zone: "abajo", box: {x: centeredX, y: safe.bottom - height, w: width, h: height}},
    {zone: "lado", box: {x: safe.left + 0.01, y: centeredY, w: width, h: height}},
    {zone: "lado", box: {x: safe.right - width - 0.01, y: centeredY, w: width, h: height}},
  ].map((candidate) => ({...candidate, box: normalizeBox(candidate.box)}));
};

export const chooseInsetPlacement = ({faces, preferredZone = "auto", avoid = [], safe = DEFAULT_SAFE_BOUNDS}) => {
  for (const scale of [1, 0.86, 0.72, 0.55]) {
    const width = 0.7 * scale;
    const height = 0.17 * scale;
    const candidates = candidatesFor(width, height, safe)
      .filter(({box}) => !faces.some((face) => boxesOverlap(box, face)) && !avoid.some((item) => boxesOverlap(box, item)))
      .map((candidate) => ({
        ...candidate,
        preferred: preferredZone !== "auto" && candidate.zone === preferredZone ? 1 : 0,
        clearance: faces.length === 0 ? 1 : Math.min(...faces.map((face) => distance(candidate.box, face))),
      }))
      .sort((left, right) => right.preferred - left.preferred || right.clearance - left.clearance);
    if (candidates.length > 0) return candidates[0].box;
  }
  return null;
};

export const chooseCaptionPlacement = ({faces, anchorY = 0.65, safe = DEFAULT_SAFE_BOUNDS}) => {
  const width = Math.min(0.78, safe.right - safe.left);
  const height = 0.1;
  const x = safe.left + ((safe.right - safe.left) - width) / 2;
  const ys = [anchorY - height / 2, safe.bottom - height - 0.01, safe.top + 0.02, 0.54, 0.7]
    .map((value) => clamp(value, safe.top, safe.bottom - height));
  const candidates = [...new Set(ys.map(round))].map((y) => normalizeBox({x, y, w: width, h: height}));
  return candidates.find((box) => !faces.some((face) => boxesOverlap(box, face))) ?? null;
};
