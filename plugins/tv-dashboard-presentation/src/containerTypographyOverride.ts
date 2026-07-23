import { compactContentRuns } from "./comunicadoContentRunEditing";
import { plainTextFromContentRuns } from "./comunicadoContentRuns";
import type {
  ComunicadoContentRun,
  ComunicadoContentRunStyle,
} from "./comunicadoTypes";

/** Chaves de tipografia que o estilo do container pode invalidar nos runs. */
export type ContainerTypographyStyleKey =
  | "fontWeight"
  | "fontStyle"
  | "textDecoration"
  | "fontFamily"
  | "fontSize"
  | "color"
  | "textHighlight";

const CONTAINER_TYPOGRAPHY_KEYS: readonly ContainerTypographyStyleKey[] = [
  "fontWeight",
  "fontStyle",
  "textDecoration",
  "fontFamily",
  "fontSize",
  "color",
  "textHighlight",
] as const;

function prunePartialRunStyle(
  style: ComunicadoContentRunStyle,
): ComunicadoContentRunStyle | undefined {
  const cleaned: ComunicadoContentRunStyle = {};
  if (style.fontSize != null && Number.isFinite(style.fontSize)) cleaned.fontSize = style.fontSize;
  if (style.color?.trim()) cleaned.color = style.color.trim();
  if (style.fontFamily?.trim()) cleaned.fontFamily = style.fontFamily.trim();
  if (style.textHighlight?.trim() && style.textHighlight !== "transparent") {
    cleaned.textHighlight = style.textHighlight.trim();
  }
  if (style.fontWeight === "bold" || style.fontWeight === "normal") {
    cleaned.fontWeight = style.fontWeight;
  }
  if (style.fontStyle === "italic" || style.fontStyle === "normal") {
    cleaned.fontStyle = style.fontStyle;
  }
  if (
    style.textDecoration === "underline" ||
    style.textDecoration === "line-through" ||
    style.textDecoration === "underline line-through"
  ) {
    cleaned.textDecoration = style.textDecoration;
  }
  if (style.listType === "bullet" || style.listType === "ordered") {
    cleaned.listType = style.listType;
  }
  if (
    style.namedStyle === "title1" ||
    style.namedStyle === "subtitle" ||
    style.namedStyle === "body"
  ) {
    cleaned.namedStyle = style.namedStyle;
  }
  if (style.lineHeight != null && Number.isFinite(style.lineHeight)) {
    cleaned.lineHeight = style.lineHeight;
  }
  return Object.keys(cleaned).length > 0 ? cleaned : undefined;
}

/**
 * Quais chaves tipográficas o patch do container está definindo
 * (só essas são removidas dos contentRuns).
 */
export function typographyKeysFromContainerPatch(
  patch: Record<string, unknown>,
): ContainerTypographyStyleKey[] {
  return CONTAINER_TYPOGRAPHY_KEYS.filter((key) => key in patch);
}

/**
 * Seleção cobrindo todo o texto plano do bloco (= tipografia de container).
 */
export function isFullContentTextSelection(
  runs: ComunicadoContentRun[] | undefined,
  content: string | undefined,
  start: number,
  end: number,
): boolean {
  const plain =
    runs && runs.length > 0
      ? plainTextFromContentRuns(runs)
      : String(content ?? "");
  const length = plain.length;
  if (length <= 0) return false;
  return start <= 0 && end >= length;
}

/**
 * Tipografia do container sobrepõe a pontual: remove do run as chaves
 * alteradas no bloco para o CSS do container voltar a mandar.
 * Preserva `dataRef` e demais estilos de caractere.
 */
export function stripContentRunStylesOverriddenByContainer(
  runs: ComunicadoContentRun[] | undefined,
  keys: readonly ContainerTypographyStyleKey[],
): ComunicadoContentRun[] | undefined {
  if (!runs?.length || keys.length === 0) return runs;
  const keySet = new Set(keys);
  const next = runs.map((run) => {
    if (!run.style) return run;
    const style: ComunicadoContentRunStyle = { ...run.style };
    for (const key of keySet) {
      delete style[key];
    }
    const pruned = prunePartialRunStyle(style);
    if (!pruned) {
      const { style: _removed, ...rest } = run;
      return rest;
    }
    return { ...run, style: pruned };
  });
  return compactContentRuns(next);
}
