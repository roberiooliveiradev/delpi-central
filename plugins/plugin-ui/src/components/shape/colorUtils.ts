import type { ColorValue } from "./types";

const HEX3 = /^#([0-9a-f]{3})$/i;
const HEX6 = /^#([0-9a-f]{6})$/i;

export function normalizeHex(input: string): string {
  const trimmed = input.trim();
  const short = trimmed.match(HEX3);
  if (short) {
    const [r, g, b] = short[1].split("");
    return `#${r}${r}${g}${g}${b}${b}`.toLowerCase();
  }
  const full = trimmed.match(HEX6);
  if (full) {
    return `#${full[1].toLowerCase()}`;
  }
  return "#000000";
}

export function parseHexColor(input: string, alpha = 1): ColorValue | null {
  const hex = normalizeHex(input);
  if (!HEX6.test(hex) && !HEX3.test(input.trim())) {
    return null;
  }
  return { hex, alpha: clampAlpha(alpha) };
}

export function clampAlpha(value: number): number {
  if (Number.isNaN(value)) return 1;
  return Math.min(1, Math.max(0, value));
}

export function clampByte(value: number): number {
  if (Number.isNaN(value)) return 0;
  return Math.min(255, Math.max(0, Math.round(value)));
}

export function hexToRgb(hex: string): { r: number; g: number; b: number } {
  const normalized = normalizeHex(hex);
  const match = normalized.match(HEX6);
  if (!match) {
    return { r: 0, g: 0, b: 0 };
  }
  const value = match[1];
  return {
    r: parseInt(value.slice(0, 2), 16),
    g: parseInt(value.slice(2, 4), 16),
    b: parseInt(value.slice(4, 6), 16),
  };
}

export function rgbToHex(r: number, g: number, b: number): string {
  const toPart = (channel: number) => clampByte(channel).toString(16).padStart(2, "0");
  return `#${toPart(r)}${toPart(g)}${toPart(b)}`;
}

export function colorToCss(color: ColorValue): string {
  const { r, g, b } = hexToRgb(color.hex);
  if (color.alpha >= 1) {
    return color.hex;
  }
  return `rgba(${r}, ${g}, ${b}, ${color.alpha.toFixed(3).replace(/\.?0+$/, "")})`;
}

export function cssToColorValue(input?: string | null, fallback = "#000000"): ColorValue {
  if (!input || input === "transparent") {
    return { hex: fallback, alpha: 0 };
  }
  const rgba = input.match(/^rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*([\d.]+))?\s*\)$/i);
  if (rgba) {
    return {
      hex: rgbToHex(Number(rgba[1]), Number(rgba[2]), Number(rgba[3])),
      alpha: rgba[4] !== undefined ? clampAlpha(Number(rgba[4])) : 1,
    };
  }
  const parsed = parseHexColor(input);
  return parsed ?? { hex: normalizeHex(fallback), alpha: 1 };
}

function mixChannel(base: number, target: number, ratio: number): number {
  return clampByte(base + (target - base) * ratio);
}

export function mixWithWhite(hex: string, ratio: number): string {
  const { r, g, b } = hexToRgb(hex);
  return rgbToHex(mixChannel(r, 255, ratio), mixChannel(g, 255, ratio), mixChannel(b, 255, ratio));
}

export function mixWithBlack(hex: string, ratio: number): string {
  const { r, g, b } = hexToRgb(hex);
  return rgbToHex(mixChannel(r, 0, ratio), mixChannel(g, 0, ratio), mixChannel(b, 0, ratio));
}

/** Gera 6 linhas × N colunas (estilo PowerPoint) a partir das cores-base do tema. */
export function buildThemeColorGrid(baseColors: readonly string[]): string[][] {
  return baseColors.map((base) => [
    base,
    mixWithWhite(base, 0.2),
    mixWithWhite(base, 0.4),
    mixWithWhite(base, 0.6),
    mixWithBlack(base, 0.25),
    mixWithBlack(base, 0.5),
  ]).reduce<string[][]>((rows, column) => {
    column.forEach((color, rowIndex) => {
      if (!rows[rowIndex]) rows[rowIndex] = [];
      rows[rowIndex].push(color);
    });
    return rows;
  }, []);
}

export function colorsEqual(a: ColorValue, b: ColorValue): boolean {
  return normalizeHex(a.hex) === normalizeHex(b.hex) && Math.abs(a.alpha - b.alpha) < 0.01;
}
