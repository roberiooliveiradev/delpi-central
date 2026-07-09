import type { FilePreviewKind } from "./filePreviewTypes";

export type ResolveFilePreviewKindInput = {
  mimeType?: string | null;
  fileName?: string | null;
  /** Tipo declarado pelo domínio (ex.: evidence.type). */
  declaredType?: string | null;
};

function normalizeMime(mimeType?: string | null): string {
  return (mimeType ?? "").toLowerCase();
}

function normalizeName(fileName?: string | null): string {
  return (fileName ?? "").toLowerCase();
}

function isImage(mime: string, declaredType?: string | null): boolean {
  return declaredType === "image" || mime.startsWith("image/");
}

function isPdf(mime: string, declaredType?: string | null): boolean {
  return declaredType === "pdf" || mime === "application/pdf";
}

function isSpreadsheet(mime: string, name: string, declaredType?: string | null): boolean {
  return (
    declaredType === "spreadsheet"
    || mime.includes("spreadsheet")
    || mime.includes("excel")
    || name.endsWith(".xlsx")
    || name.endsWith(".xls")
  );
}

function isDocx(mime: string, name: string): boolean {
  return (
    mime.includes("wordprocessingml")
    || mime === "application/msword"
    || name.endsWith(".docx")
    || name.endsWith(".doc")
  );
}

function isText(mime: string, name: string, declaredType?: string | null): boolean {
  return (
    declaredType === "manual_text"
    || declaredType === "text"
    || mime.startsWith("text/")
    || mime === "application/json"
    || mime === "application/markdown"
    || name.endsWith(".txt")
    || name.endsWith(".csv")
    || name.endsWith(".md")
    || name.endsWith(".markdown")
    || name.endsWith(".json")
    || name.endsWith(".tsv")
  );
}

export function resolveFilePreviewKind(input: ResolveFilePreviewKindInput): FilePreviewKind {
  const mime = normalizeMime(input.mimeType);
  const name = normalizeName(input.fileName);
  const declared = input.declaredType?.toLowerCase() ?? null;

  if (isImage(mime, declared)) return "image";
  if (isPdf(mime, declared)) return "pdf";
  if (isSpreadsheet(mime, name, declared)) return "spreadsheet";
  if (isDocx(mime, name)) return "docx";
  if (isText(mime, name, declared)) return "text";
  return "none";
}

export function canPreviewFile(input: ResolveFilePreviewKindInput): boolean {
  return resolveFilePreviewKind(input) !== "none";
}
