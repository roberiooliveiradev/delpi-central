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

/** Gera 6 tons a partir de uma cor-base (estilo PowerPoint). */
export function buildThemeColorColumn(base: string): string[] {
  const hex = normalizeHex(base);
  const { r, g, b } = hexToRgb(hex);
  const luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;

  // Branco (e quase-branco): misturar com branco não muda a cor — usar escala de cinzas.
  if (luminance >= 0.97) {
    return [
      hex,
      mixWithBlack(hex, 0.08),
      mixWithBlack(hex, 0.18),
      mixWithBlack(hex, 0.35),
      mixWithBlack(hex, 0.5),
      mixWithBlack(hex, 0.65),
    ];
  }

  // Preto (e quase-preto): misturar com preto não muda — clarear com branco.
  if (luminance <= 0.03) {
    return [
      hex,
      mixWithWhite(hex, 0.35),
      mixWithWhite(hex, 0.5),
      mixWithWhite(hex, 0.65),
      mixWithWhite(hex, 0.8),
      mixWithWhite(hex, 0.9),
    ];
  }

  return [
    hex,
    mixWithWhite(hex, 0.2),
    mixWithWhite(hex, 0.4),
    mixWithWhite(hex, 0.6),
    mixWithBlack(hex, 0.25),
    mixWithBlack(hex, 0.5),
  ];
}

/** Gera 6 linhas × N colunas (estilo PowerPoint) a partir das cores-base do tema. */
export function buildThemeColorGrid(baseColors: readonly string[]): string[][] {
  return baseColors
    .map((base) => buildThemeColorColumn(base))
    .reduce<string[][]>((rows, column) => {
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

export type HsvColor = { h: number; s: number; v: number };

export function rgbToHsv(r: number, g: number, b: number): HsvColor {
  const rn = clampByte(r) / 255;
  const gn = clampByte(g) / 255;
  const bn = clampByte(b) / 255;
  const max = Math.max(rn, gn, bn);
  const min = Math.min(rn, gn, bn);
  const d = max - min;
  let h = 0;
  if (d !== 0) {
    switch (max) {
      case rn:
        h = ((gn - bn) / d + (gn < bn ? 6 : 0)) * 60;
        break;
      case gn:
        h = ((bn - rn) / d + 2) * 60;
        break;
      default:
        h = ((rn - gn) / d + 4) * 60;
        break;
    }
  }
  const s = max === 0 ? 0 : d / max;
  return { h, s, v: max };
}

export function hsvToRgb(h: number, s: number, v: number): { r: number; g: number; b: number } {
  const hh = ((h % 360) + 360) % 360;
  const sat = Math.min(1, Math.max(0, s));
  const val = Math.min(1, Math.max(0, v));
  const c = val * sat;
  const x = c * (1 - Math.abs(((hh / 60) % 2) - 1));
  const m = val - c;
  let rp = 0;
  let gp = 0;
  let bp = 0;
  if (hh < 60) {
    rp = c;
    gp = x;
  } else if (hh < 120) {
    rp = x;
    gp = c;
  } else if (hh < 180) {
    gp = c;
    bp = x;
  } else if (hh < 240) {
    gp = x;
    bp = c;
  } else if (hh < 300) {
    rp = x;
    bp = c;
  } else {
    rp = c;
    bp = x;
  }
  return {
    r: clampByte((rp + m) * 255),
    g: clampByte((gp + m) * 255),
    b: clampByte((bp + m) * 255),
  };
}

export function colorValueToHsv(color: ColorValue): HsvColor {
  const { r, g, b } = hexToRgb(color.hex);
  return rgbToHsv(r, g, b);
}

export function hsvToColorValue(hsv: HsvColor, alpha: number): ColorValue {
  const { r, g, b } = hsvToRgb(hsv.h, hsv.s, hsv.v);
  return { hex: rgbToHex(r, g, b), alpha: clampAlpha(alpha) };
}

export function hueToHex(h: number): string {
  const { r, g, b } = hsvToRgb(h, 1, 1);
  return rgbToHex(r, g, b);
}

/** Luminância relativa WCAG (0–1) a partir de hex. */
export function relativeLuminance(hex: string): number {
  const { r, g, b } = hexToRgb(hex);
  const channel = (value: number) => {
    const s = value / 255;
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  };
  return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b);
}

/**
 * Cor de texto «Automático»: preto em fundo claro, branco em fundo escuro.
 * Fundo transparente / quase transparente assume claro (preto).
 */
export function resolveAutomaticTextColor(background?: string | null): "#000000" | "#ffffff" {
  const bg = cssToColorValue(background ?? "#ffffff", "#ffffff");
  if (bg.alpha < 0.45) {
    return "#000000";
  }
  return relativeLuminance(bg.hex) >= 0.45 ? "#000000" : "#ffffff";
}
