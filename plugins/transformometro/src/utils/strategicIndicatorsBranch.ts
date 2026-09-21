import type { DashboardViewMode } from "../data/api/transformometroApi";

/**
 * Same SI branch rule as the Engineering dashboard:
 * a single selected unit is forwarded; consolidated / multi-unit omit branch.
 */
export function resolveStrategicIndicatorsBranch(
  viewMode: DashboardViewMode,
  filialIds: readonly string[],
): string | undefined {
  if (viewMode === "consolidated") {
    return undefined;
  }
  if (filialIds.length !== 1) {
    return undefined;
  }
  const code = filialIds[0]?.trim();
  return code || undefined;
}
