import React from "react";
import { Composition } from "remotion";
import { LiquidGlassDemo, LiquidGlassOverlay } from "./compositions/LiquidGlassDemo";
import { LiquidGlassV2Demo, LiquidGlassV2Overlay } from "./compositions/LiquidGlassV2Demo";
import { AnimatedSearchDemo, AnimatedSearchOverlay } from "./compositions/AnimatedSearchDemo";
import { NewsHighlighterDemo, NewsHighlighterOverlay } from "./compositions/NewsHighlighterDemo";
import { DynamicCounterDemo, DynamicCounterOverlay } from "./compositions/DynamicCounterDemo";
import { BeatMapComposition, BeatMapComposition4K } from "./compositions/BeatMapComposition";
import { CompositeReview } from "./compositions/CompositeReview";
import { G3ComponentGallery } from "./compositions/G3ComponentGallery";
import { generatedBeatMap } from "./beatmap/generated-beatmap";
import {
  animatedSearchDemo,
  liquidGlassDemo,
  liquidGlassV2Demo,
  newsHighlighterDemo,
  dynamicCounterDemo,
} from "./data/demo";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="G3ComponentGallery"
        component={G3ComponentGallery}
        durationInFrames={420}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="BeatMapOverlay"
        component={BeatMapComposition}
        durationInFrames={generatedBeatMap.durationInFrames}
        fps={generatedBeatMap.fps}
        width={generatedBeatMap.config.width}
        height={generatedBeatMap.config.height}
      />
      <Composition
        id="BeatMapOverlay4K"
        component={BeatMapComposition4K}
        durationInFrames={generatedBeatMap.durationInFrames}
        fps={generatedBeatMap.fps}
        width={generatedBeatMap.config.width * 2}
        height={generatedBeatMap.config.height * 2}
      />
      <Composition
        id="CompositeReview"
        component={CompositeReview}
        durationInFrames={generatedBeatMap.durationInFrames}
        fps={generatedBeatMap.fps}
        width={540}
        height={960}
        defaultProps={{ speakerFile: "speaker.mp4", overlayFile: "overlay.mov" }}
      />
      <Composition
        id="MainComposition"
        component={LiquidGlassDemo}
        durationInFrames={300}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={liquidGlassDemo}
      />
      <Composition
        id="LiquidGlassOverlay"
        component={LiquidGlassOverlay}
        durationInFrames={300}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={liquidGlassDemo}
      />
      <Composition
        id="LiquidGlassV2Demo"
        component={LiquidGlassV2Demo}
        durationInFrames={180}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={liquidGlassV2Demo}
      />
      <Composition
        id="LiquidGlassV2Overlay"
        component={LiquidGlassV2Overlay}
        durationInFrames={180}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          ...liquidGlassV2Demo,
          renderMode: "overlay" as const,
        }}
      />
      <Composition
        id="AnimatedSearchDemo"
        component={AnimatedSearchDemo}
        durationInFrames={180}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={animatedSearchDemo}
      />
      <Composition
        id="AnimatedSearchOverlay"
        component={AnimatedSearchOverlay}
        durationInFrames={180}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          ...animatedSearchDemo,
          renderMode: "overlay" as const,
        }}
      />
      <Composition
        id="NewsHighlighterDemo"
        component={NewsHighlighterDemo}
        durationInFrames={180}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={newsHighlighterDemo}
      />
      <Composition
        id="NewsHighlighterOverlay"
        component={NewsHighlighterOverlay}
        durationInFrames={180}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          ...newsHighlighterDemo,
          renderMode: "overlay" as const,
        }}
      />
      <Composition
        id="DynamicCounterDemo"
        component={DynamicCounterDemo}
        durationInFrames={180}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={dynamicCounterDemo}
      />
      <Composition
        id="DynamicCounterOverlay"
        component={DynamicCounterOverlay}
        durationInFrames={180}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          ...dynamicCounterDemo,
          renderMode: "overlay" as const,
        }}
      />
    </>
  );
};
