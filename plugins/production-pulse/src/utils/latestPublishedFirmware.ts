import type { FirmwareListItem } from "../api/productionPulseApi";
import { firmwareSiblingsForFamily } from "./firmwareCatalogGrouping";
import { isPublishedFirmware } from "./hubOtaKpis";

/**
 * Canonical “mais recente publicada” da família OTA (non-archived published).
 * Owner for quick “Atualizar para …” actions — do not re-find by firmwareKey ad hoc.
 */
export function latestPublishedFirmwareForFamily(
  items: FirmwareListItem[],
  firmwareKey: string,
): FirmwareListItem | null {
  const key = String(firmwareKey || "").trim();
  if (!key) return null;
  const siblings = firmwareSiblingsForFamily(items, key);
  return siblings.find(isPublishedFirmware) ?? null;
}
