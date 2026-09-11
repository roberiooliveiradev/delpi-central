import type { FirmwareListItem } from "../api/productionPulseApi";
import { isNewerFirmwareRelease } from "./firmwareLinkGraph";
import { isPublishedFirmware } from "./hubOtaKpis";

export type FirmwareCatalogFamilyGroup = {
  firmwareKey: string;
  displayName: string;
  driverKey: string;
  /** Newest-first (includes archived). */
  versions: FirmwareListItem[];
  /** Prefer published non-archived; else newest non-archived; else newest overall. */
  latest: FirmwareListItem;
  latestPublished: FirmwareListItem | null;
  latestPublishedId: string | null;
  versionCount: number;
  /** True when a search query matched this family (UI should auto-expand). */
  defaultExpanded: boolean;
};

function firmwareVersionSearchHaystack(item: FirmwareListItem): string {
  return [
    item.firmwareKey,
    item.driverKey,
    item.version,
    item.displayName,
    item.lifecycle,
    item.artifactSha256 ?? "",
  ]
    .join(" ")
    .toLowerCase();
}

function compareFirmwareNewestFirst(a: FirmwareListItem, b: FirmwareListItem): number {
  if (isNewerFirmwareRelease(a, b)) return -1;
  if (isNewerFirmwareRelease(b, a)) return 1;
  return a.id.localeCompare(b.id);
}

function pickFamilyHeader(versionsNewestFirst: FirmwareListItem[]): FirmwareListItem {
  const published = versionsNewestFirst.find(isPublishedFirmware);
  if (published) return published;
  const active = versionsNewestFirst.find((item) => !item.archivedAt);
  if (active) return active;
  return versionsNewestFirst[0];
}

/**
 * Groups catalog rows by OTA family (`firmwareKey`) for the Firmwares panel.
 * Unlike `uniqueFirmwareFamilies`, archived versions remain as children.
 */
export function groupFirmwareCatalogByFamily(
  items: FirmwareListItem[],
  options: { query?: string } = {},
): FirmwareCatalogFamilyGroup[] {
  const query = options.query?.trim().toLowerCase() ?? "";
  const byKey = new Map<string, FirmwareListItem[]>();

  for (const item of items) {
    const list = byKey.get(item.firmwareKey);
    if (list) {
      list.push(item);
    } else {
      byKey.set(item.firmwareKey, [item]);
    }
  }

  const groups: FirmwareCatalogFamilyGroup[] = [];

  for (const [firmwareKey, versions] of byKey) {
    const sorted = [...versions].sort(compareFirmwareNewestFirst);
    const familyMatches =
      !query || sorted.some((item) => firmwareVersionSearchHaystack(item).includes(query));
    if (!familyMatches) continue;

    const latestPublished = sorted.find(isPublishedFirmware) ?? null;
    const latest = pickFamilyHeader(sorted);

    groups.push({
      firmwareKey,
      displayName: latest.displayName?.trim() || firmwareKey,
      driverKey: latest.driverKey,
      versions: sorted,
      latest,
      latestPublished,
      latestPublishedId: latestPublished?.id ?? null,
      versionCount: sorted.length,
      defaultExpanded: Boolean(query),
    });
  }

  return groups.sort((a, b) => a.firmwareKey.localeCompare(b.firmwareKey));
}

/** Versions of one OTA family, newest-first (for detail switcher). */
export function firmwareSiblingsForFamily(
  items: FirmwareListItem[],
  firmwareKey: string,
): FirmwareListItem[] {
  return items
    .filter((item) => item.firmwareKey === firmwareKey)
    .sort(compareFirmwareNewestFirst);
}
