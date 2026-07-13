import { dataCatalogEntries } from "./demos/data";
import { exportCatalogEntries } from "./demos/export";
import { feedbackCatalogEntries } from "./demos/feedback";
import { formsCatalogEntries } from "./demos/forms";
import { helpCatalogEntries } from "./demos/help";
import { layoutCatalogEntries } from "./demos/layout";
import { sandboxCatalogEntries } from "./demos/sandbox";
import type { CatalogEntry, CatalogFamily } from "./types";
import { CATALOG_FAMILY_LABELS } from "./types";

export const CATALOG_ENTRIES: CatalogEntry[] = [
  ...helpCatalogEntries,
  ...layoutCatalogEntries,
  ...feedbackCatalogEntries,
  ...formsCatalogEntries,
  ...dataCatalogEntries,
  ...exportCatalogEntries,
  ...sandboxCatalogEntries,
];

export function listCatalogFamilies(): CatalogFamily[] {
  const seen = new Set<CatalogFamily>();
  const order: CatalogFamily[] = [];
  for (const entry of CATALOG_ENTRIES) {
    if (!seen.has(entry.family)) {
      seen.add(entry.family);
      order.push(entry.family);
    }
  }
  return order;
}

export function filterCatalogEntries(query: string, family?: CatalogFamily | "all"): CatalogEntry[] {
  const q = query.trim().toLowerCase();
  return CATALOG_ENTRIES.filter((entry) => {
    if (family && family !== "all" && entry.family !== family) return false;
    if (!q) return true;
    const haystack = [entry.title, entry.exportName, entry.description ?? "", entry.family]
      .join(" ")
      .toLowerCase();
    return haystack.includes(q);
  });
}

export function getCatalogEntryById(id: string): CatalogEntry | undefined {
  return CATALOG_ENTRIES.find((entry) => entry.id === id);
}

export { CATALOG_FAMILY_LABELS };
