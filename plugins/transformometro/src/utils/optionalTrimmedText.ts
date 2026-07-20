/** Texto livre opcional para payload de API — usar só no save, nunca no onChange. */
export function optionalTrimmedText(value: string | null | undefined): string | undefined {
  const trimmed = String(value ?? "").trim();
  return trimmed || undefined;
}
