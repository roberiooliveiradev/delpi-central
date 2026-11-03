import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { createCoalescedRefresh } from "./coalescedRefresh.ts";

describe("createCoalescedRefresh", () => {
  it("positive: await waits for coalesced re-run after concurrent calls", async () => {
    let runs = 0;
    let release: (() => void) | null = null;
    const refresh = createCoalescedRefresh(async () => {
      runs += 1;
      if (runs === 1) {
        await new Promise<void>((resolve) => {
          release = resolve;
        });
      }
    });

    const first = refresh();
    let secondDone = false;
    const second = refresh().then(() => {
      secondDone = true;
    });
    assert.equal(secondDone, false);
    assert.equal(runs, 1);

    release?.();
    await first;
    await second;
    assert.equal(secondDone, true);
    assert.ok(runs >= 2);
  });

  it("sibling: sequential awaits each complete a full cycle", async () => {
    let runs = 0;
    const refresh = createCoalescedRefresh(async () => {
      runs += 1;
    });
    await refresh();
    await refresh();
    assert.equal(runs, 2);
  });

  it("negative: runOnce failure still releases waiters", async () => {
    let runs = 0;
    const refresh = createCoalescedRefresh(async () => {
      runs += 1;
      if (runs === 1) throw new Error("boom");
    });
    await assert.rejects(() => refresh(), /boom/);
    // waiter coalescido também precisa destravar / permitir novo ciclo
    await refresh();
    assert.equal(runs, 2);
  });
});
