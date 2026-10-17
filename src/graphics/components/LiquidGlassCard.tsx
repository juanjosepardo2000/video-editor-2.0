import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { colors, radii, spacing, typography } from "../design/tokens";

export type LiquidGlassCardProps = {
  eyebrow: string;
  title: string;
  description: string;
  metric: string;
  metricLabel: string;
  accent?: string;
};

export const LiquidGlassCard: React.FC<LiquidGlassCardProps> = ({
  eyebrow,
  title,
  description,
  metric,
  metricLabel,
  accent = colors.primary,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const entrance = spring({
    frame,
    fps,
    config: { damping: 18, mass: 0.8, stiffness: 110 },
    durationInFrames: 36,
  });
  const copyOpacity = interpolate(frame, [10, 28], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const shimmerX = interpolate(frame, [0, 120], [-420, 980], {
    extrapolateRight: "extend",
  });

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
        color: colors.foreground,
        fontFamily: typography.family,
        background: colors.card,
        border: `2px solid ${colors.border}`,
        borderRadius: radii.lg,
        boxShadow: `0 36px 100px ${colors.shadow}, inset 0 1px 0 rgba(255,255,255,0.24)`,
        backdropFilter: "blur(28px) saturate(125%)",
        transform: `translateY(${interpolate(entrance, [0, 1], [90, 0])}px) scale(${interpolate(
          entrance,
          [0, 1],
          [0.94, 1],
        )})`,
        opacity: entrance,
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          pointerEvents: "none",
          background:
            "linear-gradient(135deg, rgba(255,255,255,0.16) 0%, rgba(255,255,255,0.03) 42%, rgba(255,255,255,0.08) 100%)",
        }}
      />
      <div
        style={{
          position: "absolute",
          top: -120,
          left: shimmerX,
          width: 180,
          height: 860,
          opacity: 0.22,
          background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.34), transparent)",
          transform: "rotate(20deg)",
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
              boxShadow: `0 0 24px ${accent}`,
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
          }}
        >
          {title}
        </div>
        <div
          style={{
            maxWidth: 720,
            marginTop: spacing.md,
            color: colors.mutedForeground,
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
              color: colors.mutedForeground,
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
            fontSize: typography.eyebrow,
            fontWeight: 750,
          }}
        >
          Ver detalle
        </div>
      </div>
    </div>
  );
};
