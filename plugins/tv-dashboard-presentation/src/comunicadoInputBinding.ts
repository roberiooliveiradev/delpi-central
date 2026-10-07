import type {
  ComunicadoInputBinding,
  ComunicadoInputBlock,
  ComunicadoInputValueSchema,
  ComunicadoInputValueType,
} from "./comunicadoTypes";

/** Sintaxe de `binding.key` — espelho de `INPUT_VARIABLE_KEY_PATTERN` na TV API. */
export const INPUT_VARIABLE_KEY_PATTERN = /^[A-Za-z_][A-Za-z0-9_]{0,63}$/;

/** Prefixo do namespace de variáveis de input em ExpressionSpec (`input.<key>`). */
export const INPUT_EXPRESSION_REF_PREFIX = "input.";

const VALUE_TYPES: readonly ComunicadoInputValueType[] = ["string", "integer", "number", "boolean"];

type InputConfig = ComunicadoInputBlock["input"] | undefined | null;

/** Binding variável válido do input; `null` = legado (`paramKey`). */
export function resolveInputVariableBinding(input: InputConfig): ComunicadoInputBinding | null {
  const binding = input?.binding;
  if (!binding || binding.kind !== "variable") return null;
  const key = String(binding.key ?? "").trim();
  return key ? { kind: "variable", key } : null;
}

export function isInputVariableBlock(block: ComunicadoInputBlock): boolean {
  return resolveInputVariableBinding(block.input) !== null;
}

/** Chave exibida/identificadora do input: variável do slide ou paramKey legado. */
export function resolveInputBindingKey(input: InputConfig): string {
  return resolveInputVariableBinding(input)?.key ?? String(input?.paramKey ?? "").trim();
}

/** Normaliza `binding` persistido (load). Kind desconhecido é descartado. */
export function normalizeInputBinding(raw: unknown): ComunicadoInputBinding | undefined {
  if (!raw || typeof raw !== "object") return undefined;
  const record = raw as Record<string, unknown>;
  if (record.kind !== "variable") return undefined;
  const key = typeof record.key === "string" ? record.key.trim() : "";
  return { kind: "variable", key };
}

/** Normaliza `valueSchema` persistido (load) preservando somente o contrato suportado. */
export function normalizeInputValueSchema(raw: unknown): ComunicadoInputValueSchema | undefined {
  if (!raw || typeof raw !== "object") return undefined;
  const record = raw as Record<string, unknown>;
  const type = VALUE_TYPES.find((item) => item === record.type);
  if (!type) return undefined;
  const schema: ComunicadoInputValueSchema = { type };
  if (record.format === "date") schema.format = "date";
  if (Array.isArray(record.enum)) {
    const values = record.enum.filter(
      (item): item is string | number =>
        typeof item === "string" || (typeof item === "number" && Number.isFinite(item)),
    );
    if (values.length > 0) schema.enum = values;
  }
  if (record.enumLabels && typeof record.enumLabels === "object" && !Array.isArray(record.enumLabels)) {
    const labels: Record<string, string> = {};
    for (const [key, label] of Object.entries(record.enumLabels as Record<string, unknown>)) {
      if (typeof label === "string" && label.trim()) labels[key] = label.trim();
    }
    if (Object.keys(labels).length > 0) schema.enumLabels = labels;
  }
  return schema;
}

/** Cópia do schema para serialização (sem aliasing com o estado do editor). */
export function cloneInputValueSchema(schema: ComunicadoInputValueSchema): ComunicadoInputValueSchema {
  return {
    type: schema.type,
    ...(schema.format ? { format: schema.format } : {}),
    ...(schema.enum?.length ? { enum: [...schema.enum] } : {}),
    ...(schema.enumLabels && Object.keys(schema.enumLabels).length > 0
      ? { enumLabels: { ...schema.enumLabels } }
      : {}),
  };
}
