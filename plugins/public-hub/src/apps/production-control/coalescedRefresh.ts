/**
 * Single-flight + coalesce com Promise que só resolve após o ciclo completo.
 *
 * Evita o anti-padrão `if (inFlight) { pending=true; return; }` — callers
 * que `await refresh()` após classificar motivo recebiam resolução precoce
 * com snapshot antigo.
 */
export function createCoalescedRefresh(
  runOnce: () => Promise<void>,
): () => Promise<void> {
  let inFlight = false;
  let pending = false;
  const waiters: Array<() => void> = [];

  const flushWaiters = (batch: Array<() => void>) => {
    for (const resolve of batch) resolve();
  };

  const loop = async (): Promise<void> => {
    inFlight = true;
    try {
      do {
        pending = false;
        await runOnce();
      } while (pending);
    } finally {
      inFlight = false;
      const batch = waiters.splice(0);
      if (pending) {
        void loop().then(() => flushWaiters(batch));
      } else {
        flushWaiters(batch);
      }
    }
  };

  return async () => {
    pending = true;
    if (inFlight) {
      await new Promise<void>((resolve) => {
        waiters.push(resolve);
      });
      return;
    }
    await loop();
  };
}
