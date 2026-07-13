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
import {
  formatCatalogDatePtBr,
  resolveEffectiveUpdatedAt,
  resolveLifecycle,
  todayIsoUtc,
} from "./catalogLifecycle";
import type {
  CatalogEntry,
  CatalogEntryDraft,
  CatalogFamily,
  CatalogLifecycleFilter,
} from "./types";
import { CATALOG_FAMILY_LABELS, CATALOG_LIFECYCLE_LABELS } from "./types";
import { PACKAGE_INITIAL_DATE, VISUAL_COMPONENTS, type VisualComponentSpec } from "./visualComponents";

const metaByExport = new Map(
  VISUAL_COMPONENTS.map((spec) => [spec.exportName, spec] as const),
);

function enrichEntry(entry: CatalogEntryDraft, today: string): CatalogEntry {
  const spec = metaByExport.get(entry.exportName);
  const addedAt = spec?.addedAt ?? PACKAGE_INITIAL_DATE;
  const updatedAt = resolveEffectiveUpdatedAt(addedAt, spec?.updatedAt);
  const changeNote = spec?.changeNote;
  return {
    ...entry,
    addedAt,
    updatedAt,
    changeNote,
    lifecycle: resolveLifecycle(addedAt, spec?.updatedAt, today),
  };
}

function buildStubEntry(spec: VisualComponentSpec): CatalogEntryDraft {
  return {
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
  };
}

const EXPLICIT_ENTRIES_RAW = [
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

const coveredExports = new Set(EXPLICIT_ENTRIES_RAW.map((e) => e.exportName));

const AUTO_STUB_RAW = VISUAL_COMPONENTS.filter(
  (spec) => !coveredExports.has(spec.exportName),
).map(buildStubEntry);

/** Data de referência do build (UTC). Testes podem reconstruir via `buildCatalogEntries`. */
export function buildCatalogEntries(today = todayIsoUtc()): CatalogEntry[] {
  return [...EXPLICIT_ENTRIES_RAW, ...AUTO_STUB_RAW].map((entry) => enrichEntry(entry, today));
}

/** Todas as entradas do catálogo (demos explícitas + stubs automáticos). */
export const CATALOG_ENTRIES: CatalogEntry[] = buildCatalogEntries();

export function listCatalogFamilies(entries: CatalogEntry[] = CATALOG_ENTRIES): CatalogFamily[] {
  const seen = new Set<CatalogFamily>();
  const order: CatalogFamily[] = [];
  for (const entry of entries) {
    if (!seen.has(entry.family)) {
      seen.add(entry.family);
      order.push(entry.family);
    }
  }
  return order;
}

export function sortByUpdatedAtDesc(entries: CatalogEntry[]): CatalogEntry[] {
  return [...entries].sort((a, b) => {
    if (a.updatedAt === b.updatedAt) return a.exportName.localeCompare(b.exportName);
    return a.updatedAt < b.updatedAt ? 1 : -1;
  });
}

/** Entradas com lifecycle `new` ou `updated`, mais recentes primeiro. */
export function listRecentEntries(entries: CatalogEntry[] = CATALOG_ENTRIES): CatalogEntry[] {
  return sortByUpdatedAtDesc(
    entries.filter((e) => e.lifecycle === "new" || e.lifecycle === "updated"),
  );
}

export function filterCatalogEntries(
  query: string,
  family: CatalogFamily | "all" = "all",
  lifecycleFilter: CatalogLifecycleFilter = "all",
  entries: CatalogEntry[] = CATALOG_ENTRIES,
): CatalogEntry[] {
  const q = query.trim().toLowerCase();
  let filtered = entries.filter((entry) => {
    if (family !== "all" && entry.family !== family) return false;
    if (lifecycleFilter === "new" && entry.lifecycle !== "new") return false;
    if (lifecycleFilter === "updated" && entry.lifecycle !== "updated") return false;
    if (!q) return true;
    const haystack = [
      entry.title,
      entry.exportName,
      entry.description ?? "",
      entry.family,
      entry.changeNote ?? "",
    ]
      .join(" ")
      .toLowerCase();
    return haystack.includes(q);
  });

  if (lifecycleFilter === "new" || lifecycleFilter === "updated") {
    filtered = sortByUpdatedAtDesc(filtered);
  }

  return filtered;
}

export function getCatalogEntryById(
  id: string,
  entries: CatalogEntry[] = CATALOG_ENTRIES,
): CatalogEntry | undefined {
  return entries.find((entry) => entry.id === id);
}

export {
  CATALOG_FAMILY_LABELS,
  CATALOG_LIFECYCLE_LABELS,
  VISUAL_COMPONENTS,
  formatCatalogDatePtBr,
  resolveLifecycle,
  todayIsoUtc,
};
