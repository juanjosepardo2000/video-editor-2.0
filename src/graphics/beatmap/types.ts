export const sceneCodes = ["CAPTIONS", "CAPTION_UI", "SPLIT", "FULLSCREEN"] as const;

export type SceneCode = (typeof sceneCodes)[number];

export type TimedCaptionWord = {
  text: string;
  startFrame: number;
  endFrame: number;
};

export type BeatMapEntry = {
  id: string;
  index: number;
  startSeconds: number;
  endSeconds: number;
  startFrame: number;
  endFrame: number;
  speech: string;
  scene: SceneCode;
  visual: string;
  onScreenText: string;
  transition: string;
  sfx: string;
  caption: string;
  accentKeywords: readonly string[];
  words: readonly TimedCaptionWord[];
};

export type GeneratedBeatMap = {
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
