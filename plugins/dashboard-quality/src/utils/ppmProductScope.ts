export type PpmProductScope = "all" | "plugs";

export const PLUGS_PRODUCT_PREFIX = "9048";

export const PPM_PRODUCT_SCOPE_OPTIONS: ReadonlyArray<{
  value: PpmProductScope;
  label: string;
}> = [
  { value: "all", label: "Todos os produtos" },
  { value: "plugs", label: "Plugues (9048*)" },
];

export function isPpmProductScope(value: string | null | undefined): value is PpmProductScope {
  return value === "all" || value === "plugs";
}

export function resolvePpmProductPrefix(scope: PpmProductScope): string | undefined {
  return scope === "plugs" ? PLUGS_PRODUCT_PREFIX : undefined;
}

export function formatPpmProductScopeLabel(scope: PpmProductScope): string {
  return (
    PPM_PRODUCT_SCOPE_OPTIONS.find((option) => option.value === scope)?.label ??
    PPM_PRODUCT_SCOPE_OPTIONS[0].label
  );
}
