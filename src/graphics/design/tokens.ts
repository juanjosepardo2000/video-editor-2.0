export const colors = {
  background: "#07110F",
  foreground: "#F4FBF8",
  mutedForeground: "#B8C9C3",
  primary: "#62E6B8",
  primaryForeground: "#062019",
  card: "rgba(7, 17, 15, 0.82)",
  cardStrong: "rgba(18, 42, 35, 0.9)",
  border: "rgba(235, 255, 248, 0.26)",
  shadow: "rgba(0, 0, 0, 0.32)",
} as const;

export const typography = {
  family: "Inter, Arial, sans-serif",
  eyebrow: 24,
  body: 32,
  title: 64,
  metric: 108,
} as const;

export const spacing = {
  xs: 8,
  sm: 16,
  md: 24,
  lg: 32,
  xl: 48,
  xxl: 64,
} as const;

export const radii = {
  sm: 16,
  md: 24,
  lg: 36,
  full: 999,
} as const;

export const safeArea = {
  top: 150,
  right: 120,
  bottom: 380,
  left: 60,
} as const;
