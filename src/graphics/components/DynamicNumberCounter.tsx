import React from "react";
import { Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { colors, radii, spacing, typography } from "../design/tokens";

export type DynamicNumberCounterProps = {
  label: string;
  startValue: number;
  endValue: number;
  prefix?: string;
  suffix?: string;
  decimals?: number;
  trendLabel: string;
  supportingText: string;
  accent?: string;
  trend?: "up" | "down" | "neutral";
  renderMode?: "overlay" | "embedded";
  reducedMotion?: boolean;
};

const clamp = {
  extrapolateLeft: "clamp" as const,
  extrapolateRight: "clamp" as const,
};

const TrendIcon: React.FC<{ trend: "up" | "down" | "neutral" }> = ({ trend }) => {
  const rotation = trend === "down" ? 90 : trend === "neutral" ? 45 : 0;
  return (
    <svg
      width="28"
      height="28"
      viewBox="0 0 28 28"
      fill="none"
      aria-hidden="true"
      style={{ transform: `rotate(${rotation}deg)` }}
    >
      <path d="M6 20L20 6M10 6H20V16" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
};

export const DynamicNumberCounter: React.FC<DynamicNumberCounterProps> = ({
  label,
  startValue,
  endValue,
  prefix = "",
  suffix = "",
  decimals = 0,
  trendLabel,
  supportingText,
  accent = colors.primary,
  trend = "up",
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
        config: { damping: 19, mass: 0.76, stiffness: 116 },
      });
  const countProgress = reducedMotion
    ? interpolate(frame, [10, 18], [0, 1], clamp)
    : interpolate(frame, [28, 116], [0, 1], {
        ...clamp,
        easing: Easing.out(Easing.cubic),
      });
  const value = startValue + (endValue - startValue) * countProgress;
  const formattedValue = new Intl.NumberFormat("es-ES", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
  const detailProgress = interpolate(frame, [108, 130], [0, 1], clamp);
  const chartProgress = interpolate(frame, [40, 124], [0, 1], {
    ...clamp,
    easing: Easing.out(Easing.cubic),
  });
  const surfaceAlpha = renderMode === "embedded" ? 0.64 : 0.93;

  return (
    <div
      style={{
        position: "relative",
        width: 900,
        minHeight: 650,
        boxSizing: "border-box",
        overflow: "hidden",
        padding: spacing.xl,
        color: colors.foreground,
        fontFamily: typography.family,
        backgroundColor: `rgba(5, 15, 13, ${surfaceAlpha})`,
        border: `2px solid ${colors.border}`,
        borderRadius: radii.lg,
        boxShadow: "0 38px 110px rgba(0,0,0,0.42), inset 0 1px 0 rgba(255,255,255,0.18)",
        backdropFilter: renderMode === "embedded" ? "blur(30px) saturate(126%)" : "blur(12px)",
        opacity: entrance,
        transform: `translateY(${interpolate(entrance, [0, 1], [70, 0])}px) scale(${interpolate(
          entrance,
          [0, 1],
          [0.975, 1],
        )})`,
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          pointerEvents: "none",
          background: `radial-gradient(circle at 80% 14%, ${accent}26, transparent 36%)`,
        }}
      />

      <div
        style={{
          position: "relative",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div
          style={{
            color: colors.mutedForeground,
            fontSize: 23,
            fontWeight: 720,
            letterSpacing: 2.7,
            textTransform: "uppercase",
          }}
        >
          {label}
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: spacing.xs,
            padding: `${spacing.xs}px ${spacing.sm}px`,
            color: trend === "down" ? "#FFD4CF" : trend === "neutral" ? colors.foreground : accent,
            backgroundColor:
              trend === "down" ? "rgba(255,102,91,0.12)" : trend === "neutral" ? "rgba(255,255,255,0.08)" : `${accent}18`,
            border: `1px solid ${trend === "down" ? "rgba(255,102,91,0.28)" : `${accent}40`}`,
            borderRadius: radii.full,
            fontSize: 21,
            fontWeight: 720,
          }}
        >
          <TrendIcon trend={trend} />
          {trendLabel}
        </div>
      </div>

      <div
        style={{
          position: "relative",
          display: "flex",
          alignItems: "baseline",
          marginTop: spacing.xl,
          fontVariantNumeric: "tabular-nums",
          whiteSpace: "nowrap",
        }}
      >
        {prefix ? (
          <span style={{ marginRight: 10, color: accent, fontSize: 66, fontWeight: 720 }}>{prefix}</span>
        ) : null}
        <span
          style={{
            fontSize: 176,
            lineHeight: 0.92,
            fontWeight: 790,
            letterSpacing: -8,
          }}
        >
          {formattedValue}
        </span>
        {suffix ? (
          <span style={{ marginLeft: 12, color: accent, fontSize: 70, fontWeight: 740 }}>{suffix}</span>
        ) : null}
      </div>

      <div
        style={{
          position: "relative",
          marginTop: spacing.xl,
          height: 124,
          overflow: "hidden",
          borderRadius: radii.md,
          backgroundColor: "rgba(255,255,255,0.045)",
          border: "1px solid rgba(255,255,255,0.1)",
        }}
      >
        {[1, 2, 3].map((line) => (
          <div
            key={line}
            style={{
              position: "absolute",
              left: 0,
              right: 0,
              top: `${line * 25}%`,
              height: 1,
              backgroundColor: "rgba(255,255,255,0.07)",
            }}
          />
        ))}
        <svg width="100%" height="124" viewBox="0 0 800 124" preserveAspectRatio="none" aria-hidden="true">
          <path
            d="M0 101 C88 95 126 80 190 85 C258 90 292 57 355 65 C431 75 465 48 527 51 C604 54 645 26 800 17"
            fill="none"
            stroke={accent}
            strokeWidth="7"
            strokeLinecap="round"
            pathLength="1"
            strokeDasharray="1"
            strokeDashoffset={1 - chartProgress}
          />
        </svg>
        <div
          style={{
            position: "absolute",
            right: 20,
            top: 10,
            width: 14,
            height: 14,
            borderRadius: radii.full,
            backgroundColor: accent,
            boxShadow: `0 0 22px ${accent}`,
            opacity: chartProgress,
            transform: `scale(${interpolate(chartProgress, [0.88, 1], [0, 1], clamp)})`,
          }}
        />
      </div>

      <div
        style={{
          position: "relative",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: spacing.lg,
          marginTop: spacing.lg,
          opacity: detailProgress,
          transform: `translateY(${interpolate(detailProgress, [0, 1], [16, 0])}px)`,
        }}
      >
        <div style={{ color: colors.mutedForeground, fontSize: 27, lineHeight: 1.36, fontWeight: 500 }}>
          {supportingText}
        </div>
        <div
          style={{
            flexShrink: 0,
            color: colors.primaryForeground,
            backgroundColor: accent,
            borderRadius: radii.full,
            padding: `${spacing.xs}px ${spacing.sm}px`,
            fontSize: 19,
            fontWeight: 780,
            letterSpacing: 1.6,
            textTransform: "uppercase",
          }}
        >
          En vivo
        </div>
      </div>
    </div>
  );
};
