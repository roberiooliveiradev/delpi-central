/**
 * Contratos de domínio para o catálogo de guias.
 * Preparados para substituição futura por API DELPI sem mudar as páginas.
 */

/** Ícone Lucide em kebab-case (ex.: "receipt" → Receipt). */
export type DepartmentIconId = string;

export type Department = {
  id: string;
  name: string;
  slug: string;
  icon: DepartmentIconId;
  description?: string;
  order: number;
};

export type GuideChecklistItem = {
  id: string;
  label: string;
};

export type GuideSectionItem = {
  id: string;
  text: string;
  /** Destaque discreto para ponto crítico da conferência. */
  emphasis?: boolean;
};

export type GuideSection = {
  id: string;
  title: string;
  items: GuideSectionItem[];
};

export type GuideMeta = {
  id: string;
  slug: string;
  departmentId: string;
  title: string;
  summary: string;
  tags: string[];
  responsibleArea: string;
  /** Rótulo exibido; V1 usa valor provisório até validação oficial. */
  updatedAtLabel: string;
  /** Minutos estimados de leitura. */
  readingTimeMinutes: number;
  status: "published" | "draft";
};

export type GuideDocument = {
  meta: GuideMeta;
  introduction: string;
  sections: GuideSection[];
  checklist: GuideChecklistItem[];
  /** Aviso discreto exibido no final da página de detalhe. */
  footerNotice: string;
};

/** Resumo usado em listagens / cards (derivado do documento completo). */
export type GuideSummary = GuideMeta & {
  departmentName: string;
};

/** View model do departamento com contagem calculada do catálogo. */
export type DepartmentSummary = Department & {
  guideCount: number;
};

export type GuidesCatalog = {
  departments: Department[];
  guides: GuideDocument[];
};
