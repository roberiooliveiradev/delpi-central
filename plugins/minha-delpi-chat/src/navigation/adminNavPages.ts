import type { AdminSubTab } from "./adminNavigation";

export type AdminNestedPage = {
  key: string;
  label: string;
  slug: string;
};

/** Sub-abas com páginas internas (3º nível na sidebar e na URL). */
export const ADMIN_NESTED_PAGES: Partial<Record<AdminSubTab, AdminNestedPage[]>> = {
  learning: [
    { key: "candidates", label: "Candidatos", slug: "candidatos" },
    { key: "vocabulary", label: "Vocabulário", slug: "vocabulario" },
    { key: "memory", label: "Memória", slug: "memoria" },
    { key: "evaluation", label: "Regressão", slug: "regressao" },
    { key: "finetuning", label: "Ajuste fino", slug: "ajuste-fino" },
  ],
};

const SLUG_BY_SUB: Partial<Record<AdminSubTab, Record<string, string>>> = {};
const KEY_BY_SLUG: Partial<Record<AdminSubTab, Record<string, string>>> = {};

for (const [subTab, pages] of Object.entries(ADMIN_NESTED_PAGES) as Array<
  [AdminSubTab, AdminNestedPage[]]
>) {
  SLUG_BY_SUB[subTab] = Object.fromEntries(pages.map((page) => [page.key, page.slug]));
  KEY_BY_SLUG[subTab] = Object.fromEntries(pages.map((page) => [page.slug, page.key]));
}

export function getNestedPages(subTab: AdminSubTab): AdminNestedPage[] {
  return ADMIN_NESTED_PAGES[subTab] ?? [];
}

export function hasNestedPages(subTab: AdminSubTab): boolean {
  return getNestedPages(subTab).length > 0;
}

export function defaultPageForSubTab(subTab: AdminSubTab): string | undefined {
  return getNestedPages(subTab)[0]?.key;
}

export function nestedPageSlug(subTab: AdminSubTab, pageKey: string): string | undefined {
  return SLUG_BY_SUB[subTab]?.[pageKey];
}

export function nestedPageFromSlug(subTab: AdminSubTab, slug: string): string | undefined {
  return KEY_BY_SLUG[subTab]?.[slug];
}

export function getNestedPageLabel(subTab: AdminSubTab, pageKey: string): string | undefined {
  return getNestedPages(subTab).find((page) => page.key === pageKey)?.label;
}
