import React from "react";
import {AbsoluteFill, Sequence} from "remotion";
import type {VisualTag} from "../beatmap/types";
import {BeatGraphic} from "../components/BeatGraphic";
import {loadedFonts} from "../design/fonts";

const samples: readonly {tag: VisualTag; text: string}[] = [
  {tag: "contador", text: "25% de mejora"},
  {tag: "cifra", text: "3 pasos"},
  {tag: "comparacion", text: "Antes vs Después"},
  {tag: "lista", text: "Idea; Diseño; Resultado"},
  {tag: "interludio", text: "Haz que importe"},
  {tag: "titular", text: "La edición cambia el mensaje"},
  {tag: "busqueda", text: "Cómo editar mejor"},
] as const;

export const G3ComponentGallery: React.FC = () => <AbsoluteFill style={{background: "#07110F", color: "#F7FCFA"}}>
  {samples.map((sample, index) => <Sequence key={sample.tag} from={index * 60} durationInFrames={60}>
    <AbsoluteFill style={{display: "flex", alignItems: "center", justifyContent: "center", padding: 90, boxSizing: "border-box"}}>
      <BeatGraphic tag={sample.tag} text={sample.text} accent="#F28C28" theme="dark" fontFamily={loadedFonts.inter} accentFontFamily={loadedFonts.caveat} />
    </AbsoluteFill>
  </Sequence>)}
</AbsoluteFill>;
