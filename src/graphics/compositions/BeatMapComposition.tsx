import React from "react";
import { AbsoluteFill, interpolate, Sequence, useCurrentFrame } from "remotion";
import { LiquidGlassCardV2 } from "../components/LiquidGlassCardV2";
import { WordByWordCaptions } from "../components/WordByWordCaptions";
import { generatedBeatMap } from "../beatmap/generated-beatmap";
import type { BeatMapEntry } from "../beatmap/types";
import { colors, safeArea, typography } from "../design/tokens";
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
  const keywordWordCount = beat.accentKeywords.flatMap((keyword) => keyword.split(/\s+/)).filter(Boolean).length;
  const accentWordCount = Math.min(3, Math.max(1, keywordWordCount)) as 1 | 2 | 3;
  return (
    <WordByWordCaptions
      text={beat.speech}
      words={beat.words}
      accentKeywords={beat.accentKeywords}
      durationInFrames={duration}
      accentWordCount={accentWordCount}
      wordsPerPage={5}
      accent={beatMapAccent}
      theme={beatMapTheme}
      captionStyle={generatedBeatMap.config.captionStyle}
      primaryFontFamily={primaryFontFamily}
      accentFontFamily={accentFontFamily}
    />
  );
};

const FullscreenGraphic: React.FC<{ beat: BeatMapEntry; duration: number }> = ({ beat, duration }) => {
  if (!beat.onScreenText.trim()) return null;
  return (
    <LiquidGlassCardV2
      title={beat.onScreenText}
      accent={beatMapAccent}
      renderMode="overlay"
      contrast={beatMapTheme}
      reducedMotion={duration < 100}
    />
  );
};

const BeatLayer: React.FC<{ beat: BeatMapEntry }> = ({ beat }) => {
  const frame = useCurrentFrame();
  const duration = beat.endFrame - beat.startFrame;
  const style = transitionStyle(beat.transition, frame, duration);

  return (
    <AbsoluteFill style={{ ...style, fontFamily: primaryFontFamily }}>
      {beat.scene === "CAPTIONS" ? <CaptionLayer beat={beat} duration={duration} /> : null}

      {beat.scene === "CAPTION_UI" ? (
        <>
          {beat.onScreenText.trim() ? <div
            style={{
              position: "absolute",
              left: safeArea.left + 30,
              bottom: safeArea.bottom + 150,
            }}
          >
            <LiquidGlassCardV2
              title={beat.onScreenText}
              accent={beatMapAccent}
              renderMode="overlay"
              contrast={beatMapTheme}
              reducedMotion={duration < 100}
              size="compact"
            />
          </div> : null}
          <CaptionLayer beat={beat} duration={duration} />
        </>
      ) : null}

      {beat.scene === "SPLIT" ? (
        <>
          {beat.onScreenText.trim() ? <div
            style={{
              position: "absolute",
              top: 360,
              right: safeArea.right,
              width: 430,
              minHeight: 640,
              padding: 36,
              boxSizing: "border-box",
              color: colors.foreground,
              backgroundColor: "rgba(5,15,13,0.9)",
              border: `2px solid ${colors.border}`,
              borderRadius: 32,
              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
            }}
          >
            <div style={{ color: colors.primary, fontSize: 22, fontWeight: 700, letterSpacing: 2.2, textTransform: "uppercase" }}>
              {""}
            </div>
            <div style={{ marginTop: 24, fontFamily: headlineFontFamily, fontSize: 46, lineHeight: 1.08, fontWeight: 700, letterSpacing: -1.6 }}>
              {beat.onScreenText}
            </div>
          </div> : null}
          <CaptionLayer beat={beat} duration={duration} />
        </>
      ) : null}

      {beat.scene === "FULLSCREEN" ? (
        <AbsoluteFill
          style={{
            paddingTop: safeArea.top,
            paddingRight: safeArea.right,
            paddingBottom: safeArea.bottom,
            paddingLeft: safeArea.left,
            boxSizing: "border-box",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <FullscreenGraphic beat={beat} duration={duration} />
        </AbsoluteFill>
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
