/** Limites alinhados a `BudgetDocumentStorage` (api-delpi). */
export const MAX_DOCUMENT_BYTES = 25 * 1024 * 1024;

export const ALLOWED_EXTENSIONS = new Set([
  ".pdf",
  ".xlsx",
  ".xls",
  ".csv",
  ".pptx",
  ".ppt",
  ".doc",
  ".docx",
  ".txt",
  ".jpg",
  ".jpeg",
  ".png",
  ".webp",
  ".gif",
  ".mp4",
  ".webm",
]);

export const DOCUMENT_KIND_OPTIONS = [
  { value: "pdf", label: "PDF" },
  { value: "spreadsheet", label: "Planilha" },
  { value: "presentation", label: "Apresentação" },
  { value: "document", label: "Documento" },
  { value: "image", label: "Imagem" },
  { value: "video", label: "Vídeo" },
  { value: "external_link", label: "Link externo" },
] as const;

export type ClientUploadValidation =
  | { ok: true }
  | { ok: false; message: string };

export function validateClientUpload(file: File | null | undefined): ClientUploadValidation {
  if (!file) {
    return { ok: false, message: "Selecione um arquivo." };
  }
  if (file.size <= 0) {
    return { ok: false, message: "Arquivo vazio." };
  }
  if (file.size > MAX_DOCUMENT_BYTES) {
    return { ok: false, message: "Arquivo excede o limite de 25 MB." };
  }
  const name = file.name || "";
  const dot = name.lastIndexOf(".");
  const ext = dot >= 0 ? name.slice(dot).toLowerCase() : "";
  if (!ALLOWED_EXTENSIONS.has(ext)) {
    return { ok: false, message: "Extensão de arquivo não permitida." };
  }
  return { ok: true };
}

export function formatBytes(size: number): string {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}
