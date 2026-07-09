import type { CSSProperties } from "react";
import type ExcelJS from "exceljs";

const THEME_COLORS = [
  "#FFFFFF",
  "#000000",
  "#E7E6E6",
  "#44546A",
  "#4472C4",
  "#ED7D31",
  "#A5A5A5",
  "#FFC000",
  "#5B9BD5",
  "#70AD47",
];

const BORDER_WIDTH: Record<string, string> = {
  hair: "1px",
  thin: "1px",
  medium: "2px",
  thick: "3px",
  double: "3px",
  dotted: "1px",
  dashed: "1px",
  dashDot: "1px",
  dashDotDot: "1px",
  slantDashDot: "1px",
};

function applyTint(hex: string, tint = 0): string {
  if (!tint) return hex;

  const normalized = hex.replace("#", "");
  if (normalized.length !== 6) return hex;

  const channels = [0, 2, 4].map((offset) => parseInt(normalized.slice(offset, offset + 2), 16));
  const adjusted = channels.map((channel) => {
    if (tint < 0) return Math.round(channel * (1 + tint));
    return Math.round(channel + (255 - channel) * tint);
  });

  return `rgb(${adjusted.join(", ")})`;
}

export function excelColorToCss(color?: Partial<ExcelJS.Color>): string | undefined {
  if (!color) return undefined;

  if (color.argb) {
    const argb = color.argb.replace(/^FF/i, "");
    if (argb.length === 6) return `#${argb.toUpperCase()}`;
    if (argb.length === 8) {
      const alpha = parseInt(argb.slice(0, 2), 16) / 255;
      const red = parseInt(argb.slice(2, 4), 16);
      const green = parseInt(argb.slice(4, 6), 16);
      const blue = parseInt(argb.slice(6, 8), 16);
      if (alpha < 1) return `rgba(${red}, ${green}, ${blue}, ${alpha.toFixed(3)})`;
      return `rgb(${red}, ${green}, ${blue})`;
    }
  }

  if (color.theme != null) {
    const base = THEME_COLORS[color.theme] ?? "#000000";
    const tint = "tint" in color && typeof color.tint === "number" ? color.tint : 0;
    return applyTint(base, tint);
  }

  return undefined;
}

function borderSideToCss(side?: Partial<ExcelJS.Border>): string | undefined {
  if (!side?.style) return undefined;
  const width = BORDER_WIDTH[side.style] ?? "1px";
  const color = excelColorToCss(side.color) ?? "#bfbfbf";
  return `${width} solid ${color}`;
}

export function excelCellStyleToCss(cell: ExcelJS.Cell): CSSProperties {
  const style: CSSProperties = {};
  const font = cell.font;

  if (font) {
    if (font.bold) style.fontWeight = "700";
    if (font.italic) style.fontStyle = "italic";
    if (font.underline && font.strike) style.textDecoration = "underline line-through";
    else if (font.underline) style.textDecoration = "underline";
    else if (font.strike) style.textDecoration = "line-through";
    if (font.size) style.fontSize = `${font.size}pt`;
    if (font.name) style.fontFamily = `"${font.name}", Calibri, "Segoe UI", sans-serif`;
    const color = excelColorToCss(font.color);
    if (color) style.color = color;
  }

  const fill = cell.fill;
  if (fill && fill.type === "pattern") {
    const background = excelColorToCss(fill.fgColor) ?? excelColorToCss(fill.bgColor);
    if (background) style.backgroundColor = background;
  } else if (fill && fill.type === "gradient") {
    const stop = fill.stops?.[0]?.color;
    const background = excelColorToCss(stop);
    if (background) style.backgroundColor = background;
  }

  const alignment = cell.alignment;
  if (alignment) {
    if (alignment.horizontal) {
      style.textAlign = alignment.horizontal as CSSProperties["textAlign"];
    }
    if (alignment.vertical) {
      const verticalMap: Record<string, CSSProperties["verticalAlign"]> = {
        top: "top",
        middle: "middle",
        bottom: "bottom",
      };
      style.verticalAlign = verticalMap[alignment.vertical] ?? "bottom";
    }
    if (alignment.wrapText) {
      style.whiteSpace = "pre-wrap";
      style.wordBreak = "break-word";
    }
    if (alignment.indent) {
      style.paddingLeft = `${8 + alignment.indent * 10}px`;
    }
  }

  const border = cell.border;
  if (border) {
    const top = borderSideToCss(border.top);
    const right = borderSideToCss(border.right);
    const bottom = borderSideToCss(border.bottom);
    const left = borderSideToCss(border.left);
    if (top) style.borderTop = top;
    if (right) style.borderRight = right;
    if (bottom) style.borderBottom = bottom;
    if (left) style.borderLeft = left;
  }

  return style;
}

export function excelColumnWidthToPx(width?: number): number | undefined {
  if (!width || width <= 0) return undefined;
  return Math.max(24, Math.round(width * 7.5));
}

export function excelRowHeightToPx(height?: number): number | undefined {
  if (!height || height <= 0) return undefined;
  return Math.max(18, Math.round(height * 1.33));
}
