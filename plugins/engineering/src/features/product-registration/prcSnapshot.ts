/** Adaptação contratual explícita — snapshot consolidado publicado
 * (rota 13/15, schemaVersion=2) → mapa plano consumido por
 * `PrcTechnicalSheetView`. NÃO é um draft: a ficha consolidada é
 * somente leitura e este módulo é a única projeção autorizada. */

import type {
  PrcRecordFlag,
  PrcTechnicalSnapshot,
} from "./api/productRegistrationApi";

export type SnapshotSheetData = Record<string, unknown>;

function entryValue(entry: unknown): unknown {
  if (typeof entry !== "object" || entry === null) return undefined;
  const e = entry as { coverageState?: string; value?: unknown };
  return e.coverageState === "present" ? e.value : undefined;
}

/** `fields{path:{value,coverageState,…}}` → `{path: value}`; campos
 * com cobertura `unknown` ficam ausentes (a view exibe «—»). */
export function snapshotFieldsToSheetData(
  snapshot: PrcTechnicalSnapshot | null | undefined,
  officialCode?: string | null,
): SnapshotSheetData {
  const data: SnapshotSheetData = {};
  if (officialCode) data.officialProductCode = officialCode;
  const fields = snapshot?.fields || {};
  for (const [path, entry] of Object.entries(fields)) {
    const v = entryValue(entry);
    if (v !== undefined) data[path] = v;
  }
  return data;
}

export type SnapshotSupplierRow = {
  supplierCode: string;
  store: string;
  supplierName: string;
  partNumber: string;
  catalogNumber: string;
};

/** `supplierLinks{"code|store":{linkState,attributes}}` → linhas da
 * tabela «Código | Loja | Razão social | Part Number | Catálogo».
 * Identidade estável `supplierCode+store`, nunca posição de linha. */
export function snapshotSupplierRows(
  snapshot: PrcTechnicalSnapshot | null | undefined,
): SnapshotSupplierRow[] {
  const links = snapshot?.supplierLinks || {};
  const rows: SnapshotSupplierRow[] = [];
  for (const [key, link] of Object.entries(links)) {
    if (!link || link.linkState !== "present") continue;
    const [supplierCode = "", store = ""] = key.split("|");
    const attrs = link.attributes || {};
    const val = (name: string) => {
      const a = attrs[name];
      const v =
        typeof a === "object" && a !== null
          ? (a as { value?: unknown }).value
          : undefined;
      return v == null ? "" : String(v);
    };
    rows.push({
      supplierCode,
      store,
      supplierName: val("supplierName"),
      partNumber: val("partNumber"),
      catalogNumber: val("catalogNumber"),
    });
  }
  rows.sort(
    (a, b) =>
      a.supplierCode.localeCompare(b.supplierCode) ||
      a.store.localeCompare(b.store),
  );
  return rows;
}

/** Alvo de bandeira FIELD → path presente no snapshot? (alinhado à
 * validação fail-closed do backend — o servidor é a autoridade). */
export function snapshotHasField(
  snapshot: PrcTechnicalSnapshot | null | undefined,
  path: string,
): boolean {
  const entry = snapshot?.fields?.[path];
  return Boolean(entry && entry.coverageState === "present");
}

export function snapshotHasSupplierLink(
  snapshot: PrcTechnicalSnapshot | null | undefined,
  supplierCode: string,
  store: string,
): boolean {
  const link =
    snapshot?.supplierLinks?.[`${supplierCode}|${store}`];
  return Boolean(link && link.linkState === "present");
}

/** Filtros locais por alvo — espelham os findOpen/findResolved das
 * bandeiras de solicitação, mas no contrato record-scoped. */
export function openRecordFlagForField(
  flags: PrcRecordFlag[],
  path: string,
): PrcRecordFlag | null {
  return (
    flags.find(
      (f) =>
        f.atStatus === "OPEN" &&
        f.subject === "FIELD" &&
        f.targetPath === path,
    ) || null
  );
}

export function resolvedRecordFlagsForField(
  flags: PrcRecordFlag[],
  path: string,
): PrcRecordFlag[] {
  return flags.filter(
    (f) =>
      f.atStatus === "RESOLVED" &&
      f.subject === "FIELD" &&
      f.targetPath === path,
  );
}

export function openRecordFlagForSupplier(
  flags: PrcRecordFlag[],
  supplierCode: string,
  store: string,
  attribute: string,
): PrcRecordFlag | null {
  return (
    flags.find(
      (f) =>
        f.atStatus === "OPEN" &&
        f.subject === "SUPPLIER_LINK" &&
        f.targetAttribute === attribute &&
        f.supplierKey?.supplierCode === supplierCode &&
        f.supplierKey?.store === store,
    ) || null
  );
}

export function resolvedRecordFlagsForSupplier(
  flags: PrcRecordFlag[],
  supplierCode: string,
  store: string,
  attribute: string,
): PrcRecordFlag[] {
  return flags.filter(
    (f) =>
      f.atStatus === "RESOLVED" &&
      f.subject === "SUPPLIER_LINK" &&
      f.targetAttribute === attribute &&
      f.supplierKey?.supplierCode === supplierCode &&
      f.supplierKey?.store === store,
  );
}
