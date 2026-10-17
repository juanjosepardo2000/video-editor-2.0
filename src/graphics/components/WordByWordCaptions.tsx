import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { colors, radii, safeArea, spacing, typography } from "../design/tokens";
import type { TimedCaptionWord } from "../beatmap/types";

export type WordByWordCaptionsProps = {
  text: string;
  durationInFrames: number;
  words?: readonly TimedCaptionWord[];
  accentKeywords?: readonly string[];
  accent?: string;
  accentWordCount?: 1 | 2 | 3;
  wordsPerPage?: 3 | 4 | 5 | 6;
  position?: "lower" | "center";
  theme?: "light" | "dark";
  reducedMotion?: boolean;
};

const clamp = {
  extrapolateLeft: "clamp" as const,
  extrapolateRight: "clamp" as const,
};

export const WordByWordCaptions: React.FC<WordByWordCaptionsProps> = ({
  text,
  durationInFrames,
  words: timedWords,
  accentKeywords = [],
  accent = colors.primary,
  accentWordCount = 1,
  wordsPerPage = 5,
  position = "lower",
  theme = "dark",
  reducedMotion = false,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const fallbackWords = text.trim().split(/\s+/).filter(Boolean);
  const words = timedWords?.length
    ? timedWords
    : fallbackWords.map((word, index) => ({
        text: word,
        startFrame: Math.floor((index / fallbackWords.length) * durationInFrames),
        endFrame: Math.ceil(((index + 1) / fallbackWords.length) * durationInFrames),
      }));
  if (words.length === 0) return null;

  const safeDuration = Math.max(durationInFrames, 12);
  const currentWordIndex = Math.max(
    0,
    words.reduce((latest, word, index) => (frame >= word.startFrame ? index : latest), -1),
  );
  const pageIndex = Math.floor(currentWordIndex / wordsPerPage);
  const pageStart = pageIndex * wordsPerPage;
  const pageWords = words.slice(pageStart, pageStart + wordsPerPage);
  const visibleWords = reducedMotion ? pageWords : pageWords.filter((word) => frame >= word.startFrame);
  const normalizedKeywords = accentKeywords.flatMap((keyword) => keyword.toLocaleLowerCase("es-ES").split(/\s+/)).map((word) => word.replace(/[^\p{L}\p{N}]/gu, ""));
  const exitOpacity = interpolate(frame, [safeDuration - 10, safeDuration - 4], [1, 0], clamp);
  const light = theme === "light";

  return (
    <div
      style={{
        position: "absolute",
        left: safeArea.left,
        right: safeArea.right,
        bottom: position === "lower" ? safeArea.bottom + 36 : undefined,
        top: position === "center" ? "45%" : undefined,
        display: "flex",
        justifyContent: "center",
        opacity: exitOpacity,
        fontFamily: typography.family,
      }}
    >
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          gap: `${spacing.xs}px ${spacing.sm}px`,
          maxWidth: 820,
          padding: `${spacing.sm}px ${spacing.md}px`,
          color: light ? "#1B2421" : colors.foreground,
          backgroundColor: light ? "rgba(245,248,246,0.88)" : "rgba(4, 12, 10, 0.78)",
          border: light ? "1px solid rgba(255,255,255,0.7)" : "1px solid rgba(255,255,255,0.18)",
          borderRadius: radii.md,
          boxShadow: "0 20px 54px rgba(0,0,0,0.34)",
          backdropFilter: "blur(14px)",
          fontSize: 48,
          lineHeight: 1.16,
          fontWeight: 600,
          letterSpacing: -1.3,
          textAlign: "center",
        }}
      >
        {visibleWords.map((word, index) => {
          const normalizedWord = word.text.toLocaleLowerCase("es-ES").replace(/[^\p{L}\p{N}]/gu, "");
          const isKeyword = normalizedKeywords.includes(normalizedWord);
          const keywordRank = visibleWords.slice(0, index + 1).filter((candidate) => normalizedKeywords.includes(candidate.text.toLocaleLowerCase("es-ES").replace(/[^\p{L}\p{N}]/gu, ""))).length;
          const isAccented = isKeyword && keywordRank <= accentWordCount;
          const wordProgress = reducedMotion
            ? 1
            : spring({
                frame: Math.max(frame - word.startFrame, 0),
                fps,
                durationInFrames: 8,
                config: { damping: 18, mass: 0.55, stiffness: 150 },
              });
          return (
            <span
              key={`${pageIndex}-${index}-${word}`}
              style={{
                color: isAccented ? accent : light ? "#1B2421" : colors.foreground,
                opacity: interpolate(wordProgress, [0, 1], [0, 1]),
                transform: `translateY(${interpolate(wordProgress, [0, 1], [14, 0])}px) scale(${interpolate(wordProgress, [0, 1], [0.96, 1])})`,
                textShadow: isAccented ? `0 0 22px ${accent}38` : light ? "none" : "0 2px 12px rgba(0,0,0,0.3)",
              }}
            >
              {word.text}
            </span>
          );
        })}
      </div>
    </div>
  );
};
