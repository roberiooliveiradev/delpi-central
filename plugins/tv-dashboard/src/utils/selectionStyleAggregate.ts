import type { TextFormatStyleSnapshot } from "./selectedTextFormatTarget";
import { aggregateEqualValues, type AggregatedValue } from "./selectionSectionIntersect";
import {
  defaultStyle,
  isComunicadoVisualBoxBlock,
  type ComunicadoBlock,
  type ComunicadoBlockStyle,
} from "@delpi/tv-dashboard-presentation";

export type { AggregatedValue } from "./selectionSectionIntersect";
export { aggregateEqualValues } from "./selectionSectionIntersect";

function snapshotFromVisualBox(block: ComunicadoBlock): TextFormatStyleSnapshot | null {
  if (!isComunicadoVisualBoxBlock(block)) return null;
  const type = block.type === "heading" || block.type === "text" ? block.type : "shape";
  const defaults =
    type === "shape" ? defaultStyle("shape", block.shape) : defaultStyle(type);
  return {
    fontFamily: block.style?.fontFamily,
    fontSize: block.style?.fontSize ?? defaults.fontSize,
    fontWeight: block.style?.fontWeight,
    fontStyle: block.style?.fontStyle,
    color: block.style?.color,
    textDecoration: block.style?.textDecoration,
    textHighlight: block.style?.textHighlight,
    textAlign: block.style?.textAlign,
    verticalAlign: block.style?.verticalAlign,
    textShadow: block.style?.textShadow,
    textStrokeColor: block.style?.textStrokeColor,
    textStrokeWidth: block.style?.textStrokeWidth,
    textReflection: block.style?.textReflection,
  };
}

export type AggregatedTextFormatStyle = {
  [K in keyof TextFormatStyleSnapshot]?: AggregatedValue<
    NonNullable<TextFormatStyleSnapshot[K]>
  >;
};

/** Agrega tipografia de vários visual-box; null se a seleção não for só visual-box. */
export function aggregateVisualBoxTextFormatStyle(
  blocks: readonly ComunicadoBlock[],
): AggregatedTextFormatStyle | null {
  const snapshots = blocks.map((block) => snapshotFromVisualBox(block));
  if (snapshots.length === 0 || snapshots.some((item) => item == null)) return null;
  const list = snapshots as TextFormatStyleSnapshot[];
  const keys: Array<keyof TextFormatStyleSnapshot> = [
    "fontFamily",
    "fontSize",
    "fontWeight",
    "fontStyle",
    "color",
    "textDecoration",
    "textHighlight",
    "textAlign",
    "verticalAlign",
    "textShadow",
    "textStrokeColor",
    "textStrokeWidth",
    "textReflection",
  ];
  const out: AggregatedTextFormatStyle = {};
  for (const key of keys) {
    const values = list
      .map((snap) => snap[key])
      .filter((value): value is NonNullable<TextFormatStyleSnapshot[typeof key]> => value != null);
    if (values.length === 0) continue;
    if (values.length !== list.length) {
      out[key] = "mixed" as never;
      continue;
    }
    out[key] = aggregateEqualValues(values) as never;
  }
  return out;
}

export function aggregateStyleField<K extends keyof ComunicadoBlockStyle>(
  blocks: readonly ComunicadoBlock[],
  key: K,
  resolve: (block: ComunicadoBlock) => ComunicadoBlockStyle[K] | undefined,
): AggregatedValue<NonNullable<ComunicadoBlockStyle[K]>> | undefined {
  const values = blocks
    .map((block) => resolve(block))
    .filter((value): value is NonNullable<ComunicadoBlockStyle[K]> => value != null);
  if (values.length === 0) return undefined;
  if (values.length !== blocks.length) return "mixed";
  return aggregateEqualValues(values);
}

/** True quando a seleção multi é só caixas visuais (texto/título/forma). */
export function isHomogeneousVisualBoxSelection(
  blocks: readonly ComunicadoBlock[],
): boolean {
  return blocks.length > 0 && blocks.every((block) => isComunicadoVisualBoxBlock(block));
}
