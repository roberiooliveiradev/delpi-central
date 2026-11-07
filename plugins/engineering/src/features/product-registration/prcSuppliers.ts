/** Modelo de linha de fornecedor do PRC — conversão fiel do payload
 * `suppliers[]` (partNumber opcional pode ser null → string vazia
 * canônica, nunca valor inventado). */

export type SupplierRow = {
  supplierCode: string;
  store: string;
  supplierName: string;
  partNumber: string;
  catalogNumber: string;
};

export function toSupplierRows(value: unknown): SupplierRow[] {
  if (!Array.isArray(value)) return [];
  return value
    .filter(
      (v): v is Record<string, unknown> =>
        typeof v === "object" && v !== null,
    )
    .map((v) => ({
      supplierCode: String(v.supplierCode ?? ""),
      store: String(v.store ?? ""),
      supplierName: String(v.supplierName ?? ""),
      partNumber: v.partNumber == null ? "" : String(v.partNumber),
      catalogNumber: v.catalogNumber == null ? "" : String(v.catalogNumber),
    }));
}

export function supplierRowsToPayload(rows: SupplierRow[]) {
  return rows.map((r) => ({
    supplierCode: r.supplierCode.trim(),
    store: r.store.trim(),
    supplierName: r.supplierName.trim(),
    partNumber: r.partNumber.trim() || "",
    catalogNumber: r.catalogNumber.trim() || null,
  }));
}
