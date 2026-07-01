import type { Rnc8dTemplatePayload } from "../types/rnc8d";

export const RNC8D_QUANTITY_UNIT_PAIRS = [
  ["defective_quantity", "defective_quantity_unit"],
  ["batch_quantity", "batch_quantity_unit"],
  ["rejected_quantity", "rejected_quantity_unit"],
] as const satisfies ReadonlyArray<
  readonly [keyof Rnc8dTemplatePayload, keyof Rnc8dTemplatePayload]
>;

const COMBINED_QTY_UNIT_PATTERN = /^([\d]+(?:[.,]\d+)?)\s*(.*)$/u;

export function parseQuantityValue(value: unknown): number | undefined {
  if (value === null || value === undefined || value === "") {
    return undefined;
  }
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  const text = String(value).trim();
  if (!text) {
    return undefined;
  }
  const match = text.match(COMBINED_QTY_UNIT_PATTERN);
  const numeric = match?.[1] ?? text;
  const parsed = Number(numeric.replace(",", "."));
  return Number.isFinite(parsed) ? parsed : undefined;
}

export function quantityInputValue(value: unknown): string {
  const parsed = parseQuantityValue(value);
  return parsed === undefined ? "" : String(parsed);
}

export function unitInputValue(value: unknown): string {
  return typeof value === "string" ? value.trim() : "";
}

export function splitLegacyQuantityField(
  quantity: unknown,
  unit: unknown,
): { quantity?: number; unit?: string } {
  if (unitInputValue(unit)) {
    const parsed = parseQuantityValue(quantity);
    return parsed === undefined ? {} : { quantity: parsed, unit: unitInputValue(unit) };
  }
  if (typeof quantity !== "string" || !quantity.trim()) {
    const parsed = parseQuantityValue(quantity);
    return parsed === undefined ? {} : { quantity: parsed };
  }
  const match = quantity.trim().match(COMBINED_QTY_UNIT_PATTERN);
  if (!match) {
    return { unit: quantity.trim() };
  }
  const parsed = parseQuantityValue(match[1]);
  const parsedUnit = match[2]?.trim();
  return {
    ...(parsed === undefined ? {} : { quantity: parsed }),
    ...(parsedUnit ? { unit: parsedUnit } : {}),
  };
}

export function normalizeRnc8dQuantityFields(
  payload: Rnc8dTemplatePayload,
): Rnc8dTemplatePayload {
  const next: Rnc8dTemplatePayload = { ...payload };
  for (const [quantityKey, unitKey] of RNC8D_QUANTITY_UNIT_PAIRS) {
    const split = splitLegacyQuantityField(next[quantityKey], next[unitKey]);
    if (split.quantity !== undefined) {
      next[quantityKey] = split.quantity;
    }
    if (split.unit !== undefined) {
      next[unitKey] = split.unit;
    }
  }
  return next;
}

export function formatQuantityWithUnit(quantity: unknown, unit: unknown): string {
  const qty = parseQuantityValue(quantity);
  const unitText = unitInputValue(unit);
  if (qty !== undefined) {
    return unitText ? `${qty} ${unitText}` : String(qty);
  }
  if (typeof quantity === "string" && quantity.trim()) {
    return quantity.trim();
  }
  return unitText;
}
