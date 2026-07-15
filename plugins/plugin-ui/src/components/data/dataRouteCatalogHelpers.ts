export type DataRouteParamFieldSummary = {
  key: string;
  label: string;
  optional?: boolean;
  description?: string;
};

const META_SHAPE_BLURB: Record<string, string> = {
  scalar: "Entrega um número indicador — ideal para card KPI na TV.",
  paged_list: "Entrega uma lista paginada — ideal para tabela na TV.",
  list: "Entrega uma lista de itens — ideal para tabela na TV.",
  playbook_report: "Entrega relatório operacional (série, painéis ou resumo).",
  composite_analysis: "Entrega vários painéis juntos (análise composta).",
  hierarchy: "Entrega dados em árvore ou hierarquia.",
  product_snapshot: "Entrega uma ficha / snapshot de produto.",
  object: "Entrega um objeto estruturado com vários campos.",
  document_export: "Entrega ou prepara documento para exportação.",
};

const META_SHAPE_SHORT: Record<string, string> = {
  scalar: "Indicador (KPI)",
  paged_list: "Lista / tabela",
  list: "Lista",
  playbook_report: "Relatório / série",
  composite_analysis: "Painéis compostos",
  hierarchy: "Hierarquia",
  product_snapshot: "Ficha",
  object: "Objeto",
  document_export: "Documento",
};

export function isParamFieldOptional(field: {
  optional?: boolean;
  required?: boolean;
}): boolean {
  if (typeof field.required === "boolean") return !field.required;
  if (typeof field.optional === "boolean") return field.optional;
  return true;
}

/** Monta resumo amigável de params a partir do paramSchema da rota. */
export function summarizeRouteParams(
  paramSchema?: Record<string, unknown> | null,
  fixedQueryParams?: Record<string, unknown> | null,
): DataRouteParamFieldSummary[] {
  if (!paramSchema || typeof paramSchema !== "object") return [];
  const fixed = new Set(Object.keys(fixedQueryParams ?? {}));
  const items: DataRouteParamFieldSummary[] = [];
  for (const [key, raw] of Object.entries(paramSchema)) {
    if (fixed.has(key)) continue;
    if (!raw || typeof raw !== "object") {
      items.push({ key, label: key, optional: true });
      continue;
    }
    const field = raw as {
      label?: string;
      description?: string;
      optional?: boolean;
      required?: boolean;
    };
    items.push({
      key,
      label: typeof field.label === "string" && field.label.trim() ? field.label.trim() : key,
      optional: isParamFieldOptional(field),
      description:
        typeof field.description === "string" && field.description.trim()
          ? field.description.trim()
          : undefined,
    });
  }
  return items.sort((a, b) => {
    if (a.optional === b.optional) return a.label.localeCompare(b.label, "pt-BR");
    return a.optional ? 1 : -1;
  });
}

export function countRequiredParams(params: DataRouteParamFieldSummary[]): number {
  return params.filter((param) => param.optional === false).length;
}

/** Linha curta no card: «3 filtros · 1 obrigatório». */
export function formatParamHintLine(params: DataRouteParamFieldSummary[]): string | null {
  if (params.length === 0) return "Sem filtros";
  const required = countRequiredParams(params);
  const total = params.length;
  const filterWord = total === 1 ? "filtro" : "filtros";
  if (required === 0) return `${total} ${filterWord}`;
  if (required === total) {
    return `${total} ${filterWord} · ${required === 1 ? "obrigatório" : "obrigatórios"}`;
  }
  return `${total} ${filterWord} · ${required} obrigatório${required === 1 ? "" : "s"}`;
}

export function humanizeMetaShape(metaShape?: string | null): string | null {
  if (!metaShape?.trim()) return null;
  return META_SHAPE_SHORT[metaShape] ?? metaShape;
}

export function isTemplatedRouteDescription(description: string): boolean {
  const trimmed = description.trim();
  return (
    /^Indicador numérico para «.+»\.?$/u.test(trimmed) ||
    /^Listagem paginada de «.+»/u.test(trimmed)
  );
}

/** Texto «para que serve» — whenToUse > description útil > fallback pelo shape. */
export function resolveRouteAudienceDescription(item: {
  whenToUse?: string | null;
  description?: string | null;
  metaShape?: string | null;
}): string {
  const whenToUse = item.whenToUse?.trim();
  if (whenToUse) return whenToUse;
  const description = item.description?.trim();
  if (description && !isTemplatedRouteDescription(description)) return description;
  const shape = item.metaShape?.trim();
  if (shape && META_SHAPE_BLURB[shape]) return META_SHAPE_BLURB[shape];
  if (description) return description;
  return "Fonte de dados da api-delpi para montar KPI, gráfico ou tabela na TV.";
}

export function truncateText(text: string, maxLength: number): string {
  const trimmed = text.trim();
  if (trimmed.length <= maxLength) return trimmed;
  return `${trimmed.slice(0, maxLength - 1).trim()}…`;
}
