import React from "react";
import {AbsoluteFill, interpolate, OffthreadVideo, staticFile, useCurrentFrame} from "remotion";

export type BrollSceneProps = {
  publicFile: string;
  text?: string;
  accent: string;
  textColor: string;
  fontFamily: string;
  startFrom?: number;
  darken?: number;
  blurPx?: number;
};

export const BrollScene: React.FC<BrollSceneProps> = ({publicFile, text, accent, textColor, fontFamily, startFrom = 0, darken = .42, blurPx = 1.5}) => {
  const frame = useCurrentFrame();
  const scale = interpolate(frame, [0, 150], [1.03, 1.1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  return <AbsoluteFill style={{overflow: "hidden", background: "#050807"}}>
    <OffthreadVideo muted src={staticFile(publicFile)} startFrom={startFrom} style={{width: "100%", height: "100%", objectFit: "cover", transform: `scale(${scale})`, filter: `blur(${blurPx}px)`}} />
    <AbsoluteFill style={{background: `rgba(0,0,0,${darken})`}} />
    {text?.trim() ? <AbsoluteFill style={{display: "flex", alignItems: "center", justifyContent: "center", padding: 96, boxSizing: "border-box", fontFamily, color: textColor, textAlign: "center"}}>
      <div style={{maxWidth: 880, fontSize: 78, lineHeight: 1.04, fontWeight: 800, letterSpacing: -2.5, textShadow: "0 5px 30px rgba(0,0,0,.7)"}}>
        <span style={{boxShadow: `inset 0 -10px 0 ${accent}88`}}>{text}</span>
      </div>
    </AbsoluteFill> : null}
  </AbsoluteFill>;
};
