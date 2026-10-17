import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import {
  NewsTextHighlighter,
  type NewsTextHighlighterProps,
} from "../components/NewsTextHighlighter";
import { colors, safeArea, spacing, typography } from "../design/tokens";

const NewsStage: React.FC<NewsTextHighlighterProps> = (props) => (
  <AbsoluteFill
    style={{
      paddingTop: safeArea.top,
      paddingRight: safeArea.right,
      paddingBottom: safeArea.bottom,
      paddingLeft: safeArea.left,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      boxSizing: "border-box",
    }}
  >
    <NewsTextHighlighter {...props} />
  </AbsoluteFill>
);

export const NewsHighlighterOverlay: React.FC<NewsTextHighlighterProps> = (props) => (
  <AbsoluteFill style={{ backgroundColor: "transparent" }}>
    <NewsStage {...props} renderMode="overlay" />
  </AbsoluteFill>
);

export const NewsHighlighterDemo: React.FC<NewsTextHighlighterProps> = (props) => {
  const frame = useCurrentFrame();
  const drift = interpolate(frame, [0, 180], [-30, 75], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        overflow: "hidden",
        backgroundColor: colors.background,
        color: colors.foreground,
        fontFamily: typography.family,
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: -140,
          transform: `translate3d(${drift * 0.28}px, ${drift * 0.12}px, 0)`,
          background:
            "linear-gradient(145deg, rgba(7,17,15,0.2), rgba(7,17,15,0.94)), radial-gradient(circle at 78% 22%, rgba(98,230,184,0.34), transparent 27%), radial-gradient(circle at 16% 74%, rgba(28,86,76,0.55), transparent 34%), #07110F",
        }}
      />
      <div
        style={{
          position: "absolute",
          top: safeArea.top,
          left: safeArea.left,
          display: "flex",
          alignItems: "center",
          gap: spacing.sm,
          fontSize: 22,
          fontWeight: 650,
          letterSpacing: 2.4,
          textTransform: "uppercase",
        }}
      >
        <span style={{ width: 38, height: 4, borderRadius: 4, backgroundColor: colors.primary }} />
        Minthy Motion System · News
      </div>
      <NewsStage {...props} renderMode="embedded" />
    </AbsoluteFill>
  );
};
