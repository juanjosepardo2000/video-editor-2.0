import type { NormalizedBox } from "./types";

export const DEFAULT_SAFE_BOUNDS: Readonly<{left: number; top: number; right: number; bottom: number}>;
export function normalizeBox(box: NormalizedBox): NormalizedBox;
export function boxesOverlap(left: NormalizedBox, right: NormalizedBox): boolean;
export function faceBoxesForInterval(faceData: {fps: number; frames: readonly {t: number; boxes: readonly NormalizedBox[]}[]}, start: number, end: number): NormalizedBox[];
export function chooseInsetPlacement(input: {faces: readonly NormalizedBox[]; preferredZone?: string; avoid?: readonly NormalizedBox[]; safe?: typeof DEFAULT_SAFE_BOUNDS}): NormalizedBox | null;
export function chooseCaptionPlacement(input: {faces: readonly NormalizedBox[]; anchorY?: number; safe?: typeof DEFAULT_SAFE_BOUNDS}): NormalizedBox | null;
