import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { AnimatedSearchBar, type AnimatedSearchBarProps } from "../components/AnimatedSearchBar";
import { colors, safeArea, spacing, typography } from "../design/tokens";

const SearchStage: React.FC<AnimatedSearchBarProps> = (props) => (
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
    <AnimatedSearchBar {...props} />
  </AbsoluteFill>
);

export const AnimatedSearchOverlay: React.FC<AnimatedSearchBarProps> = (props) => (
  <AbsoluteFill style={{ backgroundColor: "transparent" }}>
    <SearchStage {...props} renderMode="overlay" />
  </AbsoluteFill>
);

export const AnimatedSearchDemo: React.FC<AnimatedSearchBarProps> = (props) => {
  const frame = useCurrentFrame();
  const drift = interpolate(frame, [0, 180], [-40, 90], {
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
          transform: `translate3d(${drift * 0.42}px, ${drift * 0.1}px, 0)`,
          background:
            "radial-gradient(circle at 82% 25%, rgba(98,230,184,0.42), transparent 28%), radial-gradient(circle at 12% 74%, rgba(31,102,86,0.44), transparent 31%), #07110F",
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
        Minthy Motion System · Search
      </div>
      <SearchStage {...props} renderMode="embedded" />
    </AbsoluteFill>
  );
};
