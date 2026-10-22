import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { useConversationQueue } from "./conversationQueue";

describe("useConversationQueue (F03-B ephemeral queue)", () => {
  it("starts empty and admits items in FIFO order", () => {
    const { result } = renderHook(() => useConversationQueue());
    expect(result.current.items).toEqual([]);
    act(() => {
      result.current.enqueue("pergunta A");
      result.current.enqueue("pergunta B");
    });
    expect(result.current.items.map((i) => i.text)).toEqual([
      "pergunta A",
      "pergunta B",
    ]);
  });

  it("freezes text and exposes local non-authoritative ids", () => {
    const { result } = renderHook(() => useConversationQueue());
    let first!: ReturnType<typeof result.current.enqueue>;
    act(() => {
      first = result.current.enqueue("texto congelado");
    });
    expect(first.id).toMatch(/^local-queue-/);
    expect(first.text).toBe("texto congelado");
    expect(first.createdAt).toBeGreaterThan(0);
  });

  it("takeNext consumes atomically — the same item is never handed out twice", () => {
    const { result } = renderHook(() => useConversationQueue());
    act(() => {
      result.current.enqueue("A");
      result.current.enqueue("B");
    });
    let first: ReturnType<typeof result.current.takeNext> = null;
    let second: ReturnType<typeof result.current.takeNext> = null;
    act(() => {
      // Synchronous double-take simulates a replayed dispatch effect.
      first = result.current.takeNext();
      second = result.current.takeNext();
    });
    expect(first?.text).toBe("A");
    expect(second?.text).toBe("B");
    expect(result.current.items).toEqual([]);
    act(() => {
      expect(result.current.takeNext()).toBeNull();
    });
  });

  it("moves pending items up/down within bounds", () => {
    const { result } = renderHook(() => useConversationQueue());
    act(() => {
      result.current.enqueue("A");
      result.current.enqueue("B");
      result.current.enqueue("C");
    });
    const c = result.current.items[2];
    act(() => {
      result.current.moveItem(c.id, "up");
    });
    expect(result.current.items.map((i) => i.text)).toEqual([
      "A",
      "C",
      "B",
    ]);
    // Out-of-range and unknown ids are no-ops.
    act(() => {
      result.current.moveItem(c.id, "up");
      result.current.moveItem(c.id, "up"); // already head
      result.current.moveItem("missing", "down");
    });
    expect(result.current.items.map((i) => i.text)).toEqual([
      "C",
      "A",
      "B",
    ]);
  });

  it("removes a pending item; unknown ids are no-ops", () => {
    const { result } = renderHook(() => useConversationQueue());
    act(() => {
      result.current.enqueue("A");
      result.current.enqueue("B");
    });
    const a = result.current.items[0];
    act(() => {
      result.current.removeItem(a.id);
      result.current.removeItem("missing");
    });
    expect(result.current.items.map((i) => i.text)).toEqual(["B"]);
  });

  it("clear discards all pendings (conversation invalidation)", () => {
    const { result } = renderHook(() => useConversationQueue());
    act(() => {
      result.current.enqueue("A");
      result.current.enqueue("B");
    });
    act(() => {
      result.current.clear();
    });
    expect(result.current.items).toEqual([]);
    act(() => {
      expect(result.current.takeNext()).toBeNull();
    });
  });
});
