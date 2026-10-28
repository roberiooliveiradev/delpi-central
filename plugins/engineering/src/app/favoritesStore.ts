/** Favoritos da Home — persistência LOCAL, escopada por identidade.
 *
 * Não existe API neutra de favoritos na plataforma: o mecanismo do
 * Comercial (`/me/home-favorites`) pertence à commercial-api e não é
 * um contrato compartilhado. Sem aprovação para criar tabela na
 * engineering-api, o MFE usa localStorage chaveado pelo `sub` do JWT:
 *
 *   engineering.home.favorites.v1.<sub>
 *
 * Consequências documentadas:
 * - isolado por usuário mesmo em dispositivo compartilhado;
 * - NÃO sincroniza entre dispositivos/navegadores;
 * - conteúdo = ids estáveis do catálogo — nunca dados de domínio;
 * - itens que perderam permissão ficam visíveis como indisponíveis
 *   mas não são executáveis (a autorização efetiva continua na Core).
 */

const STORAGE_PREFIX = "engineering.home.favorites.v1";
const MAX_FAVORITES = 8;

export type EngineeringFavorite = {
  routeId: string;
};

type Listener = (items: EngineeringFavorite[]) => void;

let identityKey = "anonymous";
let cache: EngineeringFavorite[] | null = null;
const listeners = new Set<Listener>();

function storageKey(): string {
  return `${STORAGE_PREFIX}.${identityKey}`;
}

function readPersisted(): EngineeringFavorite[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(storageKey());
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(
      (entry): entry is EngineeringFavorite =>
        !!entry &&
        typeof (entry as EngineeringFavorite).routeId === "string",
    );
  } catch {
    return [];
  }
}

function persist(items: EngineeringFavorite[]): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(storageKey(), JSON.stringify(items));
  } catch {
    /* quota/privacy — falha de persistência não derruba a sessão */
  }
}

function emit(): void {
  const snapshot = getFavoriteSnapshot();
  for (const listener of listeners) listener(snapshot);
}

/** Define a identidade dona do escopo (sub do JWT). Troca de usuário
 * recarrega o cache a partir da chave da nova identidade — o estado do
 * usuário anterior nunca vaza para a próxima sessão. */
export function setFavoritesIdentity(identity: string | null): void {
  const next = identity?.trim() || "anonymous";
  if (next === identityKey && cache !== null) return;
  identityKey = next;
  cache = null;
  emit();
}

export function getFavoriteSnapshot(): EngineeringFavorite[] {
  if (cache === null) cache = readPersisted();
  return cache;
}

export function getFavoriteRouteIds(): ReadonlySet<string> {
  return new Set(getFavoriteSnapshot().map((item) => item.routeId));
}

export function isFavorite(routeId: string): boolean {
  return getFavoriteRouteIds().has(routeId);
}

export function subscribeFavorites(listener: Listener): () => void {
  listeners.add(listener);
  listener(getFavoriteSnapshot());
  return () => {
    listeners.delete(listener);
  };
}

export function toggleFavorite(routeId: string): EngineeringFavorite[] {
  const current = getFavoriteSnapshot();
  const exists = current.some((item) => item.routeId === routeId);
  const next = exists
    ? current.filter((item) => item.routeId !== routeId)
    : [...current, { routeId }].slice(0, MAX_FAVORITES);
  cache = next;
  persist(next);
  emit();
  return next;
}

/** Limpeza de sessão (unmount do MFE): descarta cache e listeners para
 * que nenhum estado da sessão anterior sobreviva à remontagem. */
export function resetFavoritesStore(): void {
  cache = null;
  listeners.clear();
  identityKey = "anonymous";
}
