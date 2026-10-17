import React from "react";
import { AbsoluteFill, interpolate, Sequence, useCurrentFrame } from "remotion";
import { AnimatedSearchBar } from "../components/AnimatedSearchBar";
import { DynamicNumberCounter } from "../components/DynamicNumberCounter";
import { LiquidGlassCardV2 } from "../components/LiquidGlassCardV2";
import { NewsTextHighlighter } from "../components/NewsTextHighlighter";
import { WordByWordCaptions } from "../components/WordByWordCaptions";
import { generatedBeatMap } from "../beatmap/generated-beatmap";
import type { BeatMapEntry } from "../beatmap/types";
import { colors, safeArea, typography } from "../design/tokens";

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

const splitHeadline = (text: string) => {
  const words = text.trim().split(/\s+/).filter(Boolean);
  const chunkSize = Math.max(1, Math.ceil(words.length / 3));
  const chunks = [];
  for (let index = 0; index < words.length; index += chunkSize) {
    chunks.push({ text: words.slice(index, index + chunkSize).join(" "), highlighted: chunks.length === 1 });
  }
  return chunks.slice(0, 3);
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
    />
  );
};

const FullscreenGraphic: React.FC<{ beat: BeatMapEntry; duration: number }> = ({ beat, duration }) => {
  const hint = `${beat.visual} ${beat.speech}`.toLowerCase();
  const reducedMotion = duration < 100;
  if (hint.includes("busca") || hint.includes("search")) {
    return (
      <AnimatedSearchBar
        label="Búsqueda asistida"
        mistypedQuery="edicion con ia"
        correctedQuery="edición con IA"
        resultLabel="Resultado recomendado"
        suggestions={["Cortes", "Gráficos", "CapCut"]}
        accent={beatMapAccent}
        renderMode="overlay"
        reducedMotion={reducedMotion}
      />
    );
  }
  if (hint.includes("contador") || hint.includes("número") || hint.includes("numero") || hint.includes("metric")) {
    const parsedValue = Number.parseFloat(hint.match(/\d+(?:[.,]\d+)?/)?.[0].replace(",", ".") ?? "38");
    return (
      <DynamicNumberCounter
        label="Dato destacado"
        startValue={0}
        endValue={parsedValue}
        suffix="%"
        trendLabel="Evolución positiva"
        supportingText={beat.speech || beat.visual}
        accent={beatMapAccent}
        renderMode="overlay"
        reducedMotion={reducedMotion}
      />
    );
  }
  if (hint.includes("noticia") || hint.includes("news") || hint.includes("resalt")) {
    return (
      <NewsTextHighlighter
        category="Actualidad"
        source="Minthy BeatMap"
        timestamp="Ahora"
        headline={splitHeadline(beat.speech || beat.caption || beat.visual)}
        summary={beat.visual}
        accent={beatMapAccent}
        renderMode="overlay"
        reducedMotion={reducedMotion}
      />
    );
  }
  return (
    <LiquidGlassCardV2
      eyebrow="Beat destacado"
      title={beat.speech || beat.caption || "Momento clave"}
      description={beat.visual || "Gráfico generado desde el BeatMap."}
      metric={String(beat.index).padStart(2, "0")}
      metricLabel="escena del montaje"
      actionLabel="En pantalla"
      accent={beatMapAccent}
      renderMode="overlay"
      contrast={beatMapTheme}
      reducedMotion={reducedMotion}
    />
  );
};

const BeatLayer: React.FC<{ beat: BeatMapEntry }> = ({ beat }) => {
  const frame = useCurrentFrame();
  const duration = beat.endFrame - beat.startFrame;
  const style = transitionStyle(beat.transition, frame, duration);

  return (
    <AbsoluteFill style={{ ...style, fontFamily: typography.family }}>
      {beat.scene === "CAPTIONS" ? <CaptionLayer beat={beat} duration={duration} /> : null}

      {beat.scene === "CAPTION_UI" ? (
        <>
          <div
            style={{
              position: "absolute",
              top: safeArea.top + 70,
              left: safeArea.left + 10,
              transform: "scale(0.72)",
              transformOrigin: "top left",
            }}
          >
            <LiquidGlassCardV2
              eyebrow="Contexto"
              title={beat.visual || beat.speech || "Información clave"}
              description={beat.speech || beat.caption}
              metric={String(beat.index).padStart(2, "0")}
              metricLabel="beat activo"
              actionLabel="Ver"
              accent={beatMapAccent}
              renderMode="overlay"
              contrast={beatMapTheme}
              reducedMotion={duration < 100}
            />
          </div>
          <CaptionLayer beat={beat} duration={duration} />
        </>
      ) : null}

      {beat.scene === "SPLIT" ? (
        <>
          <div
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
              Vista complementaria
            </div>
            <div style={{ marginTop: 24, fontSize: 46, lineHeight: 1.08, fontWeight: 700, letterSpacing: -1.6 }}>
              {beat.visual || "Contenido dividido"}
            </div>
          </div>
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
