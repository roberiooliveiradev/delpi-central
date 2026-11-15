/** Adaptação contratual explícita — snapshot consolidado publicado
 * (rota 13/15, schemaVersion=2) → mapa plano consumido por
 * `PrcTechnicalSheetView`. NÃO é um draft: a ficha consolidada é
 * somente leitura e este módulo é a única projeção autorizada. */

import type {
  PrcRecordFlag,
  PrcRevisionChange,
  PrcRevisionDiffSummary,
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

/* --- Diff server-side (Ux × Vy) ---------------------------------- */

export type DiffSide = "before" | "after";

export type DiffCellState =
  | { kind: "value"; text: string }
  | { kind: "not_observed" }
  | { kind: "empty" };

const SUPPLIER_PATH_RE = /^suppliers\[/;

/** `changedPaths` da revisão → campos técnicos × vínculos de
 * fornecedor — única categorização derivável do payload (UX-P1-05). */
export function summarizeChangedPaths(paths: string[] | null | undefined): {
  fieldPaths: string[];
  supplierPaths: string[];
} {
  const fieldPaths: string[] = [];
  const supplierPaths: string[] = [];
  for (const path of paths || []) {
    if (SUPPLIER_PATH_RE.test(path)) supplierPaths.push(path);
    else fieldPaths.push(path);
  }
  return { fieldPaths, supplierPaths };
}

/** Lado de uma linha de diff — `*Present === false` separa «não
 * observado naquela versão» (lacuna de cobertura do snapshot) de
 * «nulo/vazio registrado». Nunca trata ausência como remoção. */
export function diffCellState(
  change: PrcRevisionChange,
  side: DiffSide,
): DiffCellState {
  const flag =
    side === "before" ? change.beforePresent : change.afterPresent;
  const value = side === "before" ? change.before : change.after;
  if (flag === false) return { kind: "not_observed" };
  if (value === null || value === undefined || value === "") {
    return { kind: "empty" };
  }
  return { kind: "value", text: String(value) };
}

/** Identidade legível do vínculo `suppliers[code|store]` ou
 * `suppliers[code|store].attr` — nunca o path técnico cru. */
export function supplierLinkIdentity(path: string): {
  supplierCode: string;
  store: string;
  attribute: string | null;
} | null {
  const match = /^suppliers\[([^\]]+)\](?:\.(.+))?$/.exec(path);
  if (!match) return null;
  const [supplierCode = "", store = ""] = match[1].split("|");
  return { supplierCode, store, attribute: match[2] ?? null };
}

export type RevisionDiffBuckets = {
  total: number;
  /** Campos/atributos com valor observado nos dois lados e
   * alterados — única classe que pode ser chamada de «alteração
   * técnica confirmada». */
  confirmed: number;
  /** Observados pela primeira vez nesta revisão — lacuna de
   * cobertura do snapshot anterior, NÃO alteração confirmada. */
  firstObserved: number;
  /** Vínculos de fornecedor novos/removidos (mudança registrada,
   * mas semântica própria — não «campo»). */
  suppliersLinked: number;
  suppliersUnlinked: number;
  /** Observados antes e ausentes agora — pode ser remoção ou
   * redução de cobertura; reportar como «deixou de ser observado». */
  noLongerObserved: number;
};

/** Decompõe o `diffSummary` da Engineering API em classes de
 * apresentação honestas. `null` → payload antigo/sem classificação
 * (consumidor cai no resumo neutro por `changedPaths`). */
export function revisionDiffBuckets(
  summary: PrcRevisionDiffSummary | null | undefined,
): RevisionDiffBuckets | null {
  if (!summary || summary.comparable !== true) return null;
  const num = (v: number | undefined) =>
    typeof v === "number" && Number.isFinite(v) ? v : 0;
  const firstObserved =
    num(summary.fieldsNewlyObserved) +
    num(summary.suppliersNewlyObserved);
  const noLongerObserved =
    num(summary.fieldsNoLongerObserved) +
    num(summary.suppliersNoLongerObserved);
  const confirmed =
    num(summary.fieldsModified) + num(summary.suppliersModified);
  const suppliersLinked = num(summary.suppliersAdded);
  const suppliersUnlinked = num(summary.suppliersRemoved);
  const total =
    num(summary.total) ||
    confirmed +
      firstObserved +
      suppliersLinked +
      suppliersUnlinked +
      noLongerObserved;
  return {
    total,
    confirmed,
    firstObserved,
    suppliersLinked,
    suppliersUnlinked,
    noLongerObserved,
  };
}
