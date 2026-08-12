import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import {
  TRANSFORMOMETRO_WORKSPACE_TREE_REFRESH_EVENT,
  requestWorkspaceTreeRefresh,
  subscribeWorkspaceTreeRefresh,
} from "../../utils/navigation";

describe("requestWorkspaceTreeRefresh", () => {
  const postMessage = vi.fn();
  const close = vi.fn();

  beforeEach(() => {
    postMessage.mockClear();
    close.mockClear();
    vi.stubGlobal("window", {
      dispatchEvent: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    });
    vi.stubGlobal(
      "BroadcastChannel",
      class {
        postMessage = postMessage;
        close = close;
        onmessage: ((event: MessageEvent) => void) | null = null;
      }
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("dispara evento para recarregar a árvore do workspace", () => {
    requestWorkspaceTreeRefresh();
    expect(window.dispatchEvent).toHaveBeenCalledWith(
      expect.objectContaining({ type: TRANSFORMOMETRO_WORKSPACE_TREE_REFRESH_EVENT })
    );
  });

  it("publica no BroadcastChannel para outras abas", () => {
    requestWorkspaceTreeRefresh();
    expect(postMessage).toHaveBeenCalledWith({
      type: TRANSFORMOMETRO_WORKSPACE_TREE_REFRESH_EVENT,
    });
    expect(close).toHaveBeenCalled();
  });

  it("subscribeWorkspaceTreeRefresh escuta evento da janela", () => {
    const handler = vi.fn();
    const listeners = new Map<string, EventListener>();
    (window.addEventListener as ReturnType<typeof vi.fn>).mockImplementation(
      (type: string, fn: EventListener) => {
        listeners.set(type, fn);
      }
    );
    const cleanup = subscribeWorkspaceTreeRefresh(handler);
    listeners.get(TRANSFORMOMETRO_WORKSPACE_TREE_REFRESH_EVENT)?.(new Event("x"));
    expect(handler).toHaveBeenCalledTimes(1);
    cleanup();
  });
});
