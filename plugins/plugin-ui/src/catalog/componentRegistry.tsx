import { dataCatalogEntries } from "./demos/data";
import { exportCatalogEntries } from "./demos/export";
import { feedbackCatalogEntries } from "./demos/feedback";
import { formsCatalogEntries } from "./demos/forms";
import { helpCatalogEntries } from "./demos/help";
import { layoutCatalogEntries } from "./demos/layout";
import { chartsCatalogEntries } from "./demos/charts";
import { previewCatalogEntries } from "./demos/preview";
import { diagramCatalogEntries } from "./demos/diagram";
import { shapeCatalogEntries } from "./demos/shape";
import { menuCatalogEntries } from "./demos/menu";
import { CatalogStub } from "./CatalogStub";
import type { CatalogEntry, CatalogFamily } from "./types";
import { CATALOG_FAMILY_LABELS } from "./types";
import { VISUAL_COMPONENTS } from "./visualComponents";

const EXPLICIT_ENTRIES: CatalogEntry[] = [
  ...helpCatalogEntries,
  ...layoutCatalogEntries,
  ...feedbackCatalogEntries,
  ...formsCatalogEntries,
  ...dataCatalogEntries,
  ...exportCatalogEntries,
  ...chartsCatalogEntries,
  ...previewCatalogEntries,
  ...diagramCatalogEntries,
  ...shapeCatalogEntries,
  ...menuCatalogEntries,
];

const coveredExports = new Set(EXPLICIT_ENTRIES.map((e) => e.exportName));

const AUTO_STUB_ENTRIES: CatalogEntry[] = VISUAL_COMPONENTS.filter(
  (spec) => !coveredExports.has(spec.exportName),
).map((spec) => ({
  id: `${spec.family}.${spec.exportName}`,
  family: spec.family,
  exportName: spec.exportName,
  title: spec.exportName,
  description:
    spec.description ??
    "Export público — prévia stub. Preferir demo interativa em src/catalog/demos/.",
  demos: [
    {
      id: "stub",
      label: "Stub",
      render: () => <CatalogStub name={spec.exportName} />,
    },
  ],
}));

/** Todas as entradas do catálogo (demos explícitas + stubs automáticos). */
export const CATALOG_ENTRIES: CatalogEntry[] = [...EXPLICIT_ENTRIES, ...AUTO_STUB_ENTRIES];

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

export { CATALOG_FAMILY_LABELS, VISUAL_COMPONENTS };
