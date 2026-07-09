import type { DocxPreviewData } from "./docxPreviewModel";
import type { SpreadsheetPreviewData } from "./spreadsheetPreviewModel";

export type FilePreviewKind = "image" | "pdf" | "text" | "spreadsheet" | "docx" | "none";

export type FilePreviewLabels = {
  loading: string;
  loadFailed: string;
  unavailable: string;
  emptyText: string;
  textTruncated: string;
  emptySpreadsheet: string;
  spreadsheetReadOnly: string;
  spreadsheetExcelTitle: string;
  docxReadOnly: string;
  docxWordTitle: string;
  docxEmptyDocument: string;
  docxTruncated: string;
  spreadsheetTruncatedPrefix: string;
  spreadsheetTruncatedRows: string;
  spreadsheetTruncatedAnd: string;
  spreadsheetTruncatedCols: string;
  spreadsheetTruncatedSuffix: string;
};

export const DEFAULT_FILE_PREVIEW_LABELS: FilePreviewLabels = {
  loading: "Carregando pré-visualização…",
  loadFailed: "Não foi possível carregar a pré-visualização.",
  unavailable: "Pré-visualização não disponível para este tipo de arquivo.",
  emptyText: "Arquivo de texto vazio.",
  textTruncated: "Conteúdo truncado. Baixe o arquivo para ver o documento completo.",
  emptySpreadsheet: "Planilha vazia.",
  spreadsheetReadOnly: "Somente leitura",
  spreadsheetExcelTitle: "Excel",
  docxReadOnly: "Somente leitura",
  docxWordTitle: "Word",
  docxEmptyDocument: "Documento vazio.",
  docxTruncated: "Conteúdo truncado na pré-visualização. Baixe o arquivo para ver o documento completo.",
  spreadsheetTruncatedPrefix: "Pré-visualização limitada",
  spreadsheetTruncatedRows: " linhas",
  spreadsheetTruncatedAnd: " e",
  spreadsheetTruncatedCols: " colunas",
  spreadsheetTruncatedSuffix: " na aba «{sheet}». Baixe o arquivo para ver a planilha completa.",
};

export type FilePreviewContentState = {
  kind: FilePreviewKind;
  loading: boolean;
  error: string | null;
  previewUrl: string | null;
  textContent: string | null;
  textTruncated: boolean;
  spreadsheetData: SpreadsheetPreviewData | null;
  docxData: DocxPreviewData | null;
};

export type FilePreviewSource =
  | Blob
  | File
  | (() => Promise<Blob>)
  | (() => Promise<string>);
