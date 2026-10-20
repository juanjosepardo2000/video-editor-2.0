import React from "react";
import { AbsoluteFill, interpolate, Sequence, useCurrentFrame } from "remotion";
import { BeatGraphic, graphicCanvasSize } from "../components/BeatGraphic";
import { WordByWordCaptions } from "../components/WordByWordCaptions";
import { BrollScene } from "../components/BrollScene";
import { generatedBeatMap } from "../beatmap/generated-beatmap";
import { generatedLayout } from "../layout/generated-layout";
import { generatedBroll } from "../broll/generated-broll";
import type { GeneratedBrollAsset } from "../broll/types";
import type { BeatMapEntry } from "../beatmap/types";
import type { LayoutLayer, NormalizedBox } from "../layout/types";
import { colors } from "../design/tokens";
import { resolveProfileFont } from "../design/fonts";

const clamp = {
  extrapolateLeft: "clamp" as const,
  extrapolateRight: "clamp" as const,
};

const accentByName: Record<string, string> = {
  orange: "#D98255",
  naranja: "#D98255",
  green: colors.primary,
  verde: colors.primary,
  blue: "#6E95B8",
  azul: "#6E95B8",
};

const beatMapAccent = accentByName[generatedBeatMap.config.accent.toLowerCase()] ?? generatedBeatMap.config.accent;
const beatMapTheme = generatedBeatMap.config.theme.toLowerCase().includes("light") ? "light" : "dark";
const primaryFontFamily = resolveProfileFont(generatedBeatMap.config.font);
const headlineFontFamily = resolveProfileFont(generatedBeatMap.config.headlineFont);
const accentFontFamily = resolveProfileFont(generatedBeatMap.config.accentFont);
const brollAssets = generatedBroll.assets as readonly GeneratedBrollAsset[];
const brollFor = (beat: BeatMapEntry) => brollAssets.find((asset) => asset.beat === beat.index);

const layerFor = (beat: BeatMapEntry, kind: LayoutLayer["kind"]): LayoutLayer | undefined =>
  generatedLayout.layers.find((layer) => layer.beat === beat.index && layer.kind === kind);

const boxStyle = (box: NormalizedBox): React.CSSProperties => ({
  position: "absolute",
  left: `${box.x * 100}%`,
  top: `${box.y * 100}%`,
  width: `${box.w * 100}%`,
  height: `${box.h * 100}%`,
  boxSizing: "border-box",
});

const GraphicInBox: React.FC<{beat: BeatMapEntry; box: NormalizedBox; duration: number; compact?: boolean}> = ({beat, box, duration, compact = false}) => {
  if (!beat.onScreenText.trim()) return null;
  const canvas = graphicCanvasSize(beat.visualTag);
  const targetWidth = box.w * generatedBeatMap.config.width;
  const targetHeight = box.h * generatedBeatMap.config.height;
  const scale = Math.min(targetWidth / canvas.width, targetHeight / canvas.height);
  return <div style={{...boxStyle(box), display: "flex", alignItems: "center", justifyContent: "center", overflow: "visible"}}>
    <div style={{width: canvas.width, height: canvas.height, display: "flex", alignItems: "center", justifyContent: "center", transform: `scale(${scale})`, flex: "0 0 auto"}}>
      <BeatGraphic tag={beat.visualTag} text={beat.onScreenText} accent={beatMapAccent} theme={beatMapTheme} fontFamily={headlineFontFamily} accentFontFamily={accentFontFamily} reducedMotion={duration < 100} compact={compact} />
    </div>
  </div>;
};

const transitionStyle = (transition: string, frame: number, duration: number): React.CSSProperties => {
  const normalized = transition.toLowerCase();
  if (normalized === "cut") return { opacity: 1 };
  const intro = interpolate(frame, [0, 8], [0, 1], clamp);
  const outro = interpolate(frame, [Math.max(duration - 8, 8), duration - 2], [1, 0], clamp);
  const opacity = Math.min(intro, outro);
  if (normalized.includes("zoom")) {
    return { opacity, transform: `scale(${interpolate(intro, [0, 1], [0.94, 1])})` };
  }
  if (normalized === "slide-up") {
    return { opacity, transform: `translateY(${interpolate(intro, [0, 1], [48, 0])}px)` };
  }
  return { opacity };
};

const CaptionLayer: React.FC<{ beat: BeatMapEntry; duration: number }> = ({ beat, duration }) => {
  const layer = layerFor(beat, "caption");
  if (!layer) return null;
  const keywordWordCount = beat.accentKeywords.flatMap((keyword) => keyword.split(/\s+/)).filter(Boolean).length;
  const accentWordCount = Math.min(3, Math.max(1, keywordWordCount)) as 1 | 2 | 3;
  const wordsPerPage = Math.min(6, Math.max(1, generatedBeatMap.config.captionWordsPerGroup[1])) as 1 | 2 | 3 | 4 | 5 | 6;
  return (
    <WordByWordCaptions
      text={beat.speech}
      words={beat.words}
      accentKeywords={beat.accentKeywords}
      durationInFrames={duration}
      accentWordCount={accentWordCount}
      wordsPerPage={wordsPerPage}
      accent={beatMapAccent}
      theme={beatMapTheme}
      captionStyle={generatedBeatMap.config.captionStyle}
      primaryFontFamily={primaryFontFamily}
      accentFontFamily={accentFontFamily}
      box={layer.box}
      fontScale={generatedBeatMap.config.captionFontScale}
    />
  );
};

const FullscreenGraphic: React.FC<{ beat: BeatMapEntry; duration: number; contentStyle: React.CSSProperties }> = ({ beat, duration, contentStyle }) => {
  const layer = layerFor(beat, "graphic");
  if (!layer) return null;
  const broll = brollFor(beat);
  if (beat.broll.source !== "none" && broll) {
    return <AbsoluteFill style={{...contentStyle}}>
      <BrollScene publicFile={broll.publicFile} text={beat.onScreenText} accent={beatMapAccent} textColor="#F7FCFA" fontFamily={headlineFontFamily} />
    </AbsoluteFill>;
  }
  return (
    <AbsoluteFill
      style={{
        backgroundColor: layer.backgroundColor,
        color: generatedBeatMap.config.textColor,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "160px 96px",
        boxSizing: "border-box",
      }}
    >
      {beat.onScreenText.trim() ? <div style={{...contentStyle, width: 900, height: 700, display: "flex", alignItems: "center", justifyContent: "center"}}>
        <BeatGraphic tag={beat.visualTag} text={beat.onScreenText} accent={beatMapAccent} theme={beatMapTheme} fontFamily={headlineFontFamily} accentFontFamily={accentFontFamily} reducedMotion={duration < 100} />
      </div> : null}
    </AbsoluteFill>
  );
};

const BeatLayer: React.FC<{ beat: BeatMapEntry }> = ({ beat }) => {
  const frame = useCurrentFrame();
  const duration = beat.endFrame - beat.startFrame;
  const style = transitionStyle(beat.transition, frame, duration);

  if (beat.scene === "FULLSCREEN") {
    return (
      <AbsoluteFill style={{fontFamily: primaryFontFamily}}>
        <FullscreenGraphic beat={beat} duration={duration} contentStyle={style} />
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill style={{ ...style, fontFamily: primaryFontFamily }}>
      {beat.scene === "CAPTIONS" ? <CaptionLayer beat={beat} duration={duration} /> : null}

      {beat.scene === "CAPTION_UI" ? (
        <>
          {(() => {
            const graphicLayer = layerFor(beat, "graphic");
            if (!graphicLayer || !beat.onScreenText.trim()) return null;
            return <GraphicInBox beat={beat} box={graphicLayer.box} duration={duration} compact />;
          })()}
          <CaptionLayer beat={beat} duration={duration} />
        </>
      ) : null}

      {beat.scene === "SPLIT" ? (
        <>
          {(() => {
            const graphicLayer = layerFor(beat, "graphic");
            if (!graphicLayer) return null;
            const broll = brollFor(beat);
            if (beat.broll.source !== "none" && broll) return <div style={{...boxStyle(graphicLayer.box), overflow: "hidden"}}>
              <BrollScene publicFile={broll.publicFile} text={beat.onScreenText} accent={beatMapAccent} textColor="#F7FCFA" fontFamily={headlineFontFamily} />
            </div>;
            return <div style={{...boxStyle(graphicLayer.box), backgroundColor: graphicLayer.backgroundColor}}>
              <GraphicInBox beat={beat} box={{x: 0, y: 0, w: 1, h: 1}} duration={duration} />
            </div>;
          })()}
          <CaptionLayer beat={beat} duration={duration} />
        </>
      ) : null}
    </AbsoluteFill>
  );
};

export const BeatMapComposition: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: "transparent" }}>
    {generatedBeatMap.beats.map((beat) => (
      <Sequence
        key={beat.id}
        name={`${beat.index}. ${beat.scene} — ${beat.visual}`}
        from={beat.startFrame}
        durationInFrames={beat.endFrame - beat.startFrame}
      >
        <BeatLayer beat={beat} />
      </Sequence>
    ))}
  </AbsoluteFill>
);

/**
 * Conserva el sistema de diseño de 1080x1920 y lo escala de forma exacta a
 * 2160x3840. Así la versión 4K mantiene proporciones, zonas seguras y tamaños
 * relativos sin duplicar valores de píxeles en cada componente.
 */
export const BeatMapComposition4K: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: "transparent", overflow: "hidden" }}>
    <div
      style={{
        position: "absolute",
        width: generatedBeatMap.config.width,
        height: generatedBeatMap.config.height,
        left: 0,
        top: 0,
        transform: "scale(2)",
        transformOrigin: "top left",
      }}
    >
      <BeatMapComposition />
    </div>
  </AbsoluteFill>
);
