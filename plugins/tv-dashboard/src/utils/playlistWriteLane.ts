/**
 * Fila FIFO por playlist para escritas OCC.
 *
 * `playlists.revision` é compartilhada por todas as mutações do agregado —
 * duas escritas do mesmo cliente emitidas em paralelo carregam o mesmo
 * `expectedRevision` e o CAS do backend rejeita a segunda (self-conflict).
 * Serializar por playlist garante que cada escrita resolva a revisão
 * esperada *depois* do ack da anterior; conflitos reais entre clientes
 * continuam rejeitados pelo servidor.
 */
const lanes = new Map<string, Promise<unknown>>();

export function enqueuePlaylistWrite<T>(
  playlistId: string,
  task: () => Promise<T>,
): Promise<T> {
  const key = playlistId || "_";
  const prev = lanes.get(key) ?? Promise.resolve();
  const next = prev.then(task, task);
  lanes.set(key, next);
  const cleanup = () => {
    if (lanes.get(key) === next) lanes.delete(key);
  };
  // .then(cleanup, cleanup): settled em ambos os casos, sem rejeição pendurada.
  void next.then(cleanup, cleanup);
  return next;
}
