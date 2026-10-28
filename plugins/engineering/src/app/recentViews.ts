/** Últimos acessos do catálogo — persistência LOCAL escopada por
 * identidade (mesmo modelo dos favoritos). Guarda apenas metadados de
 * navegação (routeId + label do catálogo); itens cujo acesso foi
 * revogado são descartados na leitura pelo consumidor. */

const STORAGE_PREFIX = "engineering.home.recentViews.v1";
const MAX_RECENTS = 5;

export type RecentCatalogView = {
  routeId: string;
  label: string;
  at: number;
};

let identityKey = "anonymous";

function storageKey(): string {
  return `${STORAGE_PREFIX}.${identityKey}`;
}

export function setRecentsIdentity(identity: string | null): void {
  identityKey = identity?.trim() || "anonymous";
}

export function readRecentViews(
  knownRouteIds?: ReadonlySet<string>,
): RecentCatalogView[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(storageKey());
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter(
        (entry): entry is RecentCatalogView =>
          !!entry &&
          typeof (entry as RecentCatalogView).routeId === "string" &&
          typeof (entry as RecentCatalogView).label === "string" &&
          (!knownRouteIds || knownRouteIds.has(entry.routeId)),
      )
      .slice(0, MAX_RECENTS);
  } catch {
    return [];
  }
}

export function pushRecentView(
  item: Omit<RecentCatalogView, "at">,
): RecentCatalogView[] {
  const nextItem: RecentCatalogView = { ...item, at: Date.now() };
  const previous = readRecentViews().filter(
    (entry) => entry.routeId !== item.routeId,
  );
  const next = [nextItem, ...previous].slice(0, MAX_RECENTS);
  if (typeof window !== "undefined") {
    try {
      window.localStorage.setItem(storageKey(), JSON.stringify(next));
    } catch {
      /* quota/privacy */
    }
  }
  return next;
}

export function resetRecentsStore(): void {
  identityKey = "anonymous";
}
