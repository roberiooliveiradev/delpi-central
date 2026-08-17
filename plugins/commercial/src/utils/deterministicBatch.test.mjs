#!/usr/bin/env node
import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { runDeterministicBatches, splitDeterministicBatches } from "./deterministicBatch.ts";

describe("deterministicBatch", () => {
  it("limita lotes a 200 e preserva a ordem com concorrencia limitada", async () => {
    const items = Array.from({ length: 451 }, (_, index) => index);
    assert.deepEqual(splitDeterministicBatches(items, 200).map((batch) => batch.length), [200, 200, 51]);
    let active = 0;
    let peak = 0;
    const execution = await runDeterministicBatches(items, {
      chunkSize: 200,
      concurrency: 2,
      execute: async (batch, batchIndex) => {
        active += 1;
        peak = Math.max(peak, active);
        await new Promise((resolve) => setTimeout(resolve, batchIndex === 0 ? 8 : 1));
        active -= 1;
        return batch[0];
      },
    });
    assert.equal(peak, 2);
    assert.deepEqual(execution.batches.map((batch) => batch.value), [0, 200, 400]);
  });
  it("registra falha parcial sem perder os demais lotes", async () => {
    const execution = await runDeterministicBatches([1, 2, 3, 4, 5], {
      chunkSize: 2,
      concurrency: 2,
      execute: async (_batch, batchIndex) => {
        if (batchIndex === 1) throw new Error("falha");
        return batchIndex;
      },
    });
    assert.equal(execution.failedBatches, 1);
    assert.deepEqual(execution.batches.map((batch) => batch.value), [0, null, 2]);
  });
  it("interrompe o processamento quando abortado", async () => {
    const controller = new AbortController();
    await assert.rejects(runDeterministicBatches([1, 2, 3], {
      chunkSize: 1,
      concurrency: 1,
      signal: controller.signal,
      execute: async () => {
        controller.abort();
        return 1;
      },
    }), (error) => error instanceof Error && error.name === "AbortError");
  });
});
