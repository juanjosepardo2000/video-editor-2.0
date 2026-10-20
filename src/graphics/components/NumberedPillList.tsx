import React from "react";
import {interpolate, spring, useCurrentFrame, useVideoConfig} from "remotion";

export type NumberedPillListProps = {
  items: readonly string[];
  accent: string;
  fontFamily: string;
};

export const NumberedPillList: React.FC<NumberedPillListProps> = ({items, accent, fontFamily}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return <div style={{display: "grid", gap: 18, width: "100%", fontFamily}}>
    {items.map((item, index) => {
      const progress = spring({frame: Math.max(0, frame - index * 5), fps, durationInFrames: 22, config: {damping: 20, stiffness: 145}});
      return <div key={`${item}-${index}`} style={{display: "flex", alignItems: "center", gap: 22, padding: "18px 26px", borderRadius: 999, background: "rgba(255,255,255,.92)", color: "#171A19", boxShadow: "0 18px 48px rgba(0,0,0,.18)", fontSize: 40, fontWeight: 700, opacity: progress, transform: `translateX(${interpolate(progress, [0, 1], [42, 0])}px)`}}>
        <span style={{display: "grid", placeItems: "center", width: 54, height: 54, flex: "0 0 54px", borderRadius: 999, background: accent, color: "#111", fontSize: 28}}>{index + 1}</span>
        <span>{item}</span>
      </div>;
    })}
  </div>;
};
