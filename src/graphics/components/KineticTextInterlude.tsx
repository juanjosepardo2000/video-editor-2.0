import React from "react";
import {interpolate, spring, useCurrentFrame, useVideoConfig} from "remotion";

export type KineticTextInterludeProps = {
  text: string;
  accent: string;
  fontFamily: string;
};

export const KineticTextInterlude: React.FC<KineticTextInterludeProps> = ({text, accent, fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const words = text.trim().split(/\s+/).filter(Boolean);
  return <div style={{display: "flex", flexWrap: "wrap", justifyContent: "center", gap: "12px 20px", fontFamily, fontSize: 88, fontWeight: 800, lineHeight: 1.02, textAlign: "center"}}>
    {words.map((word, index) => {
      const progress = spring({frame: Math.max(0, frame - index * 3), fps, durationInFrames: 18, config: {damping: 18, stiffness: 170}});
      return <span key={`${word}-${index}`} style={{color: index === words.length - 1 ? accent : "currentColor", opacity: progress, transform: `translateY(${interpolate(progress, [0, 1], [34, 0])}px) scale(${interpolate(progress, [0, 1], [0.88, 1])})`}}>{word}</span>;
    })}
  </div>;
};
