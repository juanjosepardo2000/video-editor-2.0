export type GeneratedBrollAsset = {
  beat: number;
  source: "own" | "stock" | "ai";
  value: string;
  publicFile: string;
};

export type GeneratedBrollManifest = {
  assets: readonly GeneratedBrollAsset[];
};
