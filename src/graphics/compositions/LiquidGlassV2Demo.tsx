import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { LiquidGlassCardV2, type LiquidGlassCardV2Props } from "../components/LiquidGlassCardV2";
import { colors, safeArea, spacing, typography } from "../design/tokens";

const V2Stage: React.FC<LiquidGlassCardV2Props> = (props) => (
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
    <LiquidGlassCardV2 {...props} />
  </AbsoluteFill>
);

export const LiquidGlassV2Overlay: React.FC<LiquidGlassCardV2Props> = (props) => (
  <AbsoluteFill style={{ backgroundColor: "transparent" }}>
    <V2Stage {...props} renderMode="overlay" />
  </AbsoluteFill>
);

export const LiquidGlassV2Demo: React.FC<LiquidGlassCardV2Props> = (props) => {
  const frame = useCurrentFrame();
  const drift = interpolate(frame, [0, 180], [0, 110], {
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
          inset: -120,
          transform: `translate3d(${drift * 0.35}px, ${-drift * 0.16}px, 0)`,
          background:
            "radial-gradient(circle at 78% 25%, rgba(98,230,184,0.46), transparent 27%), radial-gradient(circle at 18% 72%, rgba(45,121,102,0.42), transparent 31%), #07110F",
        }}
      />
      <div
        style={{
          position: "absolute",
          top: 330,
          left: -80 + drift,
          width: 1240,
          height: 250,
          opacity: 0.16,
          transform: "rotate(-16deg)",
          background:
            "repeating-linear-gradient(90deg, rgba(255,255,255,0.7) 0 6px, transparent 6px 72px)",
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
        Minthy Motion System · V2
      </div>
      <V2Stage {...props} renderMode="embedded" />
    </AbsoluteFill>
  );
};
