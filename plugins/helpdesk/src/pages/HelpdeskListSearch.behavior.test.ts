/**
 * HELPDESK-P0 — behavioral tests for the ticket-list search flow.
 *
 * Exercises the real debouncer + stale-response guard used by TicketListPage:
 * typing schedules a backend commit after 350 ms, rapid typing collapses into
 * one commit, clearing commits an empty term, and a delayed response from an
 * older request can never overwrite a newer one.
 */
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  SEARCH_DEBOUNCE_MS,
  createDebouncer,
  createStaleGuard,
} from "./ticketSearchFlow";

afterEach(() => {
  vi.useRealTimers();
});

describe("ticket list debounced backend search", () => {
  it("commits the term only after the debounce window", () => {
    vi.useFakeTimers();
    const commits: string[] = [];
    const debouncer = createDebouncer();
    debouncer.schedule(() => commits.push("1465"));
    vi.advanceTimersByTime(SEARCH_DEBOUNCE_MS - 10);
    expect(commits).toEqual([]);
    vi.advanceTimersByTime(10);
    expect(commits).toEqual(["1465"]);
  });

  it("collapses rapid typing into a single commit of the final term", () => {
    vi.useFakeTimers();
    const commits: string[] = [];
    const debouncer = createDebouncer();
    debouncer.schedule(() => commits.push("1"));
    vi.advanceTimersByTime(100);
    debouncer.schedule(() => commits.push("14"));
    vi.advanceTimersByTime(100);
    debouncer.schedule(() => commits.push("1465"));
    vi.advanceTimersByTime(SEARCH_DEBOUNCE_MS);
    expect(commits).toEqual(["1465"]);
  });

  it("cancel() drops a pending commit (Enter applied first)", () => {
    vi.useFakeTimers();
    const commits: string[] = [];
    const debouncer = createDebouncer();
    debouncer.schedule(() => commits.push("1465"));
    debouncer.cancel();
    expect(debouncer.pending()).toBe(false);
    vi.advanceTimersByTime(SEARCH_DEBOUNCE_MS * 2);
    expect(commits).toEqual([]);
  });

  it("an empty term is committed like any other search (clear → unfiltered reload)", () => {
    vi.useFakeTimers();
    const commits: string[] = [];
    const debouncer = createDebouncer();
    debouncer.schedule(() => commits.push(""));
    vi.advanceTimersByTime(SEARCH_DEBOUNCE_MS);
    expect(commits).toEqual([""]);
  });
});

describe("ticket list stale-response guard", () => {
  it("invalidates the older request when a newer one starts", () => {
    const guard = createStaleGuard();
    const first = guard.next();
    const second = guard.next();
    expect(guard.isCurrent(first)).toBe(false);
    expect(guard.isCurrent(second)).toBe(true);
  });

  it("a delayed HTTP response from an older query cannot overwrite newer results", async () => {
    const guard = createStaleGuard();
    const items: string[] = [];
    const apply = (seq: number, rows: string[]) => {
      if (!guard.isCurrent(seq)) return;
      items.splice(0, items.length, ...rows);
    };

    const slowRequest = (rows: string[], delayMs: number) => {
      const seq = guard.next();
      return new Promise<void>((resolve) => {
        setTimeout(() => {
          apply(seq, rows);
          resolve();
        }, delayMs);
      });
    };

    // q=1465 returns slowly; user cleared the search meanwhile.
    const stale = slowRequest(["ticket-1465"], 60);
    const fresh = slowRequest(["ticket-900", "ticket-901"], 10);
    await Promise.all([stale, fresh]);
    expect(items).toEqual(["ticket-900", "ticket-901"]);
  });

  it("aborting a page change does not resurrect its results", async () => {
    const guard = createStaleGuard();
    let applied: number[] = [];
    const seqPage2 = guard.next();
    const seqPage1 = guard.next(); // user navigated back before page-2 resolved
    applyResult(seqPage2, [21, 22]);
    applyResult(seqPage1, [1, 2]);
    function applyResult(seq: number, ids: number[]) {
      if (guard.isCurrent(seq)) applied = ids;
    }
    expect(applied).toEqual([1, 2]);
  });
});
