/** CSV com acentuação correta ao abrir no Excel (Windows / PT-BR). */

const UTF16_LE_BOM = 0xfeff;

function normalizeCsvBody(content: string): string {
  return String(content || "")
    .replace(/^\ufeff/, "")
    .replace(/^sep=;[\r\n]*/i, "")
    .replace(/\r?\n/g, "\r\n")
    .trimEnd();
}

export function buildExcelCsvContent(content: string): string {
  const body = normalizeCsvBody(content);
  return body ? `sep=;\r\n${body}` : "sep=;";
}

export function buildExcelCsvBlob(content: string): Blob {
  const text = buildExcelCsvContent(content);
  const buffer = new ArrayBuffer(text.length * 2 + 2);
  const view = new DataView(buffer);
  view.setUint16(0, UTF16_LE_BOM, true);

  for (let index = 0; index < text.length; index += 1) {
    view.setUint16(2 + index * 2, text.charCodeAt(index), true);
  }

  return new Blob([buffer], { type: "text/csv;charset=utf-16le;" });
}
