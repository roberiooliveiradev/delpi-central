/**
 * Write head compartilhado entre contextos JS da mesma origem (abas/janelas).
 *
 * A write lane serializa escritas *dentro* de um contexto; entre contextos,
 * cada um mantém seu próprio revision tracker e só aprende a revisão pelos
 * próprios acks — um segundo contexto fica permanentemente um commit atrás
 * e emite 409 determinístico (tempestade de self-409 observada em produção).
 *
 * Publicar o head dos *próprios commits* em localStorage (same-origin) permite
 * que o thunk `expectedRevision` de outro contexto resolva a revisão fresca
 * dentro da seção coordenada pelo Web Lock, e que `ifFresh` detecte escrita
 * de contexto irmão no mesmo slide antes de enviar um snapshot autoral velho.
 *
 * Somente commits do próprio origin são publicados — revisões aprendidas de
 * writers externos (outro browser, MCP/GPT) NÃO entram aqui: para essas, o
 * CAS do backend segue sendo a autoridade e produz 409 real → server-wins.
 * Isto é correlação de escrita, nunca autorização nem fonte de verdade.
 */

const GLOBAL_KEY_PREFIX = "tv-dashboard:playlist-write-head:";
const SLIDE_KEY_PREFIX = "tv-dashboard:playlist-slide-write-head:";

export type PlaylistWriteHeadEntry = {
  revision: number;
  clientId: string | null;
  at: number;
};

function storage(): Storage | null {
  try {
    if (typeof window === "undefined" || !window.localStorage) return null;
    return window.localStorage;
  } catch {
    // modo privado / storage desabilitado — head compartilhado é best-effort.
    return null;
  }
}

function readEntry(key: string): PlaylistWriteHeadEntry | null {
  const store = storage();
  if (!store) return null;
  try {
    const raw = store.getItem(key);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<PlaylistWriteHeadEntry> | null;
    if (!parsed || typeof parsed.revision !== "number") return null;
    return {
      revision: Math.trunc(parsed.revision),
      clientId: typeof parsed.clientId === "string" ? parsed.clientId : null,
      at: typeof parsed.at === "number" ? parsed.at : 0,
    };
  } catch {
    return null;
  }
}

function writeEntry(key: string, entry: PlaylistWriteHeadEntry): void {
  const store = storage();
  if (!store) return;
  try {
    store.setItem(key, JSON.stringify(entry));
  } catch {
    // quota/denied — coordenação é complementar, falha não deve quebrar escrita.
  }
}

/** Maior revisão comitada por este origin nesta playlist (0 se desconhecida). */
export function readSharedPlaylistRevision(playlistId: string): number {
  if (!playlistId) return 0;
  return readEntry(`${GLOBAL_KEY_PREFIX}${playlistId}`)?.revision ?? 0;
}

/** Head de escrita por slide — atribuição para o freshness gate por slide. */
export function readSharedSlideWriteHead(
  playlistId: string,
  slideId: string,
): PlaylistWriteHeadEntry | null {
  if (!playlistId || !slideId) return null;
  return readEntry(`${SLIDE_KEY_PREFIX}${playlistId}:${slideId}`);
}

/**
 * Detecta commit de contexto irmão no slide após a captura do gesto.
 * Retorna o head agressor ou null — usado pelo freshness gate: obter o
 * Web Lock não torna snapshot autoral velho seguro; escrita stale no mesmo
 * slide deve virar server-wins em vez de ir ao CAS com revisão atualizada.
 */
export function detectSharedSlideWrite(
  playlistId: string,
  slideId: string,
  capturedBase: number,
  ownClientId: string | null | undefined,
): PlaylistWriteHeadEntry | null {
  const head = readSharedSlideWriteHead(playlistId, slideId);
  if (!head) return null;
  if (head.revision <= capturedBase) return null;
  if (ownClientId && head.clientId === ownClientId) return null;
  return head;
}

/**
 * Registra commit próprio. Global guarda o maior revisão conhecido; a entrada
 * por slide registra quem escreveu o quê para o freshness gate cross-context.
 */
export function publishPlaylistWriteHead(
  playlistId: string,
  opts: { revision: number; slideId?: string | null; clientId?: string | null },
): void {
  if (!playlistId) return;
  const revision = Math.trunc(opts.revision);
  if (!Number.isFinite(revision) || revision <= 0) return;
  const clientId = opts.clientId ?? null;
  const now = Date.now();

  const globalKey = `${GLOBAL_KEY_PREFIX}${playlistId}`;
  const currentGlobal = readEntry(globalKey);
  if (!currentGlobal || revision >= currentGlobal.revision) {
    writeEntry(globalKey, { revision, clientId, at: now });
  }

  if (opts.slideId) {
    const slideKey = `${SLIDE_KEY_PREFIX}${playlistId}:${opts.slideId}`;
    const currentSlide = readEntry(slideKey);
    if (!currentSlide || revision >= currentSlide.revision) {
      writeEntry(slideKey, { revision, clientId, at: now });
    }
  }
}
