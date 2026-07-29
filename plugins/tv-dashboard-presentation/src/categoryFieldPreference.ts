/**
 * Preferência de campo de categoria e rótulo de exibição no gráfico.
 *
 * Rankings (ex.: refugos) expõem `code` + `label` («FM» / «FM - Falha de material»).
 * Sem esta regra, o default pegava o 1º string (`code`) e a legenda ficava só na sigla.
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

/** Score alto = melhor candidato a eixo/categoria (legenda legível). */
export function scoreCategoryFieldPreference(field: string): number {
  const key = normalizeFieldKey(field);
  const labelIdx = LABEL_LIKE_ORDER.indexOf(key as (typeof LABEL_LIKE_ORDER)[number]);
  if (labelIdx >= 0) return 200 - labelIdx;
  if (isCodeLikeField(field)) return 10;
  return 50;
}

/**
 * Entre campos string-like, prefere `label`/`name`/… a `code`/`codigo`.
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
 * Rótulo da fatia/barra na legenda: se a categoria é código e a linha tem
 * descrição mais rica, usa a descrição (já «SIGLA - significado» quando a API manda).
 */
export function resolveCategoryDisplayLabel(params: {
  categoryKey: string;
  categoryField: string;
  groupRows: ReadonlyArray<Record<string, unknown>>;
}): string {
  const { categoryKey, categoryField, groupRows } = params;
  if (categoryKey === "(vazio)" || categoryKey === "Outros") return categoryKey;

  for (const field of companionLabelFields(categoryField)) {
    for (const row of groupRows) {
      if (!(field in row)) continue;
      const raw = row[field];
      if (raw == null) continue;
      const text = String(raw).trim();
      if (!text) continue;
      if (text.toLowerCase() === categoryKey.toLowerCase()) continue;
      // API já montou «FM - Falha…» ou só a descrição.
      if (text.toLowerCase().includes(categoryKey.toLowerCase())) return text;
      return `${categoryKey} - ${text}`;
    }
  }
  return categoryKey;
}
