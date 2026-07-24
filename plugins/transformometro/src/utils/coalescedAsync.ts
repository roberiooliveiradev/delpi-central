/**
 * Dispara no máximo um `run` por vez; chamadas durante o voo enfileiram
 * um único replay ao terminar (evita rajada HTTP 429 no gateway).
 */
export function createCoalescedAsyncRunner() {
  let inFlight: Promise<void> | null = null;
  let pending = false;

  return function schedule(run: () => Promise<void>): Promise<void> {
    if (inFlight) {
      pending = true;
      return inFlight;
    }

    const loop = async () => {
      try {
        do {
          pending = false;
          await run();
        } while (pending);
      } finally {
        inFlight = null;
      }
    };

    inFlight = loop();
    return inFlight;
  };
}
