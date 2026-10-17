import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { colors, radii, spacing, typography } from "../design/tokens";

export type NewsHeadlineLine = {
  text: string;
  highlighted?: boolean;
};

export type NewsTextHighlighterProps = {
  category: string;
  source: string;
  timestamp: string;
  headline: NewsHeadlineLine[];
  summary: string;
  accent?: string;
  renderMode?: "overlay" | "embedded";
  reducedMotion?: boolean;
};

const clamp = {
  extrapolateLeft: "clamp" as const,
  extrapolateRight: "clamp" as const,
};

export const NewsTextHighlighter: React.FC<NewsTextHighlighterProps> = ({
  category,
  source,
  timestamp,
  headline,
  summary,
  accent = colors.primary,
  renderMode = "overlay",
  reducedMotion = false,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const entrance = reducedMotion
    ? interpolate(frame, [0, 10], [0, 1], clamp)
    : spring({
        frame,
        fps,
        durationInFrames: 34,
        config: { damping: 19, mass: 0.78, stiffness: 118 },
      });
  const metaProgress = interpolate(frame, [10, 28], [0, 1], clamp);
  const summaryProgress = interpolate(frame, [112, 132], [0, 1], clamp);
  const sourceProgress = interpolate(frame, [134, 150], [0, 1], clamp);
  const surfaceAlpha = renderMode === "embedded" ? 0.66 : 0.93;

  return (
    <div
      style={{
        position: "relative",
        width: 900,
        minHeight: 680,
        boxSizing: "border-box",
        overflow: "hidden",
        padding: `${spacing.xl}px ${spacing.xl}px ${spacing.lg}px`,
        color: colors.foreground,
        fontFamily: typography.family,
        backgroundColor: `rgba(5, 15, 13, ${surfaceAlpha})`,
        border: `2px solid ${colors.border}`,
        borderRadius: radii.lg,
        boxShadow: "0 38px 110px rgba(0,0,0,0.42), inset 0 1px 0 rgba(255,255,255,0.18)",
        backdropFilter: renderMode === "embedded" ? "blur(30px) saturate(125%)" : "blur(12px)",
        opacity: entrance,
        transform: `translateY(${interpolate(entrance, [0, 1], [72, 0])}px) scale(${interpolate(
          entrance,
          [0, 1],
          [0.975, 1],
        )})`,
      }}
    >
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: `${interpolate(frame, [2, 38], [0, 100], clamp)}%`,
          height: 7,
          backgroundColor: accent,
          boxShadow: `0 0 28px ${accent}`,
        }}
      />

      <div
        style={{
          position: "relative",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          opacity: metaProgress,
          transform: `translateY(${interpolate(metaProgress, [0, 1], [14, 0])}px)`,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: spacing.sm }}>
          <span
            style={{
              width: 14,
              height: 14,
              borderRadius: radii.full,
              backgroundColor: accent,
              boxShadow: `0 0 20px ${accent}`,
            }}
          />
          <span
            style={{
              color: accent,
              fontSize: 22,
              fontWeight: 780,
              letterSpacing: 2.6,
              textTransform: "uppercase",
            }}
          >
            {category}
          </span>
        </div>
        <span style={{ color: colors.mutedForeground, fontSize: 22, fontWeight: 580 }}>{timestamp}</span>
      </div>

      <div style={{ position: "relative", marginTop: spacing.xl, display: "grid", gap: 10 }}>
        {headline.map((line, index) => {
          const lineStart = 30 + index * 18;
          const lineProgress = interpolate(frame, [lineStart, lineStart + 18], [0, 1], clamp);
          const sweep = line.highlighted
            ? interpolate(frame, [lineStart + 7, lineStart + 27], [0, 1], clamp)
            : 0;

          return (
            <div
              key={`${line.text}-${index}`}
              style={{
                position: "relative",
                width: "fit-content",
                maxWidth: "100%",
                isolation: "isolate",
                opacity: lineProgress,
                transform: `translateY(${interpolate(lineProgress, [0, 1], [24, 0])}px)`,
              }}
            >
              {line.highlighted ? (
                <span
                  style={{
                    position: "absolute",
                    zIndex: -1,
                    left: -12,
                    right: -12,
                    top: 7,
                    bottom: 4,
                    borderRadius: 12,
                    backgroundColor: accent,
                    boxShadow: `0 10px 34px rgba(0,0,0,0.16), 0 0 24px ${accent}44`,
                    transform: `scaleX(${sweep})`,
                    transformOrigin: "left center",
                  }}
                />
              ) : null}
              <div
                style={{
                  color: line.highlighted ? colors.primaryForeground : colors.foreground,
                  fontSize: 65,
                  lineHeight: 1.04,
                  fontWeight: 760,
                  letterSpacing: -2.7,
                  padding: line.highlighted ? "4px 0 8px" : "0 0 6px",
                }}
              >
                {line.text}
              </div>
            </div>
          );
        })}
      </div>

      <div
        style={{
          position: "relative",
          marginTop: spacing.xl,
          paddingTop: spacing.lg,
          borderTop: "1px solid rgba(255,255,255,0.16)",
          color: colors.mutedForeground,
          fontSize: 29,
          lineHeight: 1.36,
          fontWeight: 490,
          opacity: summaryProgress,
          transform: `translateY(${interpolate(summaryProgress, [0, 1], [18, 0])}px)`,
        }}
      >
        {summary}
      </div>

      <div
        style={{
          position: "relative",
          display: "flex",
          alignItems: "center",
          gap: spacing.sm,
          marginTop: spacing.lg,
          color: colors.foreground,
          fontSize: 22,
          fontWeight: 690,
          opacity: sourceProgress,
        }}
      >
        <span style={{ width: 32, height: 3, borderRadius: 3, backgroundColor: accent }} />
        {source}
      </div>
    </div>
  );
};
