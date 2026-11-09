/** Construção pura do payload de intake PRC — separada da página para
 * teste unitário direto das regras de justificativa contextual.
 *
 * D14-FIX: razões são individuais e só viajam quando o campo/atributo
 * correspondente está efetivamente alterado (diff D13 no update,
 * preenchimento no create). Desfazer a alteração retira a razão do
 * payload sem apagar o rascunho local da linha. */

import type {
  PrcIntakeBody,
  PrcReferenceData,
  PrcSupplierLinkChange,
} from "./api/productRegistrationApi";
import {
  linkKeyOf,
  type PrcLinkOp,
  type PrcScalarChange,
} from "./prcDiff";
import {
  supplierRowsToPayload,
  type SupplierRow,
} from "./prcSuppliers";

export const PRC_PORTAL_SOURCE = "portal-engineering";

/** supplierLinkChanges[] com razões no escopo correto: `reason` é a
 * razão da operação (add/remove); `fieldReasons` só inclui o atributo
 * quando ele consta em `op.fields` — PN e Catálogo nunca compartilham
 * razão, e atributo revertido ao baseline não leva justificativa. */
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
    if (
      "partNumber" in fields &&
      row?.pnReason?.trim()
    ) {
      fieldReasons.partNumber = row.pnReason.trim();
    }
    if (
      "catalogNumber" in fields &&
      row?.catReason?.trim()
    ) {
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

/** Canal `reasons` do intake create — mesmo vocabulário do update:
 * `fields` por path técnico preenchido e `supplierLinks` por vínculo
 * incluído (razão da inclusão + razões por atributo preenchido).
 * Retorna `undefined` quando nenhuma razão foi registrada. */
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
  refData: PrcReferenceData | null;
  values: Record<string, string>;
  reasons: Record<string, string>;
  suppliers: SupplierRow[];
}): PrcIntakeBody {
  const { refData, values, reasons, suppliers } = args;
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
    source: PRC_PORTAL_SOURCE,
    requestType: "create",
    productType: refData?.productTypes?.[0] || "raw_material",
    schemaVersion: refData?.schemaVersion || 1,
    requestedData,
    ...(createReasons ? { reasons: createReasons } : {}),
  };
}

export function buildUpdateIntakeBody(args: {
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
    source: PRC_PORTAL_SOURCE,
    requestType: "update",
    productType: refData?.productTypes?.[0] || "raw_material",
    schemaVersion: refData?.schemaVersion || 1,
    officialProductCode: officialCode.trim(),
    changes,
    supplierLinkChanges: linkChangesWithReasons(linkOps, suppliers),
    ...(baselineFingerprint
      ? { baselineFingerprint }
      : {}),
    ...(editContextReadAt ? { editContextReadAt } : {}),
  };
}
