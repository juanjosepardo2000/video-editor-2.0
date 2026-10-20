export function relativeLuminance(color: string): number;
export function contrastRatio(foreground: string, background: string): number;
export function ensureTextContrast(color: string, background: string, minimum?: number): string;
export function readableTextOn(background: string): "#FFFFFF" | "#000000";
