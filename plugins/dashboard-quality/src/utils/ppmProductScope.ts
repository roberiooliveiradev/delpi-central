export type PpmProductScope = "all" | "plugs" | "components";

export const PLUGS_PRODUCT_PREFIX = "9048";
export const COMPONENTS_PRODUCT_PREFIX = "9026";

export const PPM_PRODUCT_SCOPE_OPTIONS: ReadonlyArray<{
  value: PpmProductScope;
  label: string;
}> = [
  { value: "all", label: "Todos os produtos" },
  { value: "plugs", label: "Plugues (9048*)" },
  { value: "components", label: "Componentes (9026*)" },
];

export function isPpmProductScope(value: string | null | undefined): value is PpmProductScope {
  return value === "all" || value === "plugs" || value === "components";
}

export function resolvePpmProductPrefix(scope: PpmProductScope): string | undefined {
  if (scope === "plugs") return PLUGS_PRODUCT_PREFIX;
  if (scope === "components") return COMPONENTS_PRODUCT_PREFIX;
  return undefined;
}

export function formatPpmProductScopeLabel(scope: PpmProductScope): string {
  return (
    PPM_PRODUCT_SCOPE_OPTIONS.find((option) => option.value === scope)?.label ??
    PPM_PRODUCT_SCOPE_OPTIONS[0].label
  );
}

export function formatPpmProductScopeSuffix(scope: PpmProductScope): string {
  if (scope === "plugs") return " — plugues";
  if (scope === "components") return " — componentes";
  return "";
}
