import { triggerBlobDownload } from "../utils/downloadBlob";

/** Dispara download de arquivo no navegador (única implementação do plugin). */
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

export function csvRow(cells: unknown[]): string {
  return cells.map(csvCell).join(";");
}

export function buildUtf8CsvBlob(content: string): Blob {
  const BOM = "\uFEFF";
  return new Blob([`${BOM}${content}`], { type: "text/csv;charset=utf-8" });
}

/** Nome de arquivo seguro; fallback configurável (ex.: relatório de desenho). */
export function sanitizeFilename(name: string, fallback = "dados"): string {
  const cleaned = name
    .replace(/[^a-zA-Z0-9À-ÿ\s_-]/g, "")
    .replace(/\s+/g, "_")
    .slice(0, 60);

  return cleaned || fallback;
}

/** Nome de aba Excel: sem \\ / ? * [ ] : e máx. 31 caracteres. */
export function sanitizeSheetName(name: string, fallback = "Dados"): string {
  const cleaned = name
    .replace(/[\\/?*[\]:]/g, " ")
    .replace(/\s+/g, " ")
    .trim();

  const base = cleaned || fallback;

  return base.length <= 31 ? base : `${base.slice(0, 28).trimEnd()}...`;
}
