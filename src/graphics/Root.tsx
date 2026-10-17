import React from "react";
import { Composition, AbsoluteFill } from "remotion";

const MainComposition: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: "transparent", fontFamily: "Inter, sans-serif" }}>
      {/* TODO: componentes de src/graphics/components (respetar zonas seguras 9:16) */}
    </AbsoluteFill>
  );
};

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="MainComposition"
      component={MainComposition}
      durationInFrames={300}
      fps={30}
      width={1080}
      height={1920}
    />
  );
};
