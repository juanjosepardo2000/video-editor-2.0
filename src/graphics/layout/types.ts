export type NormalizedBox = {x: number; y: number; w: number; h: number};

export type LayoutLayer = {
  beat: number;
  kind: "caption" | "graphic" | "speaker";
  scene: "CAPTIONS" | "CAPTION_UI" | "SPLIT" | "FULLSCREEN";
  startFrame: number;
  endFrame: number;
  box: NormalizedBox;
  textColor: string;
  backgroundColor: string;
  occludesSpeaker: boolean;
  keyframes: readonly {frame: number; box: NormalizedBox}[];
};

export type GeneratedLayout = {
  fps: number;
  width: number;
  height: number;
  profile: string;
  faceSource: string;
  usedFixture: boolean;
  warnings: readonly string[];
  layers: readonly LayoutLayer[];
};
