const BRANCH_EXPORT_SUFFIX: Record<string, string> = {
  "01": "MATRIZ",
  "02": "FILIAL",
};

function pad2(value: number): string {
  return String(value).padStart(2, "0");
}

/** Ex.: `MAPA 24-08-2026 MATRIZ` (filial 01) ou `MAPA 24-08-2026 FILIAL` (filial 02). */
export function buildDeliveryMapExportFileName(
  branch: string,
  exportedAt: Date = new Date(),
): string {
  const suffix = BRANCH_EXPORT_SUFFIX[branch] ?? "FILIAL";
  const day = pad2(exportedAt.getDate());
  const month = pad2(exportedAt.getMonth() + 1);
  const year = exportedAt.getFullYear();
  return `MAPA ${day}-${month}-${year} ${suffix}`;
}
