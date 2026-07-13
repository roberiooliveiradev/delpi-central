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
};

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
