import { isNumericDisplayCategory, specFromPresetId } from "./catalog";
import type { DisplayFormatSpec } from "./types";

export function togglePercentDisplayFormat(_current?: DisplayFormatSpec | null): DisplayFormatSpec {
  return specFromPresetId("percent");
}

export function toggleThousandsDisplayFormat(
  current?: DisplayFormatSpec | null,
): DisplayFormatSpec {
  const places =
    typeof current?.decimalPlaces === "number" && Number.isFinite(current.decimalPlaces)
      ? current.decimalPlaces
      : 2;
  return {
    category: "number",
    presetId: "number-thousands",
    decimalPlaces: places,
    useThousandsSeparator: true,
  };
}

export function bumpDisplayFormatDecimalPlaces(
  current: DisplayFormatSpec | null | undefined,
  delta: number,
): DisplayFormatSpec {
  const base =
    current && isNumericDisplayCategory(current.category)
      ? { ...current }
      : specFromPresetId("number-2");
  const fallback = base.category === "percent" ? 1 : base.category === "currency" ? 2 : 2;
  const currentPlaces =
    typeof base.decimalPlaces === "number" && Number.isFinite(base.decimalPlaces)
      ? base.decimalPlaces
      : fallback;
  return {
    ...base,
    decimalPlaces: Math.min(8, Math.max(0, Math.trunc(currentPlaces + delta))),
  };
}
