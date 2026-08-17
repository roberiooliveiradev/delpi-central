import { CLEARABLE_STYLE_KEYS } from "./applyComunicadoBlockStylePatch";

/**
 * Aplicação centralizada de propriedades na seleção do editor.
 *
 * Contrato:
 * - Patch **esparso**: só chaves definidas entram no merge (nunca espalhar `undefined`
 *   — isso apagava cor/peso/tamanho ao mudar só a família).
 * - Numéricos em multi-alvo (`complexGlobal`, multi-bloco):
 *   - `absolute` — mesmo valor em todos (input / lista)
 *   - `delta` — soma o passo em cada alvo (preserva hierarquia tipográfica)
 */

export type SelectionNumericApplyMode = "absolute" | "delta";

export type SelectionPropertyApplyOptions = {
  fontSizeMode?: SelectionNumericApplyMode;
  /** Usado quando `fontSizeMode === "delta"` (ex.: ± COMUNICADO_FONT_SIZE_STEP). */
  fontSizeDelta?: number;
};

/**
 * Remove `undefined` — exceto chaves clearable (`fillPaint`, sombra…),
 * onde `undefined` significa apagar no `applyComunicadoBlockStylePatch`.
 */
export function sparsePropertyPatch<T extends Record<string, unknown>>(
  patch: T,
): Partial<T> {
  const out: Partial<T> = {};
  for (const [key, value] of Object.entries(patch)) {
    if (value !== undefined || CLEARABLE_STYLE_KEYS.has(key)) {
      (out as Record<string, unknown>)[key] = value;
    }
  }
  return out;
}

/**
 * Resolve o próximo valor numérico por alvo.
 * - delta: `clamp(current + delta)`
 * - absolute / default: `clamp(value)` quando value é número
 */
export function resolveAppliedNumericProperty(params: {
  current: number;
  value?: number;
  mode?: SelectionNumericApplyMode;
  delta?: number;
  clamp: (n: number) => number;
}): number | undefined {
  const { current, value, mode, delta, clamp } = params;
  if (mode === "delta" && typeof delta === "number" && Number.isFinite(delta)) {
    return clamp(current + delta);
  }
  if (typeof value === "number" && Number.isFinite(value)) {
    return clamp(value);
  }
  return undefined;
}

/**
 * Merge de estilo de parte/bloco: só sobrescreve chaves presentes no patch esparso.
 * Não reintroduz `undefined` (compatível com upsert chart/input que espalham o objeto).
 */
export function mergeSparseStyleProperties<T extends Record<string, unknown>>(
  prev: T | null | undefined,
  patch: Partial<T>,
): T {
  const sparse = sparsePropertyPatch(patch as Record<string, unknown>) as Partial<T>;
  const next = { ...(prev ?? ({} as T)), ...sparse };
  for (const key of CLEARABLE_STYLE_KEYS) {
    if (
      Object.prototype.hasOwnProperty.call(sparse, key) &&
      (sparse as Record<string, unknown>)[key] === undefined
    ) {
      delete (next as Record<string, unknown>)[key];
    }
  }
  return next;
}
