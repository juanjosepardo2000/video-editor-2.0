const HEX_COLOR = /^#([\da-f]{6})$/i;

const parseHex = (color) => {
  const match = color.trim().match(HEX_COLOR);
  if (!match) throw new Error(`Color hexadecimal no compatible: "${color}".`);
  return [0, 2, 4].map((offset) => Number.parseInt(match[1].slice(offset, offset + 2), 16));
};

const toHex = (channels) =>
  `#${channels.map((channel) => Math.round(channel).toString(16).padStart(2, "0")).join("").toUpperCase()}`;

const linearChannel = (channel) => {
  const value = channel / 255;
  return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
};

export const relativeLuminance = (color) => {
  const [red, green, blue] = parseHex(color).map(linearChannel);
  return 0.2126 * red + 0.7152 * green + 0.0722 * blue;
};

export const contrastRatio = (foreground, background) => {
  const light = Math.max(relativeLuminance(foreground), relativeLuminance(background));
  const dark = Math.min(relativeLuminance(foreground), relativeLuminance(background));
  return (light + 0.05) / (dark + 0.05);
};

const mix = (color, target, amount) => {
  const sourceChannels = parseHex(color);
  const targetChannels = parseHex(target);
  return toHex(sourceChannels.map((channel, index) => channel + (targetChannels[index] - channel) * amount));
};

/**
 * Conserva el color del perfil si ya es legible. De lo contrario, cambia solo
 * su luminosidad, hacia blanco o negro, hasta alcanzar el contraste pedido.
 */
export const ensureTextContrast = (color, background, minimum = 4.5) => {
  if (contrastRatio(color, background) >= minimum) return color.toUpperCase();

  const candidates = ["#FFFFFF", "#000000"]
    .map((target) => {
      for (let step = 1; step <= 100; step += 1) {
        const candidate = mix(color, target, step / 100);
        if (contrastRatio(candidate, background) >= minimum) return { candidate, step };
      }
      return { candidate: target, step: 100 };
    })
    .sort((left, right) => left.step - right.step);

  return candidates[0].candidate;
};

export const readableTextOn = (background) =>
  contrastRatio("#FFFFFF", background) >= contrastRatio("#000000", background) ? "#FFFFFF" : "#000000";
