/** Separador interno da chave de cliente — não ocorre em códigos Protheus trimados. */
export const CUSTOMER_KEY_SEPARATOR = "|";

/**
 * Normaliza parte cadastral (código ou loja).
 * Trim lateral apenas — preserva zeros à esquerda; nunca converte para número.
 */
export function normalizeCadastroPart(value: string | null | undefined): string {
  if (value === null || value === undefined) return "";
  return String(value).trim();
}

/**
 * Chave estável `codigo|loja`. Retorna `null` se código ou loja estiver vazia após trim.
 * Não usa nome.
 */
export function buildCustomerKey(
  codigoCadastro: string | null | undefined,
  lojaCadastro: string | null | undefined,
): string | null {
  const codigo = normalizeCadastroPart(codigoCadastro);
  const loja = normalizeCadastroPart(lojaCadastro);
  if (!codigo || !loja) return null;
  return `${codigo}${CUSTOMER_KEY_SEPARATOR}${loja}`;
}

export function parseCustomerKey(
  key: string,
): { codigo: string; loja: string } | null {
  const sep = key.indexOf(CUSTOMER_KEY_SEPARATOR);
  if (sep <= 0 || sep === key.length - 1) return null;
  const codigo = key.slice(0, sep);
  const loja = key.slice(sep + 1);
  if (!codigo || !loja || loja.includes(CUSTOMER_KEY_SEPARATOR)) return null;
  return { codigo, loja };
}

export function isValidCustomerIdentity(
  codigoCadastro: string | null | undefined,
  lojaCadastro: string | null | undefined,
): boolean {
  return buildCustomerKey(codigoCadastro, lojaCadastro) !== null;
}

/** Chave de pedido distinto: `filial|pedido`. */
export function buildOrderKey(
  filial: string | null | undefined,
  pedido: string | null | undefined,
): string {
  return `${normalizeCadastroPart(filial)}${CUSTOMER_KEY_SEPARATOR}${normalizeCadastroPart(pedido)}`;
}
