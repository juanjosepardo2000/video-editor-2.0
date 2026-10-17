import { loadFont as loadCaveat } from "@remotion/google-fonts/Caveat";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";

const inter = loadInter("normal", {
  weights: ["600", "700"],
  subsets: ["latin", "latin-ext"],
});

const caveat = loadCaveat("normal", {
  weights: ["600", "700"],
  subsets: ["latin", "latin-ext"],
});

export const loadedFonts = {
  inter: inter.fontFamily,
  caveat: caveat.fontFamily,
} as const;

/**
 * Resuelve los nombres declarados por profile.json a fuentes cargadas y con
 * licencia OFL. CoolVetica se sustituye deliberadamente por Inter mientras no
 * exista una licencia comercial confirmada.
 */
export const resolveProfileFont = (configuredName: string): string => {
  const normalized = configuredName.trim().toLocaleLowerCase("es-ES");
  if (normalized.includes("caveat")) return `${loadedFonts.caveat}, cursive`;
  return `${loadedFonts.inter}, Arial, sans-serif`;
};

