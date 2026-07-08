export function triggerBlobDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.rel = "noopener";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export function triggerFileDownload(blob: Blob, filename: string): void {
  triggerBlobDownload(blob, filename);
}

export function csvCell(value: unknown): string {
  if (value == null) {
    return "";
  }

  const text = String(value);

  if (text.includes(";") || text.includes('"') || text.includes("\n")) {
    return `"${text.replace(/"/g, '""')}"`;
  }

  return text;
}

export function buildUtf8CsvBlob(content: string): Blob {
  const BOM = "\uFEFF";
  return new Blob([`${BOM}${content}`], { type: "text/csv;charset=utf-8" });
}

export function sanitizeFilename(name: string, fallback = "dados"): string {
  const cleaned = name
    .replace(/[^a-zA-Z0-9À-ÿ\s_-]/g, "")
    .replace(/\s+/g, "_")
    .slice(0, 60);

  return cleaned || fallback;
}

export function sanitizeSheetName(name: string, fallback = "Dados"): string {
  const cleaned = name
    .replace(/[\\/?*[\]:]/g, " ")
    .replace(/\s+/g, " ")
    .trim();

  const base = cleaned || fallback;

  return base.length <= 31 ? base : `${base.slice(0, 28).trimEnd()}...`;
}
