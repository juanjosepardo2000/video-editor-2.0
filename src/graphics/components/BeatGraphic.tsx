import React from "react";
import type {VisualTag} from "../beatmap/types";
import {AnimatedSearchBar} from "./AnimatedSearchBar";
import {BigStat} from "./BigStat";
import {ComparisonPanel} from "./ComparisonPanel";
import {DynamicNumberCounter} from "./DynamicNumberCounter";
import {KineticTextInterlude} from "./KineticTextInterlude";
import {LiquidGlassCardV2} from "./LiquidGlassCardV2";
import {NewsTextHighlighter} from "./NewsTextHighlighter";
import {NumberedPillList} from "./NumberedPillList";

export type BeatGraphicProps = {
  tag: VisualTag | null;
  text: string;
  accent: string;
  theme: "light" | "dark";
  fontFamily: string;
  accentFontFamily: string;
  reducedMotion?: boolean;
  compact?: boolean;
};

export type GraphicCanvasSize = {width: number; height: number};

export const graphicCanvasSize = (tag: VisualTag | null): GraphicCanvasSize =>
  tag === "tarjeta" || tag === "recuadro" || tag === null
    ? {width: 760, height: 300}
    : {width: 900, height: 700};

export const splitListItems = (text: string): string[] =>
  text.split(/\s*(?:[;•]|\s→\s)\s*/).map((item) => item.trim()).filter(Boolean);

export const splitComparison = (text: string): [string, string] | null => {
  const parts = text.split(/\s+(?:vs\.?|versus)\s+|\s*[|→]\s*/i).map((item) => item.trim()).filter(Boolean);
  return parts.length === 2 ? [parts[0], parts[1]] : null;
};

export const parseStat = (text: string): {value: number; prefix: string; suffix: string; context: string} | null => {
  const match = text.match(/([€$]?)([-+]?\d+(?:[.,]\d+)?)(\s*%?)/);
  if (!match || match.index === undefined) return null;
  const value = Number(match[2].replace(",", "."));
  if (!Number.isFinite(value)) return null;
  return {
    value,
    prefix: match[1],
    suffix: match[3].trim(),
    context: `${text.slice(0, match.index)}${text.slice(match.index + match[0].length)}`.trim(),
  };
};

export const BeatGraphic: React.FC<BeatGraphicProps> = ({tag, text, accent, theme, fontFamily, accentFontFamily, reducedMotion = false, compact = false}) => {
  const stat = parseStat(text);
  if (tag === "contador" && stat) {
    return <DynamicNumberCounter label="" startValue={0} endValue={stat.value} prefix={stat.prefix} suffix={stat.suffix} trendLabel="" supportingText={stat.context} accent={accent} reducedMotion={reducedMotion} />;
  }
  if (tag === "cifra" && stat) {
    return <BigStat value={`${stat.prefix}${stat.value.toLocaleString("es-ES")}${stat.suffix}`} context={stat.context} accent={accent} fontFamily={fontFamily} />;
  }
  if (tag === "comparacion") {
    const comparison = splitComparison(text);
    if (comparison) return <ComparisonPanel left={comparison[0]} right={comparison[1]} accent={accent} fontFamily={fontFamily} />;
  }
  if (tag === "lista") return <NumberedPillList items={splitListItems(text)} accent={accent} fontFamily={fontFamily} />;
  if (tag === "interludio") return <KineticTextInterlude text={text} accent={accent} fontFamily={accentFontFamily} />;
  if (tag === "titular") return <NewsTextHighlighter category="" source="" timestamp="" headline={[{text, highlighted: true}]} summary="" accent={accent} reducedMotion={reducedMotion} />;
  if (tag === "busqueda") return <AnimatedSearchBar label="" mistypedQuery={text} correctedQuery={text} resultLabel="" suggestions={[]} accent={accent} reducedMotion={reducedMotion} />;
  return <LiquidGlassCardV2 title={text} accent={accent} renderMode="overlay" contrast={theme} reducedMotion={reducedMotion} size={compact ? "compact" : "regular"} />;
};
