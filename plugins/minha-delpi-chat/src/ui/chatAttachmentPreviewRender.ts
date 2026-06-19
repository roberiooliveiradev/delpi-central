export async function renderSpreadsheetPreviewHtml(blob: Blob): Promise<string> {
  const XLSX = await import("xlsx");
  const buffer = await blob.arrayBuffer();
  const workbook = XLSX.read(buffer, { type: "array" });
  const sheetName = workbook.SheetNames[0];

  if (!sheetName) {
    return "<p>Planilha vazia.</p>";
  }

  const sheet = workbook.Sheets[sheetName];
  return XLSX.utils.sheet_to_html(sheet, { id: "mdc-attachment-preview-table" });
}

export async function renderDocxPreviewHtml(blob: Blob): Promise<string> {
  const mammoth = await import("mammoth");
  const arrayBuffer = await blob.arrayBuffer();
  const result = await mammoth.convertToHtml({ arrayBuffer });
  return result.value;
}
