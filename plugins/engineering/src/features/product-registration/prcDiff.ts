/** D13 — baseline oficial + working copy → diff automático.
 * Funções puras: um campo só está alterado quando o valor editado
 * difere do oficial, com semântica stringificada que preserva zeros
 * à esquerda e não confunde ausente/vazio/0/false.
 *
 * D14-FIX-02 — remoção/ADD usam origem da linha (`official`|`draft`)
 * e `removeRowIds` (rowId local). A chave oficial `(code|store)` só
 * identifica o vínculo SA5; nunca remove instâncias visuais em lote. */

import type { SupplierRowOrigin } from "./prcSuppliers";

export type PrcScalarChange = {
  path: string;
  before: string;
  after: string;
};

export type PrcLinkKey = { supplierCode: string; store: string };

export type PrcLinkOp =
  | {
      operation: "update";
      key: PrcLinkKey;
      fields: { partNumber?: string; catalogNumber?: string };
    }
  | {
      operation: "add";
      key: PrcLinkKey;
      fields: { partNumber?: string; catalogNumber?: string };
      supplierName?: string;
    }
  | { operation: "remove"; key: PrcLinkKey };

export function linkKeyOf(code: string, store: string): string {
  return `${String(code ?? "").trim()}|${String(store ?? "").trim()}`;
}

function norm(v: unknown): string {
  if (v === null || v === undefined) return "";
  return String(v).trim();
}

/** Diff escalar SB1: paths editados cujo valor difere do baseline. */
export function computeScalarDiff(
  baseline: Record<string, unknown>,
  working: Record<string, string>,
  paths: string[],
): PrcScalarChange[] {
  const out: PrcScalarChange[] = [];
  for (const p of paths) {
    const before = norm(baseline[p]);
    const after = norm(working[p]);
    if (before !== after) out.push({ path: p, before, after });
  }
  return out;
}

export type PrcLinkRow = {
  rowId: string;
  origin: SupplierRowOrigin;
  supplierCode: string;
  store: string;
  supplierName?: string;
  partNumber: string;
  catalogNumber: string;
};

export type PrcOfficialLink = {
  supplierCode: string;
  store: string;
  supplierName?: string;
  partNumber?: string;
  catalogNumber?: string;
};

export type LinkDiffResult = {
  ops: PrcLinkOp[];
  /** Chaves oficiais ambíguas no baseline (mais de um registro). */
  ambiguousOfficialKeys: string[];
  /** Chaves com mais de uma linha candidata/conflito local. */
  conflictingKeys: string[];
};

/**
 * Diff de vínculos SA5 (linha da tabela vs baseline oficial).
 *
 * - `draft` descartado (ausente de `rows`) → nenhum evento.
 * - `draft` com chave nova → `add`.
 * - `draft` com chave já oficial → conflito (não gera `add`).
 * - `official` + rowId em `removeRowIds` → `remove` (vence update).
 * - `official` com PN/Cat distintos → `update`.
 * - `removeRowIds` de linha draft é ignorado (descarte é só UI).
 */
export function computeLinkDiff(
  official: PrcOfficialLink[],
  rows: PrcLinkRow[],
  removeRowIds: ReadonlySet<string> = new Set(),
): PrcLinkOp[] {
  return computeLinkDiffDetailed(official, rows, removeRowIds).ops;
}

export function computeLinkDiffDetailed(
  official: PrcOfficialLink[],
  rows: PrcLinkRow[],
  removeRowIds: ReadonlySet<string> = new Set(),
): LinkDiffResult {
  const officialByKey = new Map<string, PrcOfficialLink[]>();
  for (const l of official) {
    const k = linkKeyOf(l.supplierCode, l.store);
    const list = officialByKey.get(k) || [];
    list.push(l);
    officialByKey.set(k, list);
  }
  const ambiguousOfficialKeys = [...officialByKey.entries()]
    .filter(([, list]) => list.length > 1)
    .map(([k]) => k);

  const complete = rows.filter(
    (r) => r.supplierCode.trim() && r.store.trim(),
  );

  /* Contagem por chave — conflito se 2+ linhas (qualquer origem)
   * ou draft colidindo com oficial. */
  const rowsByKey = new Map<string, PrcLinkRow[]>();
  for (const r of complete) {
    const k = linkKeyOf(r.supplierCode, r.store);
    const list = rowsByKey.get(k) || [];
    list.push(r);
    rowsByKey.set(k, list);
  }
  const conflictingKeys: string[] = [];
  for (const [k, list] of rowsByKey) {
    if (list.length > 1) conflictingKeys.push(k);
    else if (
      list[0].origin === "draft" &&
      officialByKey.has(k) &&
      !ambiguousOfficialKeys.includes(k)
    ) {
      /* Draft sozinho mas chave já no baseline → também conflito
       * (UI deveria ter bloqueado a seleção). */
      conflictingKeys.push(k);
    }
  }

  const ops: PrcLinkOp[] = [];
  const emittedKeys = new Set<string>();

  for (const row of complete) {
    const key = linkKeyOf(row.supplierCode, row.store);
    if (ambiguousOfficialKeys.includes(key)) continue;
    if (conflictingKeys.includes(key)) continue;
    if (emittedKeys.has(key)) continue;

    if (row.origin === "draft") {
      if (officialByKey.has(key)) continue; // nunca ADD do que já é oficial
      if (removeRowIds.has(row.rowId)) continue; // draft marcado ≠ remove SA5
      const fields: { partNumber?: string; catalogNumber?: string } = {};
      if (row.partNumber.trim()) fields.partNumber = row.partNumber.trim();
      if (row.catalogNumber.trim())
        fields.catalogNumber = row.catalogNumber.trim();
      ops.push({
        operation: "add",
        key: {
          supplierCode: row.supplierCode.trim(),
          store: row.store.trim(),
        },
        fields,
        supplierName: row.supplierName,
      });
      emittedKeys.add(key);
      continue;
    }

    /* official */
    if (removeRowIds.has(row.rowId)) {
      ops.push({
        operation: "remove",
        key: {
          supplierCode: row.supplierCode.trim(),
          store: row.store.trim(),
        },
      });
      emittedKeys.add(key);
      continue;
    }
    const baseList = officialByKey.get(key);
    const base = baseList?.[0];
    if (!base) continue;
    const fields: { partNumber?: string; catalogNumber?: string } = {};
    const pn = row.partNumber.trim();
    const cat = row.catalogNumber.trim();
    if (pn !== norm(base.partNumber)) fields.partNumber = pn;
    if (cat !== norm(base.catalogNumber)) fields.catalogNumber = cat;
    if (Object.keys(fields).length) {
      ops.push({
        operation: "update",
        key: {
          supplierCode: row.supplierCode.trim(),
          store: row.store.trim(),
        },
        fields,
      });
      emittedKeys.add(key);
    }
  }

  return { ops, ambiguousOfficialKeys, conflictingKeys };
}

/** Detecta conflitos: mesma chave com linhas duplicadas. */
export function linkDiffConflicts(rows: PrcLinkRow[]): string[] {
  const seen = new Map<string, number>();
  const dups: string[] = [];
  rows.forEach((r, i) => {
    const k = linkKeyOf(r.supplierCode, r.store);
    if (k === "|") return;
    if (seen.has(k)) dups.push(`${k} (linhas ${seen.get(k)! + 1} e ${i + 1})`);
    else seen.set(k, i);
  });
  return dups;
}
