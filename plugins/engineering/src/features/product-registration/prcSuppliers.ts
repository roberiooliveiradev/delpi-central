/** Modelo de linha de fornecedor do PRC — conversão fiel do payload
 * `suppliers[]` (partNumber opcional pode ser null → string vazia
 * canônica, nunca valor inventado). */

export type SupplierRow = {
  supplierCode: string;
  store: string;
  supplierName: string;
  partNumber: string;
  catalogNumber: string;
  /** Texto de busca SA2 da linha (só enquanto não há seleção oficial). */
  query: string;
  /** D14 — busca colapsável: aberta só quando a lupa foi acionada. */
  searchOpen?: boolean;
  /** D14 — justificativas individuais opcionais (≤250). */
  pnReason?: string;
  catReason?: string;
  opReason?: string;
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
      query: "",
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

/** Linha em branco para "Adicionar fornecedor". */
export function emptySupplierRow(): SupplierRow {
  return {
    supplierCode: "",
    store: "",
    supplierName: "",
    partNumber: "",
    catalogNumber: "",
    query: "",
  };
}

/** Índices de linhas duplicadas pela chave oficial (code, store). */
export function duplicateSupplierIndexes(rows: SupplierRow[]): Set<number> {
  const seen = new Map<string, number>();
  const dups = new Set<number>();
  rows.forEach((r, i) => {
    const code = r.supplierCode.trim();
    const store = r.store.trim();
    if (!code || !store) return;
    const key = `${code}|${store}`;
    if (seen.has(key)) {
      dups.add(seen.get(key) as number);
      dups.add(i);
    } else {
      seen.set(key, i);
    }
  });
  return dups;
}

/** Hit SA2 — razão social (`A2_NOME`) é sempre a linha principal;
 * código, loja e nome fantasia (`A2_NREDUZ`) vão na linha secundária.
 * Identidade do vínculo é sempre (supplierCode, store), zeros
 * preservados; nunca trocar A2_NOME por A2_NREDUZ no payload. */
export function supplierHitLabel(hit: {
  supplier_code?: string;
  supplier_store?: string;
  supplier_name?: string;
}): string {
  return supplierHitMain(hit);
}

export function supplierHitMain(hit: {
  supplier_name?: string;
}): string {
  return String(hit.supplier_name ?? "").trim();
}

export function supplierHitSecondary(hit: {
  supplier_code?: string;
  supplier_store?: string;
  supplier_short_name?: string;
  supplier_name?: string;
}): string {
  const code = String(hit.supplier_code ?? "");
  const store = String(hit.supplier_store ?? "");
  const trade = String(hit.supplier_short_name ?? "").trim();
  const legal = String(hit.supplier_name ?? "").trim();
  const parts = [`Código: ${code}`, `Loja: ${store}`];
  if (trade && trade.toUpperCase() !== legal.toUpperCase()) {
    parts.push(`Fantasia: ${trade}`);
  }
  return parts.join(" · ");
}
