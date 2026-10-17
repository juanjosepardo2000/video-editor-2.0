import React from "react";
import { AbsoluteFill } from "remotion";
import { LiquidGlassCard, type LiquidGlassCardProps } from "../components/LiquidGlassCard";
import { colors, safeArea, spacing, typography } from "../design/tokens";

const CardStage: React.FC<LiquidGlassCardProps> = (props) => (
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
    <LiquidGlassCard {...props} />
  </AbsoluteFill>
);

export const LiquidGlassOverlay: React.FC<LiquidGlassCardProps> = (props) => (
  <AbsoluteFill style={{ backgroundColor: "transparent" }}>
    <CardStage {...props} />
  </AbsoluteFill>
);

export const LiquidGlassDemo: React.FC<LiquidGlassCardProps> = (props) => (
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
        top: 90,
        right: -260,
        width: 720,
        height: 720,
        borderRadius: "50%",
        background: "radial-gradient(circle, rgba(98,230,184,0.38), rgba(98,230,184,0) 68%)",
      }}
    />
    <div
      style={{
        position: "absolute",
        bottom: 160,
        left: -320,
        width: 820,
        height: 820,
        borderRadius: "50%",
        background: "radial-gradient(circle, rgba(42,119,101,0.34), rgba(42,119,101,0) 70%)",
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
      Minthy Motion System
    </div>
    <CardStage {...props} />
  </AbsoluteFill>
);
