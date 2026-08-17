export type DeterministicBatchResult<T> = {
  batchIndex: number;
  inputCount: number;
  value: T | null;
  error: unknown | null;
};
export type DeterministicBatchExecution<T> = {
  batches: DeterministicBatchResult<T>[];
  failedBatches: number;
};
function abortError(): Error {
  if (typeof DOMException === "function") return new DOMException("Operação cancelada.", "AbortError");
  const error = new Error("Operação cancelada.");
  error.name = "AbortError";
  return error;
}
export function splitDeterministicBatches<T>(items: readonly T[], chunkSize: number): T[][] {
  if (!Number.isInteger(chunkSize) || chunkSize < 1) {
    throw new RangeError("chunkSize deve ser um inteiro positivo.");
  }
  const chunks: T[][] = [];
  for (let index = 0; index < items.length; index += chunkSize) {
    chunks.push(items.slice(index, index + chunkSize));
  }
  return chunks;
}
export async function runDeterministicBatches<TInput, TOutput>(
  items: readonly TInput[],
  options: {
    chunkSize: number;
    concurrency: number;
    signal?: AbortSignal;
    execute: (batch: readonly TInput[], batchIndex: number) => Promise<TOutput>;
  },
): Promise<DeterministicBatchExecution<TOutput>> {
  if (!Number.isInteger(options.concurrency) || options.concurrency < 1) {
    throw new RangeError("concurrency deve ser um inteiro positivo.");
  }
  if (options.signal?.aborted) throw abortError();
  const chunks = splitDeterministicBatches(items, options.chunkSize);
  const results = new Array<DeterministicBatchResult<TOutput>>(chunks.length);
  let nextIndex = 0;
  async function worker(): Promise<void> {
    while (nextIndex < chunks.length) {
      if (options.signal?.aborted) throw abortError();
      const batchIndex = nextIndex++;
      const batch = chunks[batchIndex] ?? [];
      try {
        const value = await options.execute(batch, batchIndex);
        if (options.signal?.aborted) throw abortError();
        results[batchIndex] = { batchIndex, inputCount: batch.length, value, error: null };
      } catch (error) {
        if (options.signal?.aborted || (error instanceof Error && error.name === "AbortError")) {
          throw abortError();
        }
        results[batchIndex] = {
          batchIndex,
          inputCount: batch.length,
          value: null,
          error,
        };
      }
    }
  }
  await Promise.all(
    Array.from({ length: Math.min(options.concurrency, chunks.length) }, () => worker()),
  );
  return {
    batches: results,
    failedBatches: results.filter((result) => result.error !== null).length,
  };
}
