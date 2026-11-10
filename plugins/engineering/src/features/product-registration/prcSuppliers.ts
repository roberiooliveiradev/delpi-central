/** Modelo de linha de fornecedor do PRC — conversão fiel do payload
 * `suppliers[]` (partNumber obrigatório — PRC-REF-022-FIX-01; vazio é
 * representado como string vazia canônica e rejeitado na validação).
 *
 * D14-FIX-02 — cada linha visual tem `rowId` estável e `origin`
 * (`official` = baseline SA5; `draft` = candidata da sessão). A chave
 * oficial `(supplierCode, store)` gera operações SA5; remoção/descarte
 * e justificativas usam `rowId` para não confundir instâncias. */

export type SupplierRowOrigin = "official" | "draft";

export type SupplierRow = {
  /** Identidade local estável da linha UI — nunca índice de array. */
  rowId: string;
  /** Origem: baseline SA5 vs candidata adicionada nesta sessão. */
  origin: SupplierRowOrigin;
  supplierCode: string;
  store: string;
  supplierName: string;
  /** A2_NREDUZ — nome fantasia oficial, quando disponível. */
  supplierShortName?: string;
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
  /** D14-FIX — editor de razão expandido na linha auxiliar. */
  pnReasonOpen?: boolean;
  catReasonOpen?: boolean;
  opReasonOpen?: boolean;
  /** Erro contextual de seleção (ex.: duplicidade SA2). */
  selectionError?: string;
};

let _rowSeq = 0;

/** Gera `rowId` exclusivo por sessão (não reutilizado). */
export function newSupplierRowId(prefix = "row"): string {
  _rowSeq += 1;
  const rand =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `r${Date.now().toString(36)}${Math.random().toString(36).slice(2, 8)}`;
  return `${prefix}-${_rowSeq}-${rand}`;
}

/** Chave oficial SA5 `(supplierCode|store)` — zeros preservados. */
export function supplierOfficialKey(
  code: string,
  store: string,
): string {
  return `${String(code ?? "").trim()}|${String(store ?? "").trim()}`;
}

export function toSupplierRows(value: unknown): SupplierRow[] {
  if (!Array.isArray(value)) return [];
  return value
    .filter(
      (v): v is Record<string, unknown> =>
        typeof v === "object" && v !== null,
    )
    .map((v) => ({
      rowId: newSupplierRowId("draft"),
      origin: "draft" as const,
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

/** Linha em branco (candidata) para "Adicionar fornecedor". */
export function emptySupplierRow(): SupplierRow {
  return {
    rowId: newSupplierRowId("draft"),
    origin: "draft",
    supplierCode: "",
    store: "",
    supplierName: "",
    partNumber: "",
    catalogNumber: "",
    query: "",
  };
}

/** Linha a partir de vínculo oficial SA5 do edit-context. */
export function officialSupplierRow(link: {
  supplierCode: string;
  store: string;
  supplierName?: string;
  supplierShortName?: string;
  partNumber?: string | null;
  catalogNumber?: string | null;
}): SupplierRow {
  return {
    rowId: newSupplierRowId("official"),
    origin: "official",
    supplierCode: link.supplierCode,
    store: link.store,
    supplierName: link.supplierName || "",
    supplierShortName: link.supplierShortName || "",
    partNumber: link.partNumber == null ? "" : String(link.partNumber),
    catalogNumber:
      link.catalogNumber == null ? "" : String(link.catalogNumber),
    query: "",
  };
}

/**
 * Linhas candidatas (`draft`) cuja chave oficial já existe em outra
 * linha (oficial ou outra candidata). A linha oficial do mesmo par
 * NÃO entra no conjunto — permanece íntegra; só a candidata é
 * marcada como duplicada descartável.
 */
export function duplicateDraftRowIds(rows: SupplierRow[]): Set<string> {
  const byKey = new Map<string, SupplierRow[]>();
  for (const r of rows) {
    const code = r.supplierCode.trim();
    const store = r.store.trim();
    if (!code || !store) continue;
    const key = supplierOfficialKey(code, store);
    const list = byKey.get(key) || [];
    list.push(r);
    byKey.set(key, list);
  }
  const dups = new Set<string>();
  for (const group of byKey.values()) {
    if (group.length < 2) continue;
    const hasOfficial = group.some((r) => r.origin === "official");
    for (const r of group) {
      if (r.origin === "draft") dups.add(r.rowId);
      else if (!hasOfficial) dups.add(r.rowId);
    }
    /* Múltiplos oficiais com a mesma chave = ambiguidade; marcar todos. */
    const officials = group.filter((r) => r.origin === "official");
    if (officials.length > 1) {
      for (const r of officials) dups.add(r.rowId);
    }
  }
  return dups;
}

/** @deprecated use duplicateDraftRowIds — mantido para testes legados. */
export function duplicateSupplierIndexes(rows: SupplierRow[]): Set<number> {
  const dups = duplicateDraftRowIds(rows);
  const out = new Set<number>();
  rows.forEach((r, i) => {
    if (dups.has(r.rowId)) out.add(i);
  });
  return out;
}

/** Outra linha (exceto `exceptRowId`) já ocupa a chave oficial. */
export function findRowWithOfficialKey(
  rows: SupplierRow[],
  code: string,
  store: string,
  exceptRowId?: string,
): SupplierRow | undefined {
  const key = supplierOfficialKey(code, store);
  if (key === "|") return undefined;
  return rows.find(
    (r) =>
      r.rowId !== exceptRowId &&
      supplierOfficialKey(r.supplierCode, r.store) === key,
  );
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
