import { afterEach, describe, expect, it, vi } from "vitest";

import { CHAT_BASE_PATH } from "./chatRoutes";
import {
  navigateChatHref,
  navigateChatSurface,
  setChatNavigationHostMode,
} from "./chatNavigation";

class PopStateEventStub extends Event {
  constructor(type: string) {
    super(type);
  }
}

function installBrowserNavigationStub(initialPath = "/") {
  vi.stubGlobal("PopStateEvent", PopStateEventStub);

  let pathname = initialPath;

  const history = {
    state: null as unknown,
    replaceState(state: unknown, _title: string, url?: string | URL | null) {
      history.state = state;

      if (typeof url === "string" && url.length > 0) {
        pathname = new URL(url, "http://localhost").pathname;
      }
    },
    pushState(state: unknown, _title: string, url?: string | URL | null) {
      history.state = state;

      if (typeof url === "string" && url.length > 0) {
        pathname = new URL(url, "http://localhost").pathname;
      }
    },
  };

  const dispatchEvent = vi.fn();

  vi.stubGlobal("window", {
    history,
    dispatchEvent,
    location: {
      get pathname() {
        return pathname;
      },
      search: "",
      hash: "",
    },
  });

  return { history, dispatchEvent };
}

describe("navigateChatSurface", () => {
  afterEach(() => {
    setChatNavigationHostMode("portal");
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it("reaplica a rota quando a URL já aponta para o destino", () => {
    installBrowserNavigationStub(CHAT_BASE_PATH);

    const onApplyRoute = vi.fn();
    const pushState = vi.spyOn(window.history, "pushState");
    const dispatchEvent = vi.spyOn(window, "dispatchEvent");

    navigateChatSurface(CHAT_BASE_PATH, { onApplyRoute });

    expect(pushState).not.toHaveBeenCalled();
    expect(dispatchEvent).not.toHaveBeenCalled();
    expect(onApplyRoute).toHaveBeenCalledWith({ kind: "home" });
  });

  it("navega normalmente quando a URL muda", () => {
    installBrowserNavigationStub(`${CHAT_BASE_PATH}/conversas/session-1`);

    const onApplyRoute = vi.fn();
    const pushState = vi.spyOn(window.history, "pushState");
    const dispatchEvent = vi.spyOn(window, "dispatchEvent");

    navigateChatSurface(CHAT_BASE_PATH, { onApplyRoute });

    expect(pushState).toHaveBeenCalled();
    expect(dispatchEvent).toHaveBeenCalled();
    expect(onApplyRoute).not.toHaveBeenCalled();
  });

  it("em modo embedded aplica rota sem mutar history do host", () => {
    installBrowserNavigationStub("/apps/tv-dashboard/playlists/abc");
    setChatNavigationHostMode("embedded");

    const onApplyRoute = vi.fn();
    const pushState = vi.spyOn(window.history, "pushState");
    const replaceState = vi.spyOn(window.history, "replaceState");
    const dispatchEvent = vi.spyOn(window, "dispatchEvent");

    navigateChatSurface(`${CHAT_BASE_PATH}/conversas/session-1`, { onApplyRoute });

    expect(pushState).not.toHaveBeenCalled();
    expect(replaceState).not.toHaveBeenCalled();
    expect(dispatchEvent).not.toHaveBeenCalled();
    expect(onApplyRoute).toHaveBeenCalledWith({
      kind: "session",
      sessionId: "session-1",
    });
    expect(window.location.pathname).toBe("/apps/tv-dashboard/playlists/abc");
  });
});

describe("navigateChatHref", () => {
  afterEach(() => {
    setChatNavigationHostMode("portal");
    vi.unstubAllGlobals();
  });

  it("retorna false quando a URL não muda", () => {
    installBrowserNavigationStub(CHAT_BASE_PATH);

    expect(navigateChatHref(CHAT_BASE_PATH)).toBe(false);
  });

  it("em modo embedded nunca altera a URL do host", () => {
    installBrowserNavigationStub("/apps/tv-dashboard/playlists/abc");
    setChatNavigationHostMode("embedded");

    const pushState = vi.spyOn(window.history, "pushState");
    const dispatchEvent = vi.spyOn(window, "dispatchEvent");

    expect(navigateChatHref(`${CHAT_BASE_PATH}/conversas/session-1`)).toBe(false);
    expect(pushState).not.toHaveBeenCalled();
    expect(dispatchEvent).not.toHaveBeenCalled();
    expect(window.location.pathname).toBe("/apps/tv-dashboard/playlists/abc");
  });
});
