/** Accept Brazilian currency typing and pasted values; reject ambiguous inputs. */
export function parseBrlInput(input: string): number | null {
  let raw = input.trim().replace(/\s/g, "").replace(/^R\$/i, "");
  if (/^\d{1,3}(\.\d{3})+(,\d{1,2})?$/.test(raw)) {
    raw = raw.replace(/\./g, "").replace(",", ".");
  } else if (/^\d+(,\d{1,2})?$/.test(raw)) {
    raw = raw.replace(",", ".");
  } else if (!/^\d+(\.\d{1,2})?$/.test(raw)) {
    return null;
  }
  const value = Number(raw);
  return Number.isFinite(value) && value >= 0 ? value : null;
}
