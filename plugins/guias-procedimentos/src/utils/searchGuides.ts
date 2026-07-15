import type { GuideDocument, GuideSummary } from "../types/guide";

/** Normaliza caixa e remove diacríticos para busca local. */
export function normalizeSearchText(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

function guideSearchBlob(guide: GuideDocument, departmentName: string): string {
  const parts = [
    guide.meta.title,
    guide.meta.summary,
    departmentName,
    guide.meta.responsibleArea,
    ...guide.meta.tags,
    guide.introduction,
    ...guide.sections.flatMap((section) => [
      section.title,
      ...section.items.map((item) => item.text),
    ]),
    ...guide.checklist.map((item) => item.label),
  ];
  return normalizeSearchText(parts.join(" "));
}

/**
 * Filtra guias publicados pelo texto de busca (título, resumo, departamento, tags e seções).
 * A busca é global — não restringe ao departamento selecionado.
 */
export function filterGuidesByQuery(
  guides: GuideDocument[],
  summariesById: Map<string, GuideSummary>,
  query: string,
): GuideDocument[] {
  const normalizedQuery = normalizeSearchText(query);
  if (!normalizedQuery) return guides;

  const terms = normalizedQuery.split(/\s+/).filter(Boolean);

  return guides.filter((guide) => {
    const summary = summariesById.get(guide.meta.id);
    const blob = guideSearchBlob(guide, summary?.departmentName ?? "");
    return terms.every((term) => blob.includes(term));
  });
}
