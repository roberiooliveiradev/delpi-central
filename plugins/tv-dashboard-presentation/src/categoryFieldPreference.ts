/**
 * Preferência de campo de categoria e rótulo de exibição no gráfico.
 *
 * Rankings (ex.: refugos) expõem `code` + `label` separados.
 * - Motivo (sigla curta FM/FH): legenda pode mostrar «FM - Falha…».
 * - Matéria-prima / PA (código longo): eixo/legenda ficam **só no code**;
 *   a descrição permanece no campo `label` da linha (tooltip / tabela).
 */

const CODE_LIKE = new Set([
  "code",
  "codigo",
  "código",
  "id",
  "key",
  "reason_code",
  "motivocodigo",
]);

const LABEL_LIKE_ORDER = [
  "label",
  "description",
  "descricao",
  "descrição",
  "name",
  "nome",
  "motivo",
  "title",
  "titulo",
  "título",
] as const;

/** Códigos acima disso (ex.: 10070821) não recebem descrição no eixo. */
export const CATEGORY_CODE_ENRICH_MAX_LEN = 6;

/** Descrição longa demais (produto) não entra no rótulo do gráfico. */
export const CATEGORY_ENRICHED_LABEL_MAX_LEN = 40;

function normalizeFieldKey(field: string): string {
  return field.trim().toLowerCase();
}

function isCodeLikeField(field: string): boolean {
  const key = normalizeFieldKey(field);
  if (CODE_LIKE.has(key)) return true;
  return (
    key.endsWith("_code") ||
    key.endsWith("codigo") ||
    key.endsWith("_codigo") ||
    key.endsWith("código")
  );
}

/**
 * Score alto = melhor candidato a eixo/categoria.
 * Prefere `code` a `label` — descrição longa de MP/PA não vira categoria default.
 */
export function scoreCategoryFieldPreference(field: string): number {
  const key = normalizeFieldKey(field);
  if (isCodeLikeField(field)) return 150;
  const labelIdx = LABEL_LIKE_ORDER.indexOf(key as (typeof LABEL_LIKE_ORDER)[number]);
  if (labelIdx >= 0) return 100 - labelIdx;
  return 50;
}

/**
 * Entre campos string-like, prefere `code`/`codigo` a `label`/`name`.
 * Empate: mantém ordem de entrada.
 */
export function pickPreferredCategoryField(
  fields: ReadonlyArray<{ field: string }>,
): string | undefined {
  if (fields.length === 0) return undefined;
  let best = fields[0]!;
  let bestScore = scoreCategoryFieldPreference(best.field);
  for (let i = 1; i < fields.length; i += 1) {
    const item = fields[i]!;
    const score = scoreCategoryFieldPreference(item.field);
    if (score > bestScore) {
      best = item;
      bestScore = score;
    }
  }
  return best.field;
}

function companionLabelFields(categoryField: string): string[] {
  if (!isCodeLikeField(categoryField)) return [];
  return [...LABEL_LIKE_ORDER];
}

/**
 * Rótulo da fatia/barra: enriquece só siglas curtas (motivo).
 * Códigos de produto / descrições longas → mantém o `code` puro.
 */
export function resolveCategoryDisplayLabel(params: {
  categoryKey: string;
  categoryField: string;
  groupRows: ReadonlyArray<Record<string, unknown>>;
}): string {
  const { categoryKey, categoryField, groupRows } = params;
  if (categoryKey === "(vazio)" || categoryKey === "Outros") return categoryKey;
  if (categoryKey.length > CATEGORY_CODE_ENRICH_MAX_LEN) return categoryKey;

  for (const field of companionLabelFields(categoryField)) {
    for (const row of groupRows) {
      if (!(field in row)) continue;
      const raw = row[field];
      if (raw == null) continue;
      const text = String(raw).trim();
      if (!text) continue;
      if (text.toLowerCase() === categoryKey.toLowerCase()) continue;

      const enriched = text.toLowerCase().includes(categoryKey.toLowerCase())
        ? text
        : `${categoryKey} - ${text}`;
      if (enriched.length > CATEGORY_ENRICHED_LABEL_MAX_LEN) return categoryKey;
      return enriched;
    }
  }
  return categoryKey;
}
