export type DelpiDocumentColumn = { key: string; label: string };

export type DelpiDocumentTable = {
  title: string;
  columns: DelpiDocumentColumn[];
  rows: Record<string, unknown>[];
  /** Chave do perfil de colunas (structure, guide, inspection, checklist, …). */
  layoutKey?: string;
  /** Destaca coluna status (OK/erro) — relatório de desenho. */
  highlightStatusColumn?: boolean;
  /** Árvore ASCII no lugar da tabela plana (estrutura SG1010). */
  presentation?: "outline" | "table";
  outline?: string;
};

export type DelpiDocumentSummaryLine = {
  label: string;
  value: string;
};

export type DelpiDocumentImageSection = {
  title?: string;
  dataUrl: string;
  alt?: string;
};

export type DelpiDocumentBadgeTone = "approved" | "rejected" | "neutral";

export type DelpiDocumentSpec = {
  documentTitle: string;
  subtitle?: string;
  badge?: string;
  badgeTone?: DelpiDocumentBadgeTone;
  runningMeta?: string;
  summaryLines?: DelpiDocumentSummaryLine[];
  tables?: DelpiDocumentTable[];
  imageSections?: DelpiDocumentImageSection[];
  footerNote?: string;
  /** Contexto exibido no rodapé fixo (ex.: código do produto ou título). */
  footerContext?: string;
};
