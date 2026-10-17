import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { colors, radii, spacing, typography } from "../design/tokens";

export type LiquidGlassRenderMode = "overlay" | "embedded";
export type LiquidGlassVariant = "regular" | "clear";
export type LiquidGlassContrast = "dark" | "light";

export type LiquidGlassCardV2Props = {
  eyebrow: string;
  title: string;
  description: string;
  metric: string;
  metricLabel: string;
  actionLabel?: string;
  accent?: string;
  renderMode?: LiquidGlassRenderMode;
  variant?: LiquidGlassVariant;
  contrast?: LiquidGlassContrast;
  reducedMotion?: boolean;
};

type SurfacePalette = {
  foreground: string;
  muted: string;
  surface: string;
  border: string;
  shadow: string;
  dimming: string;
  bevel: string;
};

const getSurfacePalette = (
  renderMode: LiquidGlassRenderMode,
  variant: LiquidGlassVariant,
  contrast: LiquidGlassContrast,
): SurfacePalette => {
  const isDark = contrast === "dark";
  const isClear = variant === "clear";
  const isOverlay = renderMode === "overlay";

  if (isDark) {
    return {
      foreground: "#F7FCFA",
      muted: "#B9CAC4",
      surface: isClear
        ? isOverlay
          ? "rgba(5, 15, 13, 0.48)"
          : "rgba(5, 15, 13, 0.2)"
        : isOverlay
          ? "rgba(5, 15, 13, 0.82)"
          : "rgba(5, 15, 13, 0.46)",
      border: isClear ? "rgba(235, 255, 248, 0.34)" : "rgba(235, 255, 248, 0.26)",
      shadow: "rgba(0, 0, 0, 0.42)",
      dimming: isClear
        ? "linear-gradient(90deg, rgba(3,10,8,0.7) 0%, rgba(3,10,8,0.48) 62%, rgba(3,10,8,0.24) 100%)"
        : "linear-gradient(135deg, rgba(255,255,255,0.09), transparent 42%, rgba(98,230,184,0.05))",
      bevel: "rgba(255, 255, 255, 0.72)",
    };
  }

  return {
    foreground: "#07110F",
    muted: "#40544E",
    surface: isClear
      ? isOverlay
        ? "rgba(245, 252, 249, 0.58)"
        : "rgba(245, 252, 249, 0.24)"
      : isOverlay
        ? "rgba(245, 252, 249, 0.9)"
        : "rgba(245, 252, 249, 0.58)",
    border: isClear ? "rgba(255, 255, 255, 0.68)" : "rgba(255, 255, 255, 0.82)",
    shadow: "rgba(7, 17, 15, 0.28)",
    dimming: isClear
      ? "linear-gradient(90deg, rgba(246,252,249,0.82) 0%, rgba(246,252,249,0.62) 62%, rgba(246,252,249,0.34) 100%)"
      : "linear-gradient(135deg, rgba(255,255,255,0.38), transparent 46%, rgba(98,230,184,0.08))",
    bevel: "rgba(255, 255, 255, 0.94)",
  };
};

export const LiquidGlassCardV2: React.FC<LiquidGlassCardV2Props> = ({
  eyebrow,
  title,
  description,
  metric,
  metricLabel,
  actionLabel = "Ver detalle",
  accent = colors.primary,
  renderMode = "overlay",
  variant = "regular",
  contrast = "dark",
  reducedMotion = false,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const palette = getSurfacePalette(renderMode, variant, contrast);

  const entrance = reducedMotion
    ? interpolate(frame, [0, 12], [0, 1], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      })
    : spring({
        frame,
        fps,
        config: { damping: 20, mass: 0.78, stiffness: 105 },
        durationInFrames: 42,
      });
  const copyOpacity = interpolate(frame, reducedMotion ? [2, 14] : [10, 30], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const ambientPulse = reducedMotion ? 0.45 : 0.45 + Math.sin(frame / 28) * 0.12;
  const lightX = reducedMotion ? 68 : 50 + Math.sin(frame / 42) * 34;
  const lightY = reducedMotion ? 12 : 14 + Math.cos(frame / 54) * 12;
  const sweep = reducedMotion
    ? -400
    : interpolate(frame, [4, 86], [-420, 1040], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      });
  const translateY = reducedMotion ? 0 : interpolate(entrance, [0, 1], [72, 0]);
  const scale = reducedMotion ? 1 : interpolate(entrance, [0, 1], [0.965, 1]);
  const borderOpacity = 0.72 + entrance * 0.28;
  const backdrop =
    renderMode === "embedded"
      ? variant === "clear"
        ? "blur(18px) saturate(132%)"
        : "blur(30px) saturate(124%)"
      : "blur(12px) saturate(112%)";

  return (
    <div
      style={{
        position: "relative",
        width: 880,
        minHeight: 560,
        boxSizing: "border-box",
        overflow: "hidden",
        padding: spacing.xxl,
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        color: palette.foreground,
        fontFamily: typography.family,
        backgroundColor: palette.surface,
        border: `2px solid ${palette.border}`,
        borderRadius: radii.lg,
        boxShadow: `0 ${26 + entrance * 12}px ${72 + entrance * 34}px ${palette.shadow}, inset 0 1px 0 rgba(255,255,255,${
          0.16 + ambientPulse * 0.16
        })`,
        backdropFilter: backdrop,
        transform: `translateY(${translateY}px) scale(${scale})`,
        opacity: entrance,
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          borderRadius: radii.lg,
          opacity: borderOpacity,
          background: palette.dimming,
          pointerEvents: "none",
        }}
      />

      <div
        style={{
          position: "absolute",
          inset: 2,
          borderRadius: radii.lg - 2,
          pointerEvents: "none",
          background: `radial-gradient(circle at ${lightX}% ${lightY}%, rgba(255,255,255,${
            0.12 + ambientPulse * 0.16
          }) 0%, rgba(255,255,255,0.04) 22%, transparent 48%)`,
        }}
      />

      <div
        style={{
          position: "absolute",
          top: -150,
          left: sweep,
          width: 150,
          height: 900,
          opacity: variant === "clear" ? 0.28 : 0.19,
          background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.8), transparent)",
          filter: "blur(5px)",
          transform: "rotate(18deg)",
          pointerEvents: "none",
        }}
      />

      <div
        style={{
          position: "absolute",
          top: 0,
          left: 72,
          right: 72,
          height: 2,
          opacity: 0.42 + ambientPulse * 0.44,
          background: `linear-gradient(90deg, transparent, ${palette.bevel}, transparent)`,
          pointerEvents: "none",
        }}
      />

      <div style={{ position: "relative", opacity: copyOpacity }}>
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: spacing.sm,
            marginBottom: spacing.lg,
            color: accent,
            fontSize: typography.eyebrow,
            fontWeight: 700,
            letterSpacing: 3,
            textTransform: "uppercase",
          }}
        >
          <span
            style={{
              width: 12,
              height: 12,
              borderRadius: radii.full,
              backgroundColor: accent,
              boxShadow: `0 0 ${18 + ambientPulse * 16}px ${accent}`,
            }}
          />
          {eyebrow}
        </div>

        <div
          style={{
            maxWidth: 700,
            fontSize: typography.title,
            lineHeight: 1.05,
            fontWeight: 720,
            letterSpacing: -2.2,
            textShadow: contrast === "dark" ? "0 2px 18px rgba(0,0,0,0.2)" : "none",
          }}
        >
          {title}
        </div>
        <div
          style={{
            maxWidth: 720,
            marginTop: spacing.md,
            color: palette.muted,
            fontSize: typography.body,
            lineHeight: 1.45,
            fontWeight: 450,
          }}
        >
          {description}
        </div>
      </div>

      <div
        style={{
          position: "relative",
          display: "flex",
          alignItems: "flex-end",
          justifyContent: "space-between",
          gap: spacing.lg,
          marginTop: spacing.xl,
          opacity: copyOpacity,
        }}
      >
        <div style={{ display: "flex", alignItems: "baseline", gap: spacing.md }}>
          <span
            style={{
              color: accent,
              fontSize: typography.metric,
              lineHeight: 0.82,
              fontWeight: 760,
              letterSpacing: -5,
            }}
          >
            {metric}
          </span>
          <span
            style={{
              maxWidth: 220,
              color: palette.muted,
              fontSize: typography.eyebrow,
              lineHeight: 1.25,
              fontWeight: 600,
            }}
          >
            {metricLabel}
          </span>
        </div>

        <div
          style={{
            padding: `${spacing.sm}px ${spacing.md}px`,
            color: colors.primaryForeground,
            backgroundColor: accent,
            borderRadius: radii.full,
            boxShadow: `0 10px 28px rgba(0,0,0,${0.14 + ambientPulse * 0.08})`,
            fontSize: typography.eyebrow,
            fontWeight: 750,
          }}
        >
          {actionLabel}
        </div>
      </div>
    </div>
  );
};
