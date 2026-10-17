import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { colors, radii, spacing, typography } from "../design/tokens";

export type AnimatedSearchBarProps = {
  label: string;
  mistypedQuery: string;
  correctedQuery: string;
  resultLabel: string;
  suggestions: string[];
  accent?: string;
  renderMode?: "overlay" | "embedded";
  reducedMotion?: boolean;
};

type TypingState = {
  text: string;
  phase: "typing" | "holding" | "correcting" | "ready";
  readyFrame: number;
};

const commonPrefixLength = (first: string, second: string) => {
  const limit = Math.min(first.length, second.length);
  let index = 0;
  while (index < limit && first[index] === second[index]) index += 1;
  return index;
};

const getTypingState = (
  frame: number,
  mistypedQuery: string,
  correctedQuery: string,
  reducedMotion: boolean,
): TypingState => {
  if (reducedMotion) {
    return { text: correctedQuery, phase: "ready", readyFrame: 10 };
  }

  const prefixLength = commonPrefixLength(mistypedQuery, correctedQuery);
  const typeStart = 26;
  const framesPerTypedCharacter = 3;
  const framesPerDeletedCharacter = 2;
  const typedEnd = typeStart + mistypedQuery.length * framesPerTypedCharacter;
  const holdEnd = typedEnd + 14;
  const deleteCount = mistypedQuery.length - prefixLength;
  const deleteEnd = holdEnd + deleteCount * framesPerDeletedCharacter;
  const correctedSuffix = correctedQuery.slice(prefixLength);
  const readyFrame = deleteEnd + correctedSuffix.length * framesPerTypedCharacter;

  if (frame < typeStart) return { text: "", phase: "typing", readyFrame };
  if (frame < typedEnd) {
    const count = Math.floor((frame - typeStart) / framesPerTypedCharacter) + 1;
    return { text: mistypedQuery.slice(0, count), phase: "typing", readyFrame };
  }
  if (frame < holdEnd) return { text: mistypedQuery, phase: "holding", readyFrame };
  if (frame < deleteEnd) {
    const deleted = Math.floor((frame - holdEnd) / framesPerDeletedCharacter) + 1;
    return {
      text: mistypedQuery.slice(0, Math.max(prefixLength, mistypedQuery.length - deleted)),
      phase: "correcting",
      readyFrame,
    };
  }
  if (frame < readyFrame) {
    const typed = Math.floor((frame - deleteEnd) / framesPerTypedCharacter) + 1;
    return {
      text: correctedQuery.slice(0, prefixLength) + correctedSuffix.slice(0, typed),
      phase: "correcting",
      readyFrame,
    };
  }
  return { text: correctedQuery, phase: "ready", readyFrame };
};

const SearchIcon: React.FC<{ color: string }> = ({ color }) => (
  <svg width="42" height="42" viewBox="0 0 42 42" fill="none" aria-hidden="true">
    <circle cx="18" cy="18" r="11" stroke={color} strokeWidth="3.5" />
    <path d="M26.5 26.5L36 36" stroke={color} strokeWidth="3.5" strokeLinecap="round" />
  </svg>
);

export const AnimatedSearchBar: React.FC<AnimatedSearchBarProps> = ({
  label,
  mistypedQuery,
  correctedQuery,
  resultLabel,
  suggestions,
  accent = colors.primary,
  renderMode = "overlay",
  reducedMotion = false,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const typing = getTypingState(frame, mistypedQuery, correctedQuery, reducedMotion);
  const entrance = reducedMotion
    ? interpolate(frame, [0, 12], [0, 1], {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
      })
    : spring({
        frame,
        fps,
        durationInFrames: 34,
        config: { damping: 19, mass: 0.72, stiffness: 115 },
      });
  const resultsProgress = interpolate(frame, [typing.readyFrame, typing.readyFrame + 16], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const cursorVisible = typing.phase === "ready" ? frame % 28 < 14 : frame % 16 < 8;
  const isCorrecting = typing.phase === "correcting";
  const isReady = typing.phase === "ready";
  const surfaceAlpha = renderMode === "embedded" ? 0.56 : 0.88;
  const ambientX = reducedMotion ? 74 : 68 + Math.sin(frame / 38) * 20;

  return (
    <div
      style={{
        position: "relative",
        width: 900,
        minHeight: 480,
        boxSizing: "border-box",
        overflow: "hidden",
        padding: spacing.xl,
        color: colors.foreground,
        fontFamily: typography.family,
        backgroundColor: `rgba(5, 15, 13, ${surfaceAlpha})`,
        border: `2px solid ${colors.border}`,
        borderRadius: radii.lg,
        boxShadow: `0 34px 100px rgba(0,0,0,0.38), inset 0 1px 0 rgba(255,255,255,0.2)`,
        backdropFilter: renderMode === "embedded" ? "blur(30px) saturate(128%)" : "blur(12px)",
        transform: `translateY(${interpolate(entrance, [0, 1], [62, 0])}px) scale(${interpolate(
          entrance,
          [0, 1],
          [0.97, 1],
        )})`,
        opacity: entrance,
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          pointerEvents: "none",
          background: `radial-gradient(circle at ${ambientX}% 8%, rgba(98,230,184,0.2), transparent 38%)`,
        }}
      />

      <div
        style={{
          position: "relative",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          marginBottom: spacing.lg,
        }}
      >
        <div
          style={{
            color: colors.mutedForeground,
            fontSize: typography.eyebrow,
            fontWeight: 700,
            letterSpacing: 2.8,
            textTransform: "uppercase",
          }}
        >
          {label}
        </div>
        <div
          style={{
            padding: `${spacing.xs}px ${spacing.sm}px`,
            color: isCorrecting || isReady ? colors.primaryForeground : colors.mutedForeground,
            backgroundColor: isCorrecting || isReady ? accent : "rgba(255,255,255,0.08)",
            borderRadius: radii.full,
            fontSize: 20,
            fontWeight: 720,
          }}
        >
          {isReady ? "Corrección aplicada" : isCorrecting ? "Corrigiendo" : "Escuchando"}
        </div>
      </div>

      <div
        style={{
          position: "relative",
          height: 118,
          boxSizing: "border-box",
          display: "flex",
          alignItems: "center",
          gap: spacing.md,
          padding: `0 ${spacing.lg}px`,
          backgroundColor: "rgba(255,255,255,0.08)",
          border: `2px solid ${isCorrecting || isReady ? "rgba(98,230,184,0.62)" : "rgba(255,255,255,0.14)"}`,
          borderRadius: radii.md,
          boxShadow: isCorrecting || isReady ? "0 0 0 5px rgba(98,230,184,0.08)" : "none",
        }}
      >
        <SearchIcon color={isCorrecting || isReady ? accent : colors.mutedForeground} />
        <div
          style={{
            minWidth: 0,
            flex: 1,
            overflow: "hidden",
            whiteSpace: "nowrap",
            fontSize: 44,
            fontWeight: 610,
            letterSpacing: -1.2,
          }}
        >
          {typing.text}
          <span style={{ color: accent, opacity: cursorVisible ? 1 : 0 }}>|</span>
        </div>
      </div>

      <div
        style={{
          position: "relative",
          minHeight: 150,
          marginTop: spacing.lg,
          opacity: resultsProgress,
          transform: `translateY(${interpolate(resultsProgress, [0, 1], [22, 0])}px)`,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: spacing.sm,
            marginBottom: spacing.md,
            color: colors.mutedForeground,
            fontSize: 25,
            fontWeight: 600,
          }}
        >
          <span
            style={{
              width: 11,
              height: 11,
              borderRadius: radii.full,
              backgroundColor: accent,
              boxShadow: `0 0 18px ${accent}`,
            }}
          />
          {resultLabel}
        </div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: spacing.sm }}>
          {suggestions.map((suggestion, index) => {
            const chipProgress = interpolate(
              frame,
              [typing.readyFrame + 8 + index * 5, typing.readyFrame + 20 + index * 5],
              [0, 1],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
            );
            return (
              <div
                key={suggestion}
                style={{
                  padding: `${spacing.sm}px ${spacing.md}px`,
                  color: colors.foreground,
                  backgroundColor: "rgba(255,255,255,0.08)",
                  border: "1px solid rgba(255,255,255,0.14)",
                  borderRadius: radii.full,
                  fontSize: 23,
                  fontWeight: 620,
                  opacity: chipProgress,
                  transform: `translateY(${interpolate(chipProgress, [0, 1], [12, 0])}px)`,
                }}
              >
                {suggestion}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
