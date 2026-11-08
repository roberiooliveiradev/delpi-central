/** D13 — baseline oficial + working copy → diff automático.
 * Funções puras: um campo só está alterado quando o valor editado
 * difere do oficial, com semântica stringificada que preserva zeros
 * à esquerda e não confunde ausente/vazio/0/false. */

export type PrcScalarChange = {
  path: string;
  before: string;
  after: string;
};

export type PrcLinkKey = { supplierCode: string; store: string };

export type PrcLinkOp =
  | { operation: "update"; key: PrcLinkKey; fields: { partNumber?: string; catalogNumber?: string } }
  | { operation: "add"; key: PrcLinkKey; fields: { partNumber?: string; catalogNumber?: string }; supplierName?: string }
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

/** Diff de vínculos SA5 (linha da tabela vs baseline oficial).
 * `removeMarks` = conjunto de chaves marcadas para remoção proposta.
 * UPDATE só com atributos que mudaram; ADD só vínculos novos; REMOVE
 * só oficiais existentes marcados. Sem no-ops. */
export function computeLinkDiff(
  official: PrcOfficialLink[],
  rows: PrcLinkRow[],
  removeMarks: ReadonlySet<string>,
): PrcLinkOp[] {
  const officialKeys = new Map(
    official.map((l) => [linkKeyOf(l.supplierCode, l.store), l]),
  );
  const rowKeys = new Map(
    rows
      .filter((r) => r.supplierCode.trim() && r.store.trim())
      .map((r) => [linkKeyOf(r.supplierCode, r.store), r]),
  );
  const ops: PrcLinkOp[] = [];

  for (const [key, row] of rowKeys) {
    const base = officialKeys.get(key);
    if (!base) {
      const fields: { partNumber?: string; catalogNumber?: string } = {};
      if (row.partNumber.trim()) fields.partNumber = row.partNumber.trim();
      if (row.catalogNumber.trim())
        fields.catalogNumber = row.catalogNumber.trim();
      ops.push({
        operation: "add",
        key: { supplierCode: row.supplierCode, store: row.store },
        fields,
        supplierName: row.supplierName,
      });
      continue;
    }
    if (removeMarks.has(key)) continue; // REMOVE vence UPDATE
    const fields: { partNumber?: string; catalogNumber?: string } = {};
    const pn = row.partNumber.trim();
    const cat = row.catalogNumber.trim();
    if (pn !== norm(base.partNumber)) fields.partNumber = pn;
    if (cat !== norm(base.catalogNumber)) fields.catalogNumber = cat;
    if (Object.keys(fields).length) {
      ops.push({
        operation: "update",
        key: { supplierCode: row.supplierCode, store: row.store },
        fields,
      });
    }
  }

  for (const key of removeMarks) {
    if (!officialKeys.has(key)) continue; // só oficial pode remover
    const [supplierCode, store] = key.split("|");
    ops.push({ operation: "remove", key: { supplierCode, store } });
  }
  return ops;
}

/** Detecta conflitos: mesma chave com op duplicada ou linha duplicada. */
export function linkDiffConflicts(
  rows: PrcLinkRow[],
): string[] {
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
