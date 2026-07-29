import { KAIZEN_CATEGORIES } from "../constants/kaizen";

const STORAGE_KEY = "delpi-kaizen-custom-categories";

export type CategoryOption = { value: string; label: string };

function normalizeLabel(value: string): string {
  return value.trim();
}

function dedupeLabels(values: string[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const raw of values) {
    const label = normalizeLabel(raw);
    if (!label) continue;
    const key = label.toLocaleLowerCase("pt-BR");
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(label);
  }
  return out;
}

export function categoriesFromRecord(input: {
  categories?: string[] | null;
  category?: string | null;
}): string[] {
  if (input.categories?.length) {
    return dedupeLabels(input.categories);
  }
  if (input.category?.trim()) {
    return [normalizeLabel(input.category)];
  }
  return [];
}

export function loadStoredCustomCategories(): string[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return dedupeLabels(parsed.filter((item): item is string => typeof item === "string"));
  } catch {
    return [];
  }
}

export function rememberCustomCategories(values: string[]): void {
  const defaults = new Set(KAIZEN_CATEGORIES.map((item) => item.toLocaleLowerCase("pt-BR")));
  const custom = dedupeLabels(values).filter(
    (item) => !defaults.has(item.toLocaleLowerCase("pt-BR")),
  );
  if (custom.length === 0) {
    localStorage.removeItem(STORAGE_KEY);
    return;
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(custom));
}

export function buildCategoryOptions(
  selectedValues: string[],
  storedCustom: string[] = loadStoredCustomCategories(),
): CategoryOption[] {
  const merged = dedupeLabels([...KAIZEN_CATEGORIES, ...storedCustom, ...selectedValues]);
  return merged
    .sort((left, right) => left.localeCompare(right, "pt-BR"))
    .map((label) => ({ value: label, label }));
}

export function formatCategoriesDisplay(values: string[]): string {
  if (values.length === 0) return "—";
  return values.join(", ");
}
