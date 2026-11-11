/** PRC — adaptadores puros de contrato do Product Registration.
 *
 * Fonte única dos mapeamentos form-estado ↔ contrato da Engineering API
 * (`/v1/product-registration`), consumidos por `plugins/engineering` e
 * `plugins/my-requests` (PRC-REF-023-F03/F04). A autoridade de validação
 * e de domínio é sempre o backend — aqui há apenas shaping de payload,
 * diff de baseline e identidade local de linhas/arquivos. Nenhuma regra
 * de negócio é decidida no cliente.
 */

// ---------------------------------------------------------------------
// Contrato (espelho estrutural do OpenAPI da Engineering API — inglês).
// ---------------------------------------------------------------------

export type PrcFieldSpec = {
  path: string;
  kind: string;
  requiredCreateIntake: boolean;
  verifiable: boolean;
  officialField?: string | null;
  enumValues?: string[] | null;
  maxLength: number;
  note?: string | null;
};

export type PrcReferenceData = {
  schemaVersion: number;
  productTypes: string[];
  requestTypes: string[];
  statuses: string[];
  sources: string[];
  fields: PrcFieldSpec[];
  editableDraftPaths: string[];
  supplierKeys: { required: string[]; optional: string[] };
};

export type PrcSupplierLinkChange = {
  operation: "update" | "add" | "remove";
  key: { supplierCode: string; store: string };
  fields: { partNumber?: string; catalogNumber?: string };
  reason?: string;
  fieldReasons?: { partNumber?: string; catalogNumber?: string };
};

export type PrcIntakeBody = {
  source: string;
  externalRequestId?: string | null;
  externalItemId?: string | null;
  requestType: "create" | "update";
  productType: string;
  schemaVersion: number;
  requestedData?: Record<string, unknown> | null;
  officialProductCode?: string | null;
  baseRevision?: number | null;
  changes?: Array<{
    path: string;
    proposedValue: unknown;
    reason: string;
  }> | null;
  supplierLinkChanges?: PrcSupplierLinkChange[] | null;
  reasons?: {
    fields?: Record<string, string>;
    supplierLinks?: Array<{
      key: { supplierCode: string; store: string };
      reason?: string;
      fieldReasons?: { partNumber?: string; catalogNumber?: string };
    }>;
  } | null;
  baselineFingerprint?: string | null;
  editContextReadAt?: string | null;
};

// ---------------------------------------------------------------------
// Diff escalar (D13).
// ---------------------------------------------------------------------

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

// ---------------------------------------------------------------------
// Linhas de fornecedor (modelo visual do formulário).
// ---------------------------------------------------------------------

export type SupplierRowOrigin = "official" | "draft";

export type SupplierRow = {
  /** Identidade local estável da linha UI — nunca índice de array. */
  rowId: string;
  origin: SupplierRowOrigin;
  supplierCode: string;
  store: string;
  supplierName: string;
  supplierShortName?: string;
  partNumber: string;
  catalogNumber: string;
  query: string;
  searchOpen?: boolean;
  pnReason?: string;
  catReason?: string;
  opReason?: string;
  pnReasonOpen?: boolean;
  catReasonOpen?: boolean;
  opReasonOpen?: boolean;
  selectionError?: string;
};

let _rowSeq = 0;

export function newSupplierRowId(prefix = "row"): string {
  _rowSeq += 1;
  const rand =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `r${Date.now().toString(36)}${Math.random().toString(36).slice(2, 8)}`;
  return `${prefix}-${_rowSeq}-${rand}`;
}

export function supplierOfficialKey(code: string, store: string): string {
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

/** Linhas candidatas (`draft`) cuja chave oficial já existe em outra
 * linha — marcadas como duplicadas descartáveis. */
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
    const officials = group.filter((r) => r.origin === "official");
    if (officials.length > 1) {
      for (const r of officials) dups.add(r.rowId);
    }
  }
  return dups;
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

export function supplierHitMain(hit: {
  supplier_name?: string;
}): string {
  return String(hit.supplier_name ?? "").trim();
}

/** Hit SA2 — razão social (`A2_NOME`) é a linha principal. */
export function supplierHitLabel(hit: {
  supplier_code?: string;
  supplier_store?: string;
  supplier_name?: string;
}): string {
  return supplierHitMain(hit);
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

// ---------------------------------------------------------------------
// Diff de vínculos SA5 (linha da tabela vs baseline oficial).
// ---------------------------------------------------------------------

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
  ambiguousOfficialKeys: string[];
  conflictingKeys: string[];
};

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
      if (officialByKey.has(key)) continue;
      if (removeRowIds.has(row.rowId)) continue;
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

// ---------------------------------------------------------------------
// Construção do payload de intake (create + update).
// ---------------------------------------------------------------------

/** supplierLinkChanges[] com razões no escopo correto. */
export function linkChangesWithReasons(
  ops: PrcLinkOp[],
  rows: SupplierRow[],
): PrcSupplierLinkChange[] {
  const rowByKey = new Map(
    rows.map((r) => [linkKeyOf(r.supplierCode, r.store), r]),
  );
  return ops.map((op) => {
    const row = rowByKey.get(
      linkKeyOf(op.key.supplierCode, op.key.store),
    );
    const fields = op.operation === "remove" ? {} : op.fields;
    const fieldReasons: Record<string, string> = {};
    if ("partNumber" in fields && row?.pnReason?.trim()) {
      fieldReasons.partNumber = row.pnReason.trim();
    }
    if ("catalogNumber" in fields && row?.catReason?.trim()) {
      fieldReasons.catalogNumber = row.catReason.trim();
    }
    return {
      operation: op.operation,
      key: op.key,
      fields,
      reason: (row?.opReason || "").trim(),
      ...(Object.keys(fieldReasons).length ? { fieldReasons } : {}),
    };
  });
}

export function buildCreateReasons(
  values: Record<string, string>,
  reasons: Record<string, string>,
  suppliers: SupplierRow[],
): NonNullable<PrcIntakeBody["reasons"]> | undefined {
  const fields: Record<string, string> = {};
  for (const [path, raw] of Object.entries(reasons)) {
    const text = raw.trim();
    if (text && (values[path] || "").trim()) {
      fields[path] = text;
    }
  }
  const supplierLinks = suppliers
    .filter((r) => r.supplierCode.trim() && r.store.trim())
    .map((r) => {
      const entry: {
        key: { supplierCode: string; store: string };
        reason?: string;
        fieldReasons?: { partNumber?: string; catalogNumber?: string };
      } = {
        key: {
          supplierCode: r.supplierCode.trim(),
          store: r.store.trim(),
        },
      };
      if (r.opReason?.trim()) entry.reason = r.opReason.trim();
      const fr: { partNumber?: string; catalogNumber?: string } = {};
      if (r.pnReason?.trim() && r.partNumber.trim()) {
        fr.partNumber = r.pnReason.trim();
      }
      if (r.catReason?.trim() && r.catalogNumber.trim()) {
        fr.catalogNumber = r.catReason.trim();
      }
      if (Object.keys(fr).length) entry.fieldReasons = fr;
      return entry;
    })
    .filter((e) => e.reason || e.fieldReasons);
  if (!Object.keys(fields).length && !supplierLinks.length) {
    return undefined;
  }
  return {
    ...(Object.keys(fields).length ? { fields } : {}),
    ...(supplierLinks.length ? { supplierLinks } : {}),
  };
}

export function buildCreateIntakeBody(args: {
  source: string;
  refData: PrcReferenceData | null;
  values: Record<string, string>;
  reasons: Record<string, string>;
  suppliers: SupplierRow[];
}): PrcIntakeBody {
  const { source, refData, values, reasons, suppliers } = args;
  const requestedData: Record<string, unknown> = {};
  for (const spec of refData?.fields || []) {
    if (spec.path === "suppliers") continue;
    const raw = (values[spec.path] || "").trim();
    if (raw || spec.requiredCreateIntake || spec.kind === "text") {
      requestedData[spec.path] = raw;
    }
  }
  requestedData.suppliers = supplierRowsToPayload(suppliers);
  const createReasons = buildCreateReasons(values, reasons, suppliers);
  return {
    source,
    requestType: "create",
    productType: refData?.productTypes?.[0] || "raw_material",
    schemaVersion: refData?.schemaVersion || 1,
    requestedData,
    ...(createReasons ? { reasons: createReasons } : {}),
  };
}

export function buildUpdateIntakeBody(args: {
  source: string;
  refData: PrcReferenceData | null;
  officialCode: string;
  scalarDiff: PrcScalarChange[];
  linkOps: PrcLinkOp[];
  reasons: Record<string, string>;
  suppliers: SupplierRow[];
  baselineFingerprint?: string | null;
  editContextReadAt?: string | null;
}): PrcIntakeBody {
  const {
    source,
    refData,
    officialCode,
    scalarDiff,
    linkOps,
    reasons,
    suppliers,
    baselineFingerprint,
    editContextReadAt,
  } = args;
  const changes = scalarDiff.map((change) => ({
    path: change.path,
    proposedValue: change.after,
    reason: (reasons[change.path] || "").trim(),
  }));
  return {
    source,
    requestType: "update",
    productType: refData?.productTypes?.[0] || "raw_material",
    schemaVersion: refData?.schemaVersion || 1,
    officialProductCode: officialCode.trim(),
    changes,
    supplierLinkChanges: linkChangesWithReasons(linkOps, suppliers),
    ...(baselineFingerprint ? { baselineFingerprint } : {}),
    ...(editContextReadAt ? { editContextReadAt } : {}),
  };
}

// ---------------------------------------------------------------------
// Anexos — pré-validação client-side e identidade estável local.
// ---------------------------------------------------------------------

export const PRC_ATTACHMENT_ACCEPT = ".pdf,.png,.jpg,.jpeg,.webp";
export const PRC_ATTACHMENT_MAX_BYTES = 10 * 1024 * 1024;
export const PRC_ATTACHMENT_MAX_COUNT = 10;
export const PRC_ATTACHMENT_MAX_MB = PRC_ATTACHMENT_MAX_BYTES / 1024 / 1024;

const _ATT_EXT_OK = new Set(["pdf", "png", "jpg", "jpeg", "webp"]);

export type PrcAttachmentLocalCheck =
  | { ok: true }
  | { ok: false; error: string };

export function prcCheckAttachmentFile(
  file: File,
): PrcAttachmentLocalCheck {
  const ext = (file.name.split(".").pop() || "").toLowerCase();
  if (!_ATT_EXT_OK.has(ext)) {
    return {
      ok: false,
      error: "Tipo não permitido. Envie PDF ou imagem (PNG, JPEG, WebP).",
    };
  }
  if (file.size <= 0) {
    return { ok: false, error: "Arquivo vazio não é permitido." };
  }
  if (file.size > PRC_ATTACHMENT_MAX_BYTES) {
    return {
      ok: false,
      error: `Arquivo excede o limite de ${PRC_ATTACHMENT_MAX_MB} MB.`,
    };
  }
  return { ok: true };
}

export function prcFormatSize(bytes: number): string {
  if (!bytes || bytes <= 0) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

/** Rótulos pt-BR dos estados de anexo do contrato (UI copy). */
export const PRC_ATTACHMENT_STATE_LABELS: Record<string, string> = {
  PENDING_SCAN: "Em análise",
  AVAILABLE: "Disponível",
  REJECTED: "Rejeitado",
  QUARANTINED: "Em quarentena",
  DELETED: "Removido",
};

export const PRC_ATTACHMENT_MEDIA_LABELS: Record<string, string> = {
  "application/pdf": "PDF",
  "image/png": "PNG",
  "image/jpeg": "JPEG",
  "image/webp": "WebP",
};

export interface PrcSupportFile {
  localId: string;
  file: File;
}

let _sfSeq = 0;

/** Id estável único por seleção (nunca índice de array). */
export function newSupportFileId(file: File): string {
  _sfSeq += 1;
  return `sf-${_sfSeq}-${file.name}-${file.size}-${file.lastModified}`;
}

export interface PrcSupportPickResult {
  files: PrcSupportFile[];
  errors: Record<string, string>;
}

export function addSupportFiles(
  existing: PrcSupportFile[],
  incoming: File[],
  maxCount: number,
): PrcSupportPickResult {
  const errors: Record<string, string> = {};
  const accepted: PrcSupportFile[] = [];
  for (const file of incoming) {
    const entry: PrcSupportFile = {
      localId: newSupportFileId(file),
      file,
    };
    const check = prcCheckAttachmentFile(file);
    if (check.ok) {
      accepted.push(entry);
    } else {
      errors[entry.localId] = check.error;
    }
  }
  return {
    files: [...existing, ...accepted].slice(0, maxCount),
    errors,
  };
}

export function removeSupportFile(
  existing: PrcSupportFile[],
  localId: string,
): PrcSupportFile[] {
  return existing.filter((entry) => entry.localId !== localId);
}

// ---------------------------------------------------------------------
// Rótulos pt-BR do contrato (UI copy compartilhada — chaves técnicas
// permanecem em inglês).
// ---------------------------------------------------------------------

export const PRC_STATUS_LABELS: Record<string, string> = {
  submitted: "Enviada",
  in_progress: "Em atendimento",
  needs_information: "Aguardando informações",
  needs_correction: "Devolvida para correção",
  under_review: "Em revisão",
  completed: "Concluída",
  rejected: "Rejeitada",
};

export const PRC_STATUS_VARIANTS: Record<
  string,
  "neutral" | "info" | "success" | "warning" | "danger"
> = {
  submitted: "info",
  in_progress: "info",
  needs_information: "warning",
  needs_correction: "warning",
  under_review: "warning",
  completed: "success",
  rejected: "danger",
};

export const PRC_TYPE_LABELS: Record<string, string> = {
  create: "Criação",
  update: "Alteração",
};

export const PRC_FIELD_LABELS: Record<string, string> = {
  officialProductCode: "Código oficial",
  description: "Descrição",
  group: "Grupo",
  productKind: "Tipo",
  unit: "Unidade",
  defaultWarehouse: "Armazém padrão",
  thirdPartyProduct: "Produto de terceiros",
  accountingAccount: "Conta contábil",
  customerReference: "Referência do cliente",
  suppliers: "Fornecedores",
};

export const PRC_SUPPLIER_LABELS: Record<string, string> = {
  supplierCode: "Código",
  store: "Loja",
  supplierName: "Razão social",
  partNumber: "Part Number",
  catalogNumber: "Catálogo",
};

export const PRC_ENUM_OPTION_LABELS: Record<
  string,
  Record<string, string>
> = {
  productKind: {
    MP: "Matéria-prima",
    PA: "Produto acabado",
    PI: "Produto intermediário",
  },
  thirdPartyProduct: {
    "1": "Não",
    "2": "Sim",
  },
};

export const PRC_FIELD_HELP: Record<string, string> = {
  officialProductCode:
    "Código atribuído ao produto no TOTVS. Preserve zeros à esquerda.",
  description:
    "Descrição técnica utilizada para identificar o produto.",
  group:
    "Classificação do produto nos grupos cadastrados no TOTVS.",
  productKind:
    "Classificação do tipo de produto no ERP.",
  unit:
    "Unidade de medida utilizada no cadastro e movimentação.",
  defaultWarehouse:
    "Armazém normalmente associado ao produto.",
  accountingAccount:
    "Conta usada na classificação contábil do produto.",
  thirdPartyProduct:
    "Indica a classificação do produto quanto à propriedade de terceiros, conforme cadastro oficial.",
  customerReference:
    "Código ou referência fornecida pelo cliente para identificar o produto.",
  suppliers:
    "Vínculos do produto com fornecedores oficiais (código, loja e atributos).",
};

// ---------------------------------------------------------------------
// Catálogos — mapeamento campo→kind e opções de select.
// ---------------------------------------------------------------------

/** path do campo → `kind` da rota BFF `reference-data/catalogs/{kind}`. */
export const PRC_CATALOG_KINDS: Record<string, string> = {
  group: "product-groups",
  unit: "units",
  defaultWarehouse: "warehouses",
  accountingAccount: "accounting-accounts",
};

export type PrcCatalogOption = { value: string; label: string };

export type PrcCatalogOptionItem = {
  code: string;
  label?: string | null;
  description?: string | null;
};

/** `code — label` pesquisável pelos dois lados; código nunca coage. */
export function catalogOptions(
  items: readonly PrcCatalogOptionItem[],
): PrcCatalogOption[] {
  return (items ?? [])
    .filter((item) => item != null && item.code != null)
    .map((item) => {
      const code = String(item.code);
      const label = String(item.label ?? item.description ?? "").trim();
      return { value: code, label: label ? `${code} — ${label}` : code };
    });
}

/** Enum do domínio → opções rotuladas (`código — descrição funcional`). */
export function enumOptions(
  path: string,
  values: readonly string[],
): PrcCatalogOption[] {
  const labels = PRC_ENUM_OPTION_LABELS[path] ?? {};
  return values.map((v) => ({
    value: v,
    label: labels[v] ? `${v} — ${labels[v]}` : v,
  }));
}

/** Opções do Select incluindo o valor selecionado quando não está na
 * lista carregada — a escolha do usuário nunca some nem vira texto
 * livre. */
export function withSelectedOption(
  options: readonly PrcCatalogOption[],
  selected: string,
): PrcCatalogOption[] {
  if (!selected || options.some((o) => o.value === selected)) {
    return [...options];
  }
  return [
    { value: selected, label: `${selected} — valor selecionado` },
    ...options,
  ];
}
