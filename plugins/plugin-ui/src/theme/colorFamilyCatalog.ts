/**
 * Color Family Catalog — fonte única para famílias semânticas de paleta.
 * IDs alinhados à API (PresentationSpec.paletteFamily) e resolvidos para
 * tokens CSS `--mdc-*` (nunca hex solto no conteúdo do chat).
 */

export type ColorFamilyTheme = "light" | "dark";

export type ColorFamilyId =
  | "brand"
  | "sequential-blue"
  | "cool"
  | "warm"
  | "diverging-status"
  | "status"
  | "categorical";

export type ColorFamilyDefinition = {
  id: ColorFamilyId;
  /** Tokens CSS var() — tema claro/escuro resolve via folhas MDC do host. */
  tokens: readonly string[];
  /** IDs legados/sinônimos que normalizam para esta família canônica. */
  aliases?: readonly string[];
};

const CHART_SERIES_TOKENS = Array.from(
  { length: 10 },
  (_, index) => `var(--mdc-chart-series-${index + 1})`,
) as readonly string[];

const COLOR_FAMILIES: readonly ColorFamilyDefinition[] = [
  {
    id: "brand",
    tokens: ["var(--mdc-chart-series-1)", "var(--mdc-chart-series-10)"],
  },
  {
    id: "sequential-blue",
    tokens: ["var(--mdc-heatmap-low)", "var(--mdc-heatmap-high)"],
  },
  {
    id: "cool",
    tokens: ["var(--mdc-chart-series-7)", "var(--mdc-chart-series-2)"],
  },
  {
    id: "warm",
    tokens: ["var(--mdc-chart-series-4)", "var(--mdc-chart-series-5)"],
  },
  {
    id: "diverging-status",
    tokens: ["var(--mdc-chart-series-5)", "var(--mdc-chart-series-3)"],
  },
  {
    id: "status",
    tokens: ["var(--mdc-chart-series-5)", "var(--mdc-chart-series-3)"],
  },
  {
    id: "categorical",
    tokens: CHART_SERIES_TOKENS,
    aliases: ["categorical-deck"],
  },
] as const;

const FAMILY_BY_ID = new Map<string, ColorFamilyDefinition>(
  COLOR_FAMILIES.flatMap((family) => {
    const entries: Array<[string, ColorFamilyDefinition]> = [[family.id, family]];
    for (const alias of family.aliases ?? []) {
      entries.push([alias, family]);
    }
    return entries;
  }),
);

function normalizeColorFamilyId(id: string | undefined): string {
  return String(id || "")
    .trim()
    .toLowerCase();
}

/** Lista IDs canônicos (sem duplicar aliases). */
export function listColorFamilies(): ColorFamilyId[] {
  return COLOR_FAMILIES.map((family) => family.id);
}

/**
 * Resolve família semântica para tokens CSS.
 * `theme` reserva extensão futura; hoje os tokens são vars MDC do host.
 */
export function resolveColorFamily(
  id: string | undefined,
  _theme: ColorFamilyTheme = "light",
): string[] {
  const normalized = normalizeColorFamilyId(id);
  if (!normalized) {
    return [];
  }

  const family = FAMILY_BY_ID.get(normalized);
  if (!family) {
    return [];
  }

  return [...family.tokens];
}

export function getColorFamilyDefinition(
  id: string | undefined,
): ColorFamilyDefinition | undefined {
  const normalized = normalizeColorFamilyId(id);
  if (!normalized) {
    return undefined;
  }

  return FAMILY_BY_ID.get(normalized);
}
