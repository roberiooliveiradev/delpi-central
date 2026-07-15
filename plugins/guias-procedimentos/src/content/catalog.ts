import type {
  Department,
  DepartmentSummary,
  GuideDocument,
  GuideSummary,
  GuidesCatalog,
} from "../types/guide";
import { EMISSAO_NOTA_FISCAL_GUIDE } from "./guides/emissao-nota-fiscal";

/** Catálogo local V1 — único ponto de índice para listagem e busca. */
export const GUIDES_CATALOG: GuidesCatalog = {
  departments: [
    {
      id: "faturamento",
      name: "Faturamento",
      slug: "faturamento",
      icon: "receipt",
      description:
        "Consulte os procedimentos e orientações do setor de Faturamento.",
      order: 1,
    },
  ],
  guides: [EMISSAO_NOTA_FISCAL_GUIDE],
};

export const MODULE_TITLE = "Guias e Procedimentos";

export const MODULE_INTRO =
  "Consulte e relembre orientações práticas do dia a dia. Novos guias poderão ser incluídos aqui ao longo do tempo.";

export const MODULE_EYEBROW = "Minha DELPI";

export const SEARCH_PLACEHOLDER = "Buscar por assunto…";

export const SEARCH_EMPTY_TITLE = "Nenhum guia encontrado";

export const SEARCH_EMPTY_MESSAGE =
  "Tente outros termos, como “nota fiscal”, “estoque” ou “transportadora”.";

export const DEPARTMENTS_SECTION_TITLE = "Departamentos";

export const SEARCH_RESULTS_TITLE = "Resultados da busca";

export const BACK_TO_GUIDES_LABEL = "Voltar para Guias";

export const BACK_TO_DEPARTMENTS_LABEL = "Voltar para departamentos";

export const CLEAR_SEARCH_LABEL = "Limpar busca";

export const PRINT_GUIDE_LABEL = "Imprimir guia";

export const OPEN_GUIDE_LABEL = "Abrir guia";

export const CHECKLIST_TITLE = "Checklist de conferência";

export const CHECKLIST_HINT =
  "Use esta lista apenas para conferir se reuniu as informações necessárias. As marcações não são salvas.";

export function getDepartments(): Department[] {
  return [...GUIDES_CATALOG.departments].sort((a, b) => a.order - b.order);
}

export function getDepartmentById(departmentId: string): Department | undefined {
  return GUIDES_CATALOG.departments.find(
    (department) => department.id === departmentId,
  );
}

export function getDepartmentBySlug(slug: string): Department | undefined {
  return GUIDES_CATALOG.departments.find(
    (department) => department.slug === slug,
  );
}

export function getPublishedGuides(): GuideDocument[] {
  return GUIDES_CATALOG.guides.filter((guide) => guide.meta.status === "published");
}

export function getGuideBySlug(slug: string): GuideDocument | undefined {
  return getPublishedGuides().find((guide) => guide.meta.slug === slug);
}

export function countGuidesByDepartment(departmentId: string): number {
  return getPublishedGuides().filter(
    (guide) => guide.meta.departmentId === departmentId,
  ).length;
}

export function getDepartmentSummaries(): DepartmentSummary[] {
  return getDepartments().map((department) => ({
    ...department,
    guideCount: countGuidesByDepartment(department.id),
  }));
}

export function toGuideSummary(guide: GuideDocument): GuideSummary {
  const department = getDepartmentById(guide.meta.departmentId);
  return {
    ...guide.meta,
    departmentName: department?.name ?? guide.meta.responsibleArea,
  };
}

export function getGuideSummaries(): GuideSummary[] {
  return getPublishedGuides().map(toGuideSummary);
}

export function getGuidesByDepartment(departmentId: string): GuideDocument[] {
  return getPublishedGuides().filter(
    (guide) => guide.meta.departmentId === departmentId,
  );
}

export function formatReadingTime(minutes: number): string {
  if (minutes <= 1) return "1 min de leitura";
  return `${minutes} min de leitura`;
}

export function formatProcedureCount(count: number): string {
  return count === 1 ? "1 procedimento" : `${count} procedimentos`;
}
