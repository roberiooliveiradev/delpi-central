import {
  filterAdminNavTree,
  type AdminNavTreeSection,
} from "./adminNavTree";
import {
  ADMIN_NAV_CONTENT_INDEX,
  type AdminNavContentEntry,
} from "./adminNavSearchIndex";

export type AdminNavContentHit = AdminNavContentEntry & {
  snippet: string;
};

function normalizeSearch(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/\p{M}/gu, "");
}

function buildSnippet(searchText: string, query: string, maxLen = 72): string {
  const normalizedText = normalizeSearch(searchText);
  const normalizedQuery = normalizeSearch(query);
  const index = normalizedText.indexOf(normalizedQuery);

  if (index < 0) {
    return searchText.slice(0, maxLen);
  }

  const start = Math.max(0, index - 18);
  const end = Math.min(searchText.length, index + normalizedQuery.length + 42);
  const slice = searchText.slice(start, end).trim();
  const prefix = start > 0 ? "…" : "";
  const suffix = end < searchText.length ? "…" : "";

  return `${prefix}${slice}${suffix}`;
}

export function searchAdminContentHits(
  query: string,
  limit = 12,
): AdminNavContentHit[] {
  const normalized = normalizeSearch(query);

  if (!normalized) {
    return [];
  }

  const hits: AdminNavContentHit[] = [];

  for (const entry of ADMIN_NAV_CONTENT_INDEX) {
    if (!normalizeSearch(entry.searchText).includes(normalized)) {
      continue;
    }

    hits.push({
      ...entry,
      snippet: buildSnippet(entry.searchText, query),
    });

    if (hits.length >= limit) {
      break;
    }
  }

  return hits;
}

export type AdminNavSearchResult = {
  tree: AdminNavTreeSection[];
  contentHits: AdminNavContentHit[];
  hasQuery: boolean;
};

export function searchAdminNavigation(
  tree: AdminNavTreeSection[],
  query: string,
): AdminNavSearchResult {
  const normalized = normalizeSearch(query);

  return {
    tree: filterAdminNavTree(tree, normalized),
    contentHits: searchAdminContentHits(query),
    hasQuery: Boolean(normalized),
  };
}
