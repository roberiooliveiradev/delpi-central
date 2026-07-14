import {
  applyBlockShapeChromeStyle,
  blockUsesInnerShapeChrome,
  isInnerShapeChromeStyleKey,
  type ComunicadoBlock,
  type ComunicadoBlockStyle,
  type ComunicadoInputPartRef,
} from "@delpi/tv-dashboard-presentation";

/**
 * Chaves opcionais que o patch pode remover com `undefined` / `null` / string vazia.
 * (Demais `undefined` no patch são ignorados para permitir patches parciais.)
 */
const CLEARABLE_STYLE_KEYS = new Set<string>(["boxShadow", "textShadow", "textStrokeColor", "textStrokeWidth"]);

function shouldClearStyleValue(key: string, value: unknown): boolean {
  if (!CLEARABLE_STYLE_KEYS.has(key)) return false;
  if (value === undefined || value === null) return true;
  return typeof value === "string" && value.trim() === "";
}

export type ApplyComunicadoBlockStylePatchOptions = {
  selectedInputPart?: ComunicadoInputPartRef | null;
};

/**
 * Aplica patch de estilo ao bloco: chrome interno (KPI/chart/tabela) + limpeza de sombra etc.
 */
export function applyComunicadoBlockStylePatch(
  block: ComunicadoBlock,
  patch: Partial<ComunicadoBlockStyle>,
  options?: ApplyComunicadoBlockStylePatchOptions,
): ComunicadoBlock {
  const chromePatch: Record<string, unknown> = {};
  const restPatch: Record<string, unknown> = {};
  const clearKeys: string[] = [];

  for (const [key, value] of Object.entries(patch)) {
    if (shouldClearStyleValue(key, value)) {
      clearKeys.push(key);
      continue;
    }
    if (value === undefined) continue;
    if (blockUsesInnerShapeChrome(block) && isInnerShapeChromeStyleKey(key)) {
      chromePatch[key] = value;
    } else {
      restPatch[key] = value;
    }
  }

  let next: ComunicadoBlock = block;
  if (Object.keys(chromePatch).length > 0) {
    const applied = applyBlockShapeChromeStyle(block, chromePatch, {
      selectedInputPart: options?.selectedInputPart,
    });
    if (applied) {
      next = { ...block, ...applied } as ComunicadoBlock;
    }
  }

  if (Object.keys(restPatch).length > 0 || clearKeys.length > 0) {
    const nextStyle: ComunicadoBlockStyle = { ...next.style, ...restPatch };
    for (const key of clearKeys) {
      delete nextStyle[key as keyof ComunicadoBlockStyle];
    }
    next = { ...next, style: nextStyle };
  }

  return next;
}
