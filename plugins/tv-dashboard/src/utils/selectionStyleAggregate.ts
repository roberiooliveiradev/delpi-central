import type { TextFormatStyleSnapshot } from "./selectedTextFormatTarget";
import { aggregateEqualValues, type AggregatedValue } from "./selectionSectionIntersect";
import {
  isComunicadoVisualBoxBlock,
  resolveVisualBoxEffectiveTextFormatSnapshot,
  type ComunicadoBlock,
  type ComunicadoBlockStyle,
} from "@delpi/tv-dashboard-presentation";

export type { AggregatedValue } from "./selectionSectionIntersect";
export { aggregateEqualValues } from "./selectionSectionIntersect";

function snapshotFromVisualBox(block: ComunicadoBlock): TextFormatStyleSnapshot | null {
  if (!isComunicadoVisualBoxBlock(block)) return null;
  return resolveVisualBoxEffectiveTextFormatSnapshot(block);
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
