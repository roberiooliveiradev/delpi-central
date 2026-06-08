import { afterEach, describe, expect, it, vi } from "vitest";

import { CHAT_BASE_PATH } from "./chatRoutes";
import { navigateChatHref, navigateChatSurface } from "./chatNavigation";

describe("navigateChatSurface", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    window.history.replaceState(window.history.state, "", "/");
  });

  it("reaplica a rota quando a URL já aponta para o destino", () => {
    window.history.replaceState(window.history.state, "", CHAT_BASE_PATH);

    const onApplyRoute = vi.fn();
    const pushState = vi.spyOn(window.history, "pushState");
    const dispatchEvent = vi.spyOn(window, "dispatchEvent");

    navigateChatSurface(CHAT_BASE_PATH, { onApplyRoute });

    expect(pushState).not.toHaveBeenCalled();
    expect(dispatchEvent).not.toHaveBeenCalled();
    expect(onApplyRoute).toHaveBeenCalledWith({ kind: "home" });
  });

  it("navega normalmente quando a URL muda", () => {
    window.history.replaceState(
      window.history.state,
      "",
      `${CHAT_BASE_PATH}/conversas/session-1`,
    );

    const onApplyRoute = vi.fn();
    const pushState = vi.spyOn(window.history, "pushState");
    const dispatchEvent = vi.spyOn(window, "dispatchEvent");

    navigateChatSurface(CHAT_BASE_PATH, { onApplyRoute });

    expect(pushState).toHaveBeenCalled();
    expect(dispatchEvent).toHaveBeenCalled();
    expect(onApplyRoute).not.toHaveBeenCalled();
  });
});

describe("navigateChatHref", () => {
  afterEach(() => {
    window.history.replaceState(window.history.state, "", "/");
  });

  it("retorna false quando a URL não muda", () => {
    window.history.replaceState(window.history.state, "", CHAT_BASE_PATH);

    expect(navigateChatHref(CHAT_BASE_PATH)).toBe(false);
  });
});
