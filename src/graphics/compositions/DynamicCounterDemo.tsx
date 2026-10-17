import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import {
  DynamicNumberCounter,
  type DynamicNumberCounterProps,
} from "../components/DynamicNumberCounter";
import { colors, safeArea, spacing, typography } from "../design/tokens";

const CounterStage: React.FC<DynamicNumberCounterProps> = (props) => (
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
    <DynamicNumberCounter {...props} />
  </AbsoluteFill>
);

export const DynamicCounterOverlay: React.FC<DynamicNumberCounterProps> = (props) => (
  <AbsoluteFill style={{ backgroundColor: "transparent" }}>
    <CounterStage {...props} renderMode="overlay" />
  </AbsoluteFill>
);

export const DynamicCounterDemo: React.FC<DynamicNumberCounterProps> = (props) => {
  const frame = useCurrentFrame();
  const drift = interpolate(frame, [0, 180], [-45, 80], {
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
          transform: `translate3d(${drift * 0.34}px, ${drift * 0.1}px, 0)`,
          background:
            "radial-gradient(circle at 78% 26%, rgba(98,230,184,0.35), transparent 28%), radial-gradient(circle at 13% 71%, rgba(26,92,77,0.55), transparent 32%), #07110F",
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
        Minthy Motion System · Metrics
      </div>
      <CounterStage {...props} renderMode="embedded" />
    </AbsoluteFill>
  );
};
