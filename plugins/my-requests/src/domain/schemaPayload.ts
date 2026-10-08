import {
  mapFormSchemaToFields,
  type FormSchema,
  type UiSchema,
} from "../features/raw-material-creation/mapFormSchemaToFields";
import type { RequestTypeSummary } from "../types/requests";

/** Tipos com painel de payload dedicado — o genérico não deve duplicá-los. */
const DEDICATED_PAYLOAD_TYPES = new Set(["invoice-issuance", "process-issue"]);

export function hasDedicatedPayloadPanel(
  typeCode: string | null | undefined,
): boolean {
  return DEDICATED_PAYLOAD_TYPES.has(String(typeCode || "").trim());
}

export type SchemaPayloadField = {
  name: string;
  label: string;
  hint?: string;
  value: string;
};

function formatSchemaValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "boolean") return value ? "Sim" : "Não";
  if (typeof value === "string" || typeof value === "number") {
    const text = String(value).trim();
    return text || "—";
  }
  return "";
}

/** Campos renderizáveis do payload conforme o form_schema do tipo (escalares). */
export function schemaPayloadFields(
  requestType: RequestTypeSummary | null | undefined,
  payload: Record<string, unknown> | null | undefined,
): SchemaPayloadField[] {
  if (!requestType || !payload || hasDedicatedPayloadPanel(requestType.code)) {
    return [];
  }
  const mode = (requestType.presentation_mode || "").trim().toLowerCase();
  if (mode === "specialized") return [];
  const fields = mapFormSchemaToFields(
    (requestType.form_schema || {}) as FormSchema,
    (requestType.ui_schema || {}) as UiSchema,
  );
  const out: SchemaPayloadField[] = [];
  for (const field of fields) {
    const value = formatSchemaValue(payload[field.name]);
    if (!value) continue;
    out.push({ name: field.name, label: field.label, hint: field.hint, value });
  }
  return out;
}
