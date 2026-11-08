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

/**
 * Apresentação com exatamente `fractionDigits` casas decimais (pt-BR).
 * Arredonda apenas na UI a partir da string canônica (`.` decimal); sem float.
 */
export function formatDecimalStringFixed(
  value: string | null | undefined,
  fractionDigits: number,
  empty = "—",
): string {
  const text = (value ?? "").trim();
  if (!text) return empty;
  if (!Number.isInteger(fractionDigits) || fractionDigits < 0) {
    return formatDecimalString(value, empty);
  }

  const negative = text.startsWith("-");
  const raw = negative ? text.slice(1) : text;
  if (!/^\d+(\.\d+)?$/.test(raw)) return empty;

  const [intRaw, fracRaw = ""] = raw.split(".");
  const intDigits = (intRaw || "0").replace(/^0+(?=\d)/, "") || "0";
  const frac = fracRaw.replace(/\D/g, "");
  const sign = negative ? "-" : "";

  if (fractionDigits === 0) {
    const nextDigit = frac[0] ?? "0";
    let rounded = intDigits;
    if (nextDigit >= "5") rounded = addOneToDigitString(rounded);
    return `${sign}${rounded.replace(/\B(?=(\d{3})+(?!\d))/g, ".")}`;
  }

  const head = `${intDigits}${frac.padEnd(fractionDigits, "0").slice(0, fractionDigits)}`;
  const nextDigit = frac.length > fractionDigits ? frac[fractionDigits] : "0";
  let scaled = head.replace(/^0+(?=\d)/, "") || "0";
  if (nextDigit >= "5") scaled = addOneToDigitString(scaled);

  const padded = scaled.padStart(fractionDigits + 1, "0");
  const intOut = padded.slice(0, -fractionDigits).replace(/^0+(?=\d)/, "") || "0";
  const fracOut = padded.slice(-fractionDigits);
  return `${sign}${intOut.replace(/\B(?=(\d{3})+(?!\d))/g, ".")},${fracOut}`;
}

function addOneToDigitString(digits: string): string {
  const chars = digits.split("");
  let carry = 1;
  for (let i = chars.length - 1; i >= 0 && carry; i -= 1) {
    const next = Number(chars[i]) + carry;
    if (next >= 10) {
      chars[i] = "0";
      carry = 1;
    } else {
      chars[i] = String(next);
      carry = 0;
    }
  }
  return carry ? `1${chars.join("")}` : chars.join("");
}
