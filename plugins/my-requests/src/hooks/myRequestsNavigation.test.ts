import { afterEach, describe, expect, it, vi } from "vitest";

import {
  myRequestsPath,
  navigateMyRequestsPath,
} from "./myRequestsNavigation";

describe("navigateMyRequestsPath", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("usa pushState e dispara popstate sem location.assign", () => {
    const pushState = vi.fn();
    const assign = vi.fn();
    const dispatchEvent = vi.fn();
    vi.stubGlobal("window", {
      location: { pathname: "/apps/my-requests/mine", search: "" },
      history: { pushState, replaceState: vi.fn() },
      dispatchEvent,
    });

    navigateMyRequestsPath(myRequestsPath("work-queue"));

    expect(pushState).toHaveBeenCalledWith(
      null,
      "",
      "/apps/my-requests/work-queue",
    );
    expect(dispatchEvent).toHaveBeenCalled();
    expect(assign).not.toHaveBeenCalled();
  });

  it("não navega quando o path já é o atual", () => {
    const pushState = vi.fn();
    vi.stubGlobal("window", {
      location: { pathname: "/apps/my-requests/new", search: "" },
      history: { pushState, replaceState: vi.fn() },
      dispatchEvent: vi.fn(),
    });

    navigateMyRequestsPath(myRequestsPath("new"));
    expect(pushState).not.toHaveBeenCalled();
  });

  it("monta path de detalhe", () => {
    expect(myRequestsPath({ requestId: "abc" })).toBe(
      "/apps/my-requests/requests/abc",
    );
  });
});
