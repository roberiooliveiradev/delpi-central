import { describe, expect, it, vi } from "vitest";

import {
  createChatStreamSessionRegistry,
} from "./chatStreamSessionRegistry";

describe("createChatStreamSessionRegistry", () => {
  it("aborta stream anterior ao iniciar outro na mesma sessão", async () => {
    const registry = createChatStreamSessionRegistry();
    const firstAbort = vi.fn();
    const secondAbort = vi.fn();

    const firstController = new AbortController();
    const secondController = new AbortController();

    firstController.signal.addEventListener("abort", firstAbort);
    secondController.signal.addEventListener("abort", secondAbort);

    registry.register("sess-1", firstController);

    expect(registry.isStreaming("sess-1")).toBe(true);

    registry.register("sess-1", secondController);

    expect(firstAbort).toHaveBeenCalledTimes(1);
    expect(secondAbort).not.toHaveBeenCalled();
    expect(registry.isStreaming("sess-1")).toBe(true);
  });

  it("só remove o controller ativo no unregister", () => {
    const registry = createChatStreamSessionRegistry();
    const first = new AbortController();
    const second = new AbortController();

    registry.register("sess-1", first);
    registry.register("sess-1", second);

    registry.unregister("sess-1", first);

    expect(registry.isStreaming("sess-1")).toBe(true);

    registry.unregister("sess-1", second);

    expect(registry.isStreaming("sess-1")).toBe(false);
  });
});
