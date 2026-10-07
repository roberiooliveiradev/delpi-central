import {
  INPUT_VARIABLE_KEY_PATTERN,
  resolveInputVariableBinding,
  type ComunicadoBlock,
  type ComunicadoInputValueSchema,
} from "@delpi/tv-dashboard-presentation";

import type { DataParamSchema } from "./dataParamSchema";

/** Tipo exibido no inspetor — data é `string` + `format: "date"` (shape de paramSchema). */
export type InputVariableTypeId = "string" | "date" | "integer" | "number" | "boolean";

export const INPUT_VARIABLE_TYPE_OPTIONS: Array<{ value: InputVariableTypeId; label: string }> = [
  { value: "string", label: "Texto" },
  { value: "date", label: "Data" },
  { value: "integer", label: "Número inteiro" },
  { value: "number", label: "Número" },
  { value: "boolean", label: "Sim / Não" },
];

/** Chave sintética do campo de valor padrão no DataParamFields (sem heurística por nome). */
export const INPUT_VARIABLE_DEFAULT_FIELD = "defaultValue";

export type InputVariableKeyIssue = "invalid" | "duplicate";

export function valueSchemaTypeId(schema: ComunicadoInputValueSchema | undefined): InputVariableTypeId {
  if (!schema) return "string";
  if (schema.type === "string" && schema.format === "date") return "date";
  return schema.type;
}

export function valueSchemaForTypeId(typeId: InputVariableTypeId): ComunicadoInputValueSchema {
  if (typeId === "date") return { type: "string", format: "date" };
  return { type: typeId };
}

/** Opções editáveis só para texto/número; data e sim/não não usam enum. */
export function valueSchemaSupportsEnum(schema: ComunicadoInputValueSchema | undefined): boolean {
  return Boolean(schema) && schema?.type !== "boolean" && schema?.format !== "date";
}

export function variableKeyIssue(
  key: string,
  blocks: ComunicadoBlock[] | undefined | null,
  selfId: string,
): InputVariableKeyIssue | null {
  if (!INPUT_VARIABLE_KEY_PATTERN.test(key)) return "invalid";
  const duplicated = (blocks ?? []).some(
    (block) =>
      block.id !== selfId &&
      block.type === "input" &&
      resolveInputVariableBinding(block.input)?.key === key,
  );
  return duplicated ? "duplicate" : null;
}

/** Refs `input.<key>` publicadas pelo slide — chave duplicada fica de fora (backend a rejeita). */
export function listSlideInputVariableRefs(
  blocks: ComunicadoBlock[] | undefined | null,
): Array<{ key: string; label: string }> {
  const byKey = new Map<string, { key: string; label: string; count: number }>();
  for (const block of blocks ?? []) {
    if (block.type !== "input") continue;
    const key = resolveInputVariableBinding(block.input)?.key;
    if (!key) continue;
    const entry = byKey.get(key);
    if (entry) entry.count += 1;
    else byKey.set(key, { key, label: block.input.label?.trim() || key, count: 1 });
  }
  return [...byKey.values()]
    .filter((entry) => entry.count === 1)
    .map(({ key, label }) => ({ key, label }));
}

export function suggestVariableKey(blocks: ComunicadoBlock[] | undefined | null): string {
  const used = new Set(
    (blocks ?? [])
      .map((block) => (block.type === "input" ? resolveInputVariableBinding(block.input)?.key : null))
      .filter(Boolean),
  );
  let index = 1;
  while (used.has(`variable_${index}`)) index += 1;
  return `variable_${index}`;
}

/** `valor=rótulo` por linha (rótulo opcional). */
export function formatEnumOptionsText(schema: ComunicadoInputValueSchema | undefined): string {
  return (schema?.enum ?? [])
    .map((value) => {
      const label = schema?.enumLabels?.[String(value)];
      return label ? `${value}=${label}` : String(value);
    })
    .join("\n");
}

export type ParsedEnumOptions =
  | { ok: true; enum?: Array<string | number>; enumLabels?: Record<string, string> }
  | { ok: false; line: number };

export function parseEnumOptionsText(
  text: string,
  type: ComunicadoInputValueSchema["type"],
): ParsedEnumOptions {
  const values: Array<string | number> = [];
  const labels: Record<string, string> = {};
  const lines = text.split("\n");
  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index]?.trim() ?? "";
    if (!line) continue;
    const separator = line.indexOf("=");
    const rawValue = (separator >= 0 ? line.slice(0, separator) : line).trim();
    const label = separator >= 0 ? line.slice(separator + 1).trim() : "";
    let value: string | number = rawValue;
    if (type === "integer" || type === "number") {
      const parsed = Number(rawValue);
      if (!rawValue || !Number.isFinite(parsed) || (type === "integer" && !Number.isInteger(parsed))) {
        return { ok: false, line: index + 1 };
      }
      value = parsed;
    }
    if (!rawValue || values.includes(value)) return { ok: false, line: index + 1 };
    values.push(value);
    if (label) labels[String(value)] = label;
  }
  if (values.length === 0) return { ok: true };
  return {
    ok: true,
    enum: values,
    ...(Object.keys(labels).length > 0 ? { enumLabels: labels } : {}),
  };
}

/** Valor bruto do campo de padrão → escalar do valueSchema (`null` = sem padrão). */
export function parseVariableDefault(
  raw: string,
  schema: ComunicadoInputValueSchema,
): string | number | boolean | null {
  if (raw === "") return null;
  if (schema.type === "boolean") return raw === "true";
  if (schema.type === "integer" || schema.type === "number") {
    const parsed = Number(raw);
    if (!Number.isFinite(parsed)) return null;
    return schema.type === "integer" ? Math.trunc(parsed) : parsed;
  }
  return raw;
}

export function buildVariableDefaultEditorSchema(schema: ComunicadoInputValueSchema): DataParamSchema {
  return {
    [INPUT_VARIABLE_DEFAULT_FIELD]: {
      type: schema.type,
      label: "Valor padrão",
      optional: true,
      expressionAllowed: false,
      ...(schema.format ? { format: schema.format } : {}),
      ...(schema.enum?.length ? { enum: [...schema.enum] } : {}),
      ...(schema.enumLabels ? { enumLabels: { ...schema.enumLabels } } : {}),
    },
  };
}
