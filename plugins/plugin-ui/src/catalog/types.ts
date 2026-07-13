import type { ReactNode } from "react";

export type CatalogFamily =
  | "help"
  | "layout"
  | "feedback"
  | "forms"
  | "data"
  | "export"
  | "charts"
  | "preview"
  | "diagram"
  | "shape"
  | "menu";

export type CatalogLifecycle = "new" | "updated" | "stable";

export type CatalogLifecycleFilter = "all" | "new" | "updated";

export type CatalogDemo = {
  id: string;
  label: string;
  render: () => ReactNode;
};

export type CatalogEntry = {
  id: string;
  family: CatalogFamily;
  exportName: string;
  title: string;
  description?: string;
  /** Âncora relativa em docs/component-catalog.md */
  docAnchor?: string;
  /** Props principais (só documentação visual — API canônica no markdown). */
  propsSummary?: string[];
  demos: CatalogDemo[];
  /** Primeira aparição pública (ISO YYYY-MM-DD). */
  addedAt: string;
  /** Última mudança relevante (ISO); default efetivo = addedAt. */
  updatedAt: string;
  changeNote?: string;
  /** Derivado de addedAt/updatedAt — não gravar manualmente no inventário. */
  lifecycle: CatalogLifecycle;
};

/** Entrada de demo (sem metadados — mergeados do inventário no registry). */
export type CatalogEntryDraft = Omit<
  CatalogEntry,
  "addedAt" | "updatedAt" | "lifecycle" | "changeNote"
>;


export const CATALOG_FAMILY_LABELS: Record<CatalogFamily, string> = {
  help: "Help",
  layout: "Layout",
  feedback: "Feedback",
  forms: "Forms",
  data: "Data",
  export: "Export",
  charts: "Charts",
  preview: "Preview",
  diagram: "Diagram",
  shape: "Shape",
  menu: "Menu",
};

export const CATALOG_LIFECYCLE_LABELS: Record<Exclude<CatalogLifecycle, "stable">, string> = {
  new: "Novo",
  updated: "Atualizado",
};
