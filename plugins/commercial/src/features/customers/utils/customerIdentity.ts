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
  customerCenter?: string | null,
): string | null {
  const codigo = normalizeCadastroPart(codigoCadastro);
  const loja = normalizeCadastroPart(lojaCadastro);
  if (!codigo || !loja) return null;
  const center = normalizeCadastroPart(customerCenter);
  const pair = `${codigo}${CUSTOMER_KEY_SEPARATOR}${loja}`;
  return center ? `${pair}${CUSTOMER_KEY_SEPARATOR}${center}` : pair;
}

export function parseCustomerKey(
  key: string,
): { codigo: string; loja: string; center: string } | null {
  const parts = key.split(CUSTOMER_KEY_SEPARATOR);
  if (parts.length !== 2 && parts.length !== 3) return null;
  const [codigo, loja, center = ""] = parts;
  if (!codigo || !loja) return null;
  if (parts.length === 3 && !center) return null;
  return { codigo, loja, center };
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
