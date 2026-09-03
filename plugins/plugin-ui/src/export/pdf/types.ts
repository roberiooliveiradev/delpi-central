export type DelpiDocumentColumn = { key: string; label: string };

export type DelpiDocumentTable = {
  title: string;
  columns: DelpiDocumentColumn[];
  rows: Record<string, unknown>[];
  /** Destaca coluna status (OK/erro) — relatório de desenho. */
  highlightStatusColumn?: boolean;
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

/** Bloco narrativo (título + corpo) — fichas A4 com grade 2×2. */
export type DelpiDocumentTextSection = {
  title: string;
  body: string;
};

export type DelpiDocumentBadgeTone = "approved" | "rejected" | "neutral";

export type DelpiDocumentSpec = {
  documentTitle: string;
  subtitle?: string;
  badge?: string;
  badgeTone?: DelpiDocumentBadgeTone;
  runningMeta?: string;
  summaryLines?: DelpiDocumentSummaryLine[];
  /** Blocos narrativos renderizados em grade (ex.: processo / problema / melhoria). */
  textSections?: DelpiDocumentTextSection[];
  tables?: DelpiDocumentTable[];
  imageSections?: DelpiDocumentImageSection[];
  footerNote?: string;
  /** Contexto exibido no rodapé fixo (ex.: código do produto ou título). */
  footerContext?: string;
};
