import { canPreviewFile, resolveFilePreviewKind, type FilePreviewKind } from "@delpi/plugin-ui/index";

export type AttachedFilePreviewInput = {
  tipo?: string | null;
  tipo_mime?: string | null;
  nome_arquivo?: string | null;
};

export function canPreviewAttachedFile(input: AttachedFilePreviewInput): boolean {
  if (input.tipo === "link") return false;
  return canPreviewFile({
    mimeType: input.tipo_mime,
    fileName: input.nome_arquivo,
  });
}

export function attachedFilePreviewKind(input: AttachedFilePreviewInput): FilePreviewKind {
  return resolveFilePreviewKind({
    mimeType: input.tipo_mime,
    fileName: input.nome_arquivo,
  });
}

export function isSpreadsheetAttachedFile(input: AttachedFilePreviewInput): boolean {
  return attachedFilePreviewKind(input) === "spreadsheet";
}
