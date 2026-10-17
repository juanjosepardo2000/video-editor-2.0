import React from "react";
import { AbsoluteFill, OffthreadVideo, staticFile } from "remotion";

export type CompositeReviewProps = {
  speakerFile: string;
  overlayFile: string;
};

export const CompositeReview: React.FC<CompositeReviewProps> = ({
  speakerFile,
  overlayFile,
}) => (
  <AbsoluteFill style={{ backgroundColor: "#101312", overflow: "hidden" }}>
    <OffthreadVideo
      src={staticFile(speakerFile)}
      style={{ width: "100%", height: "100%", objectFit: "cover" }}
    />
    <OffthreadVideo
      src={staticFile(overlayFile)}
      muted
      style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}
    />
  </AbsoluteFill>
);

