import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { colors, radii, safeArea, spacing, typography } from "../design/tokens";
import type { TimedCaptionWord } from "../beatmap/types";
import type { NormalizedBox } from "../layout/types";
import { ensureTextContrast } from "../design/contrast.mjs";

export type CaptionStyle = "word-by-word" | "phrase";

export type CaptionPhrase = {
  words: readonly TimedCaptionWord[];
  startFrame: number;
  endFrame: number;
};

export const groupCaptionPhrases = (
  words: readonly TimedCaptionWord[],
  maximumWords = 7,
): CaptionPhrase[] => {
  const phrases: CaptionPhrase[] = [];
  let current: TimedCaptionWord[] = [];
  for (const word of words) {
    current.push(word);
    const closesPhrase = /[.!?;:]$/.test(word.text) || current.length >= maximumWords;
    if (closesPhrase) {
      phrases.push({
        words: current,
        startFrame: current[0].startFrame,
        endFrame: current[current.length - 1].endFrame,
      });
      current = [];
    }
  }
  if (current.length > 0) {
    phrases.push({
      words: current,
      startFrame: current[0].startFrame,
      endFrame: current[current.length - 1].endFrame,
    });
  }
  return phrases;
};

export type WordByWordCaptionsProps = {
  text: string;
  durationInFrames: number;
  words?: readonly TimedCaptionWord[];
  accentKeywords?: readonly string[];
  accent?: string;
  accentWordCount?: 1 | 2 | 3;
  wordsPerPage?: 1 | 2 | 3 | 4 | 5 | 6;
  position?: "lower" | "center";
  theme?: "light" | "dark";
  captionStyle?: CaptionStyle;
  primaryFontFamily?: string;
  accentFontFamily?: string;
  reducedMotion?: boolean;
  box?: NormalizedBox;
  fontScale?: number;
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
  captionStyle = "word-by-word",
  primaryFontFamily = typography.family,
  accentFontFamily = typography.family,
  reducedMotion = false,
  box,
  fontScale = 1,
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
  const currentWordIndex = words.reduce(
    (latest, word, index) => (frame >= word.startFrame ? index : latest),
    -1,
  );
  const phrases = groupCaptionPhrases(words);
  const currentPhraseIndex = phrases.reduce(
    (latest, phrase, index) => (frame >= phrase.startFrame ? index : latest),
    -1,
  );
  const pageIndex = captionStyle === "phrase"
    ? Math.max(currentPhraseIndex, 0)
    : Math.floor(Math.max(currentWordIndex, 0) / wordsPerPage);
  const pageStart = pageIndex * wordsPerPage;
  const pageWords = captionStyle === "phrase"
    ? phrases[pageIndex]?.words ?? []
    : words.slice(pageStart, pageStart + wordsPerPage);
  const captionsStarted = captionStyle === "phrase" ? currentPhraseIndex >= 0 : currentWordIndex >= 0;
  const visibleWords = !captionsStarted
    ? []
    : captionStyle === "phrase" || reducedMotion
      ? pageWords
      : pageWords.filter((word) => frame >= word.startFrame);
  const normalizedKeywords = accentKeywords.flatMap((keyword) => keyword.toLocaleLowerCase("es-ES").split(/\s+/)).map((word) => word.replace(/[^\p{L}\p{N}]/gu, ""));
  const exitOpacity = interpolate(frame, [safeDuration - 10, safeDuration - 4], [1, 0], clamp);
  const light = theme === "light";
  const captionSurface = light ? "#F5F8F6" : "#040C0A";
  const readableAccent = ensureTextContrast(accent, captionSurface);

  return (
    <div
      style={{
        position: "absolute",
        left: box ? `${box.x * 100}%` : safeArea.left,
        right: box ? undefined : safeArea.right,
        top: box ? `${box.y * 100}%` : position === "center" ? "45%" : undefined,
        bottom: box ? undefined : position === "lower" ? safeArea.bottom + 36 : undefined,
        width: box ? `${box.w * 100}%` : undefined,
        height: box ? `${box.h * 100}%` : undefined,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        opacity: exitOpacity,
        fontFamily: primaryFontFamily,
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
          fontSize: 48 * fontScale,
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
          const animationStart = captionStyle === "phrase"
            ? phrases[pageIndex]?.startFrame ?? word.startFrame
            : word.startFrame;
          const wordProgress = reducedMotion
            ? 1
            : spring({
                frame: Math.max(frame - animationStart, 0),
                fps,
                durationInFrames: 8,
                config: { damping: 18, mass: 0.55, stiffness: 150 },
              });
          return (
            <span
              key={`${pageIndex}-${index}-${word}`}
              style={{
                color: isAccented ? readableAccent : light ? "#1B2421" : colors.foreground,
                fontFamily: isAccented ? accentFontFamily : primaryFontFamily,
                fontSize: isAccented ? "1.12em" : "1em",
                fontWeight: isAccented ? 750 : 600,
                opacity: interpolate(wordProgress, [0, 1], [0, 1]),
                transform: `translateY(${interpolate(wordProgress, [0, 1], [14, 0])}px) scale(${interpolate(wordProgress, [0, 1], [0.96, 1])})`,
                textShadow: isAccented ? `0 0 22px ${readableAccent}38` : light ? "none" : "0 2px 12px rgba(0,0,0,0.3)",
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
