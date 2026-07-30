import {
  detectMediaUploadKind,
  validateMediaUploadFile,
  type MediaUploadKind,
} from "../api/mediaUploadLimits";

const DROP_KINDS: MediaUploadKind[] = ["image", "video"];

/** Durante dragover o browser costuma expor só `types`, não `files`. */
export function dataTransferLooksLikeOsFileDrag(data: DataTransfer | null | undefined): boolean {
  if (!data?.types) return false;
  const types = Array.from(data.types);
  return types.includes("Files") || types.includes("application/x-moz-file");
}

/** True se o DataTransfer traz arquivos de imagem/vídeo do SO (no drop). */
export function dataTransferHasCanvasMediaFiles(data: DataTransfer | null | undefined): boolean {
  if (!data) return false;
  return collectCanvasMediaFiles(data).length > 0;
}

export function collectCanvasMediaFiles(data: DataTransfer): File[] {
  const out: File[] = [];
  const seen = new Set<string>();
  const push = (file: File | null | undefined) => {
    if (!file) return;
    const kind = detectMediaUploadKind(file);
    if (!kind || !DROP_KINDS.includes(kind)) return;
    const key = `${file.name}:${file.size}:${file.lastModified}`;
    if (seen.has(key)) return;
    seen.add(key);
    out.push(file);
  };

  if (data.files?.length) {
    for (const file of Array.from(data.files)) push(file);
  }
  if (data.items?.length) {
    for (const item of Array.from(data.items)) {
      if (item.kind !== "file") continue;
      push(item.getAsFile() ?? undefined);
    }
  }
  return out;
}

/** Valida e filtra arquivos dropados; devolve erros por arquivo rejeitado. */
export function planCanvasMediaDrop(files: File[]): {
  accepted: File[];
  errors: string[];
} {
  const accepted: File[] = [];
  const errors: string[] = [];
  for (const file of files) {
    const err = validateMediaUploadFile(file, DROP_KINDS);
    if (err) {
      errors.push(`${file.name}: ${err}`);
      continue;
    }
    accepted.push(file);
  }
  return { accepted, errors };
}

export function isEditableDropTarget(target: EventTarget | null): boolean {
  if (!(target instanceof Element)) return false;
  return Boolean(
    target.closest(
      'input, textarea, select, [contenteditable="true"], [contenteditable=""], .ProseMirror',
    ),
  );
}
