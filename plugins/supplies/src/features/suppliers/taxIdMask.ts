/**
 * Máscaras de documento fiscal (X4.UX-R1.S9 — UX polish).
 *
 * O draft e o payload continuam canônicos (somente dígitos); estas funções
 * afetam apenas a camada de apresentação/edição.
 */

/** Mantém só dígitos e limita ao tamanho declarado. */
export function digitsOnly(value: string, max = 14): string {
  return (value ?? "").replace(/\D/g, "").slice(0, max);
}

/** CNPJ progressivo: `23.622.391/0001-81`. */
export function formatCnpjDigits(value: string): string {
  const d = digitsOnly(value, 14);
  let out = d.slice(0, 2);
  if (d.length > 2) out += "." + d.slice(2, 5);
  if (d.length > 5) out += "." + d.slice(5, 8);
  if (d.length > 8) out += "/" + d.slice(8, 12);
  if (d.length > 12) out += "-" + d.slice(12, 14);
  return out;
}

/** CPF progressivo: `123.456.789-01`. */
export function formatCpfDigits(value: string): string {
  const d = digitsOnly(value, 11);
  let out = d.slice(0, 3);
  if (d.length > 3) out += "." + d.slice(3, 6);
  if (d.length > 6) out += "." + d.slice(6, 9);
  if (d.length > 9) out += "-" + d.slice(9, 11);
  return out;
}

/**
 * Máscara de exibição do documento conforme o tipo de pessoa.
 * Tipo indefinido/Outros → dígitos puros (não inventamos máscara ambígua).
 * Se o documento excede o tamanho do tipo, exibe dígitos puros para não
 * esconder conteúdo que seguiria no payload.
 */
export function formatTaxIdForPerson(
  value: string,
  personType: string | null | undefined,
): string {
  const d = digitsOnly(value);
  if (personType === "J") return formatCnpjDigits(d);
  if (personType === "F") {
    return d.length <= 11 ? formatCpfDigits(d) : d;
  }
  return d;
}

/** Quantidade de dígitos antes de `pos` numa string crua. */
export function digitsBeforePos(raw: string, pos: number): number {
  return raw.slice(0, Math.max(0, pos)).replace(/\D/g, "").length;
}

/**
 * Posição do caret na string formatada depois de `count` dígitos —
 * inclui os separadores que a máscara já renderizou logo após o dígito.
 */
export function caretPosAfterDigits(
  formatted: string,
  count: number,
): number {
  if (count <= 0) return 0;
  let seen = 0;
  for (let i = 0; i < formatted.length; i += 1) {
    if (/\d/.test(formatted[i])) {
      seen += 1;
      if (seen === count) {
        let j = i + 1;
        while (j < formatted.length && /\D/.test(formatted[j])) j += 1;
        return j;
      }
    }
  }
  return formatted.length;
}
