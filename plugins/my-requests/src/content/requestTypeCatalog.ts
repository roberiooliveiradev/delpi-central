/**
 * Catálogo JSON de apresentação dos tipos de solicitação
 * (MY-REQUESTS-JSON-PRESENTATION-CATALOG-TRANSITION-01).
 *
 * Conteúdo estritamente visual: título, descrição e ordem dos cards.
 * NÃO concede acesso, NÃO cria tipo operacional e NÃO substitui o
 * catálogo oficial do requests-api — a disponibilidade, a permissão
 * (`canCreateRequestType`) e os formulários continuam vindos da API.
 * Uma entrada aqui sem tipo operacional correspondente nunca vira um
 * card clicável: a página só renderiza tipos retornados pela API e
 * autorizados.
 */
import catalogFile from "./requestTypeCatalog.json";

export const REQUEST_TYPE_CATALOG_VERSION = 1;

export type RequestTypePresentation = {
  code: string;
  title: string;
  description: string;
  order: number;
};

function fail(message: string): never {
  throw new Error(`requestTypeCatalog inválido: ${message}`);
}

/** Valida a estrutura do JSON — lança Error em qualquer violação. */
export function parseRequestTypeCatalog(raw: unknown): RequestTypePresentation[] {
  if (!raw || typeof raw !== "object") fail("raiz deve ser objeto");
  const file = raw as { version?: unknown; types?: unknown };
  if (file.version !== REQUEST_TYPE_CATALOG_VERSION) {
    fail(`versão incompatível: ${JSON.stringify(file.version)}`);
  }
  if (!Array.isArray(file.types)) fail("`types` deve ser um array");

  const codes = new Set<string>();
  const orders = new Set<number>();
  return (file.types as unknown[]).map((item, index) => {
    if (!item || typeof item !== "object") {
      fail(`types[${index}] deve ser objeto`);
    }
    const entry = item as Record<string, unknown>;
    const code = String(entry.code ?? "").trim();
    const title = String(entry.title ?? "").trim();
    const description = String(entry.description ?? "").trim();
    const order = Number(entry.order);
    if (!code) fail(`types[${index}].code vazio`);
    if (!title) fail(`types[${index}] ('${code}') title vazio`);
    if (!description) fail(`types[${index}] ('${code}') description vazio`);
    if (!Number.isFinite(order)) fail(`types[${index}] ('${code}') order inválida`);
    if (codes.has(code)) fail(`código duplicado: '${code}'`);
    if (orders.has(order)) fail(`ordenação ambígua: order ${order} repetida`);
    codes.add(code);
    orders.add(order);
    return { code, title, description, order };
  });
}

const CATALOG = parseRequestTypeCatalog(catalogFile);
const BY_CODE = new Map(CATALOG.map((entry) => [entry.code, entry]));

/** Apresentação JSON de um tipo pelo `code` — null quando não catalogado. */
export function getRequestTypePresentation(
  code: string | null | undefined,
): RequestTypePresentation | null {
  return BY_CODE.get((code || "").trim()) ?? null;
}

/**
 * Ordena tipos operacionais pela `order` do JSON; tipos sem entrada
 * mantêm a ordem relativa da API, após os catalogados.
 */
export function sortRequestTypesByPresentation<T extends { code: string }>(
  types: readonly T[],
): T[] {
  return types
    .map((type, index) => ({
      type,
      index,
      order: getRequestTypePresentation(type.code)?.order ?? Number.POSITIVE_INFINITY,
    }))
    .sort((a, b) => a.order - b.order || a.index - b.index)
    .map(({ type }) => type);
}

export type RequestTypeCardCopy = { title: string; description: string };

/**
 * Copy do card: JSON primeiro; API (name/description) como fallback
 * para tipo operacional ainda não catalogado.
 */
export function resolveRequestTypeCardCopy(type: {
  code: string;
  name: string;
  description?: string | null;
}): RequestTypeCardCopy {
  const entry = getRequestTypePresentation(type.code);
  return {
    title: entry?.title || type.name,
    description: entry?.description || type.description?.trim() || "",
  };
}
