/**
 * Display-only conversion for Protheus UM=MI (1 MI = 1000 pieces).
 * Does not mutate API/OTD contracts — only presentation.
 */

import { formatQuantity } from "./format";

export const MI_TO_PIECES_FACTOR = 1000;

export type QuantityDisplayMode = "catalog" | "pieces";

export const DEFAULT_QUANTITY_DISPLAY_MODE: QuantityDisplayMode = "catalog";

export const QUANTITY_DISPLAY_STORAGE_KEY = "commercial:quantity-display-mode";

export type DisplayQuantity = {
  value: number;
  unit: string;
  converted: boolean;
};

export function normalizeQuantityDisplayMode(
  value: string | null | undefined,
): QuantityDisplayMode {
  return value === "pieces" ? "pieces" : DEFAULT_QUANTITY_DISPLAY_MODE;
}

export function isMilheiroUnit(unit: string | null | undefined): boolean {
  return (unit || "").trim().toUpperCase() === "MI";
}

/**
 * Catalog mode keeps native qty/UM. Pieces mode only converts when UM is MI.
 */
export function resolveDisplayQuantity(
  quantity: number | null | undefined,
  unit: string | null | undefined,
  mode: QuantityDisplayMode = DEFAULT_QUANTITY_DISPLAY_MODE,
): DisplayQuantity {
  const value = Number(quantity);
  const safe = Number.isFinite(value) ? value : 0;
  const catalogUnit = (unit || "").trim();
  if (mode === "pieces" && isMilheiroUnit(catalogUnit)) {
    return {
      value: safe * MI_TO_PIECES_FACTOR,
      unit: "PC",
      converted: true,
    };
  }
  return {
    value: safe,
    unit: catalogUnit || "—",
    converted: false,
  };
}

export function formatDisplayQuantity(
  quantity: number | null | undefined,
  unit: string | null | undefined,
  mode: QuantityDisplayMode = DEFAULT_QUANTITY_DISPLAY_MODE,
): string {
  const resolved = resolveDisplayQuantity(quantity, unit, mode);
  const qty = formatQuantity(resolved.value);
  if (!resolved.unit || resolved.unit === "—") return qty;
  return `${qty} ${resolved.unit}`;
}
