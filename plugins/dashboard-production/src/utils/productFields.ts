export function readProductField(
  product: Record<string, unknown> | undefined,
  ...keys: string[]
): string {
  if (!product) return "—";

  for (const key of keys) {
    const value = product[key];
    if (value == null || value === "") continue;
    return String(value);
  }

  return "—";
}
