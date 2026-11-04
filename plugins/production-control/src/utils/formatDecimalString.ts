/** Formata string decimal canônica em pt-BR sem converter para float. */
export function formatDecimalString(value: string | null | undefined, empty = "—"): string {
  const text = (value ?? "").trim();
  if (!text) return empty;
  const negative = text.startsWith("-");
  const raw = negative ? text.slice(1) : text;
  const [intPartRaw, fracPart] = raw.split(".");
  const intDigits = (intPartRaw || "0").replace(/\D/g, "") || "0";
  const grouped = intDigits.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  const sign = negative ? "-" : "";
  if (fracPart == null || fracPart === "") return `${sign}${grouped}`;
  return `${sign}${grouped},${fracPart}`;
}
