import type { LiquidGlassCardProps } from "../components/LiquidGlassCard";
import type { LiquidGlassCardV2Props } from "../components/LiquidGlassCardV2";
import type { AnimatedSearchBarProps } from "../components/AnimatedSearchBar";
import type { NewsTextHighlighterProps } from "../components/NewsTextHighlighter";
import type { DynamicNumberCounterProps } from "../components/DynamicNumberCounter";

export const liquidGlassDemo: LiquidGlassCardProps = {
  eyebrow: "Sistema modular",
  title: "Gráficos que siguen el ritmo del video.",
  description:
    "Una plantilla reutilizable preparada para recibir contenido del futuro Beat Map.",
  metric: "10s",
  metricLabel: "primera prueba visual",
};

export const liquidGlassV2Demo: LiquidGlassCardV2Props = {
  eyebrow: "Componente V2",
  title: "Una capa viva, preparada para cada escena.",
  description:
    "Contraste controlado, luz dinámica y dos modos de render para integrarse con el flujo de CapCut.",
  metric: "V2",
  metricLabel: "overlay listo para producción",
  actionLabel: "Explorar",
  renderMode: "embedded",
  variant: "regular",
  contrast: "dark",
  reducedMotion: false,
};

export const animatedSearchDemo: AnimatedSearchBarProps = {
  label: "Búsqueda asistida",
  mistypedQuery: "motion grafics",
  correctedQuery: "motion graphics",
  resultLabel: "3 componentes relacionados",
  suggestions: ["Tarjetas", "Contadores", "Overlays"],
  renderMode: "embedded",
  reducedMotion: false,
};

export const newsHighlighterDemo: NewsTextHighlighterProps = {
  category: "Tecnología",
  source: "Minthy Brief · Edición 01",
  timestamp: "Ahora · 02:14",
  headline: [
    { text: "La edición con IA" },
    { text: "reduce el trabajo", highlighted: true },
    { text: "repetitivo." },
  ],
  summary:
    "El editor conserva la decisión creativa mientras automatiza cortes, ritmo y gráficos recurrentes.",
  renderMode: "embedded",
  reducedMotion: false,
};

export const dynamicCounterDemo: DynamicNumberCounterProps = {
  label: "Tiempo ahorrado",
  startValue: 0,
  endValue: 38,
  suffix: "%",
  decimals: 0,
  trendLabel: "+12% esta semana",
  supportingText: "Tareas repetitivas resueltas por el flujo automático.",
  trend: "up",
  renderMode: "embedded",
  reducedMotion: false,
};
