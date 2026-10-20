import React from "react";
import {AbsoluteFill, Sequence} from "remotion";
import {generatedBeatMap} from "../beatmap/generated-beatmap";
import {BeatMapComposition} from "./BeatMapComposition";

export const PERFORMANCE_FRAMES = 1800;

export const PerformanceBenchmark: React.FC = () => {
  const loops = Math.ceil(PERFORMANCE_FRAMES / generatedBeatMap.durationInFrames);
  return <AbsoluteFill style={{backgroundColor: "transparent"}}>
    {Array.from({length: loops}, (_, index) => <Sequence key={index} from={index * generatedBeatMap.durationInFrames} durationInFrames={generatedBeatMap.durationInFrames}>
      <BeatMapComposition />
    </Sequence>)}
  </AbsoluteFill>;
};
