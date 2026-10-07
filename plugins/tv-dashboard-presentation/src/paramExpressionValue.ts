import type { ParamExpressionSpec } from "./comunicadoTypes";

/** Marker wire — `params[name] = {expression: {version, expression}}`. Nunca avalia. */
export function isParamExpressionValue(value: unknown): value is ParamExpressionSpec {
  if (value == null || typeof value !== "object" || Array.isArray(value)) {
    return false;
  }
  const inner = (value as Record<string, unknown>).expression;
  return inner != null && typeof inner === "object" && !Array.isArray(inner);
}
