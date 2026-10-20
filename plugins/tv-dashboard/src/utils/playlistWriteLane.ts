/**
 * Fila FIFO por playlist para escritas OCC.
 *
 * `playlists.revision` é compartilhada por todas as mutações do agregado —
 * duas escritas do mesmo cliente emitidas em paralelo carregam o mesmo
 * `expectedRevision` e o CAS do backend rejeita a segunda (self-conflict).
 * Serializar por playlist garante que cada escrita resolva a revisão
 * esperada *depois* do ack da anterior; conflitos reais entre clientes
 * continuam rejeitados pelo servidor.
 *
 * Cross-context (abas/janelas same-origin): quando o Web Locks API está
 * disponível, cada task executa dentro de um lock nomeado por playlist.
 * Isso dá exclusão mútua entre contextos do mesmo origin — o segundo
 * contexto espera o primeiro commitar, resolve `expectedRevision` dentro
 * da seção coordenada e comita em vez de gerar 409 artificial. O lock é
 * liberado automaticamente em erro e em fechamento de aba (sem deadlock,
 * sem timers). Coordenação de browser é complementar ao CAS — nunca o
 * substitui; escritas com conteúdo obsoleto seguem rejeitadas pelas
 * freshness guards e/ou pelo backend.
 */
const lanes = new Map<string, Promise<unknown>>();

type LockManagerLike = {
  request: (
    name: string,
    callback: () => Promise<unknown>,
  ) => Promise<unknown>;
};

function getLockManager(): LockManagerLike | null {
  try {
    const locks = (
      globalThis.navigator as (Navigator & { locks?: LockManagerLike }) | undefined
    )?.locks;
    return locks && typeof locks.request === "function" ? locks : null;
  } catch {
    return null;
  }
}

function lockName(key: string): string {
  return `tv-dashboard:playlist-write:${key}`;
}

export function enqueuePlaylistWrite<T>(
  playlistId: string,
  task: () => Promise<T>,
): Promise<T> {
  const key = playlistId || "_";
  const prev = lanes.get(key) ?? Promise.resolve();
  const locks = getLockManager();
  const run = locks
    ? () => locks.request(lockName(key), task) as Promise<T>
    : task;
  // `prev.then(run, run)`: a fila continua mesmo quando a escrita anterior
  // falhou — liberação do lock é responsabilidade do browser em ambos os casos.
  const next: Promise<T> = prev.then(run, run);
  lanes.set(key, next);
  const cleanup = () => {
    if (lanes.get(key) === next) lanes.delete(key);
  };
  // .then(cleanup, cleanup): settled em ambos os casos, sem rejeição pendurada.
  void next.then(cleanup, cleanup);
  return next;
}
