import React from "react";

export type ComparisonPanelProps = {
  left: string;
  right: string;
  accent: string;
  fontFamily: string;
};

export const ComparisonPanel: React.FC<ComparisonPanelProps> = ({left, right, accent, fontFamily}) => (
  <div style={{display: "grid", gridTemplateColumns: "1fr auto 1fr", alignItems: "stretch", gap: 20, width: "100%", fontFamily}}>
    {[left, right].map((text, index) => <React.Fragment key={`${text}-${index}`}>
      {index === 1 ? <div style={{display: "grid", placeItems: "center", color: accent, fontSize: 34, fontWeight: 900}}>VS</div> : null}
      <div style={{display: "grid", placeItems: "center", minHeight: 270, padding: 28, borderRadius: 34, background: index === 0 ? "rgba(255,255,255,.12)" : `${accent}28`, border: `2px solid ${index === 0 ? "rgba(255,255,255,.25)" : accent}`, fontSize: 48, lineHeight: 1.05, fontWeight: 750, textAlign: "center"}}>{text}</div>
    </React.Fragment>)}
  </div>
);
