import { describe, expect, it, vi } from "vitest";

import { createCoalescedAsyncRunner } from "./coalescedAsync";

describe("createCoalescedAsyncRunner", () => {
  it("executa uma vez e faz um replay se chamada durante o voo", async () => {
    const schedule = createCoalescedAsyncRunner();
    let runs = 0;
    let release!: () => void;
    const gate = new Promise<void>((resolve) => {
      release = resolve;
    });

    const run = vi.fn(async () => {
      runs += 1;
      if (runs === 1) await gate;
    });

    const first = schedule(run);
    const second = schedule(run);
    const third = schedule(run);

    expect(run).toHaveBeenCalledTimes(1);
    release();
    await Promise.all([first, second, third]);
    expect(runs).toBe(2);
  });
});
