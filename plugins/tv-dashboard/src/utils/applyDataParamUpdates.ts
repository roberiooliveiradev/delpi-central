import type { DataParamSchema } from "../components/DataParamFields";

/** Converte raw de UI (string) para valor tipado do schema. */
export function parseDataParamRaw(
  key: string,
  raw: string,
  schema: DataParamSchema | undefined,
): string | number | boolean | undefined {
  const fieldType = schema?.[key]?.type;
  if (!raw.trim()) return undefined;
  if (fieldType === "integer" || fieldType === "number") return Number(raw);
  if (fieldType === "boolean") return raw === "true";
  return raw.trim();
}

/**
 * Aplica várias chaves de parâmetro de uma vez (evita race com binding stale
 * quando Período + competence / datas mudam juntos).
 */
export function applyDataParamRawUpdates(
  current: Record<string, string | number | boolean | null | undefined> | undefined,
  updates: Record<string, string>,
  schema: DataParamSchema | undefined,
): Record<string, string | number | boolean> {
  const next: Record<string, string | number | boolean> = { ...(current ?? {}) };
  for (const [key, raw] of Object.entries(updates)) {
    const parsed = parseDataParamRaw(key, raw, schema);
    if (parsed === undefined) delete next[key];
    else next[key] = parsed;
  }
  return next;
}
