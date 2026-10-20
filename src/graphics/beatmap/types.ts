export const sceneCodes = ["CAPTIONS", "CAPTION_UI", "SPLIT", "FULLSCREEN"] as const;
export const zoneCodes = ["arriba", "abajo", "lado", "auto"] as const;
export const brollSources = ["none", "own", "stock", "ai"] as const;
export const visualTags = [
  "contador",
  "comparacion",
  "titular",
  "busqueda",
  "lista",
  "cifra",
  "tarjeta",
  "interludio",
  "recuadro",
  "hablante",
  "broll",
] as const;

export type SceneCode = (typeof sceneCodes)[number];
export type ZoneCode = (typeof zoneCodes)[number];
export type BrollSource = (typeof brollSources)[number];
export type VisualTag = (typeof visualTags)[number];

export type BrollSpec = {
  source: BrollSource;
  value: string;
};

export type TimedCaptionWord = {
  text: string;
  startFrame: number;
  endFrame: number;
};

export type BeatMapEntry = {
  contractVersion: "v1" | "v2";
  id: string;
  index: number;
  startSeconds: number;
  endSeconds: number;
  startFrame: number;
  endFrame: number;
  speech: string;
  scene: SceneCode;
  visual: string;
  visualTag: VisualTag | null;
  onScreenText: string;
  broll: BrollSpec;
  zone: ZoneCode;
  transition: string;
  sfx: string;
  caption: string;
  accentKeywords: readonly string[];
  words: readonly TimedCaptionWord[];
};

export type GeneratedBeatMap = {
  contractVersion: "v1" | "v2";
  fps: number;
  source: "pipeline";
  sourcePath: string;
  transcriptSource: "aligned" | "uniform";
  config: {
    profile: string;
    theme: string;
    accent: string;
    font: string;
    headlineFont: string;
    accentFont: string;
    textColor: string;
    textSecondary: string;
    captionStyle: "word-by-word" | "phrase";
    width: number;
    height: number;
    fps: number;
  };
  warnings: string[];
  durationInFrames: number;
  beats: BeatMapEntry[];
};
