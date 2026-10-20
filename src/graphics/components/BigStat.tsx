import React from "react";
import {interpolate, useCurrentFrame} from "remotion";

export type BigStatProps = {
  value: string;
  context?: string;
  accent: string;
  fontFamily: string;
};

export const BigStat: React.FC<BigStatProps> = ({value, context, accent, fontFamily}) => {
  const frame = useCurrentFrame();
  const progress = interpolate(frame, [0, 18], [0, 1], {extrapolateLeft: "clamp", extrapolateRight: "clamp"});
  return <div style={{fontFamily, textAlign: "center", opacity: progress, transform: `scale(${interpolate(progress, [0, 1], [.82, 1])})`}}>
    <div style={{color: accent, fontSize: 196, lineHeight: .9, fontWeight: 850, letterSpacing: -9, fontVariantNumeric: "tabular-nums"}}>{value}</div>
    {context ? <div style={{marginTop: 28, fontSize: 50, lineHeight: 1.08, fontWeight: 700}}>{context}</div> : null}
  </div>;
};
