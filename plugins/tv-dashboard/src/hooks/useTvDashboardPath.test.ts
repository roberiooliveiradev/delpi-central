// @vitest-environment happy-dom
import { act, renderHook } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { useTvDashboardPath } from "./useTvDashboardPath";

describe("useTvDashboardPath", () => {
  it("prioriza window.location quando host envia base path stale", () => {
    window.history.replaceState({}, "", "/apps/tv-dashboard/playlists/abc-123");

    const { result } = renderHook(({ hostPath }) => useTvDashboardPath(hostPath), {
      initialProps: { hostPath: "/apps/tv-dashboard" },
    });

    expect(result.current).toBe("/apps/tv-dashboard/playlists/abc-123");

    act(() => {
      window.history.pushState({}, "", "/apps/tv-dashboard/playlists/abc-123/preview");
      window.dispatchEvent(new PopStateEvent("popstate"));
    });

    expect(result.current).toBe("/apps/tv-dashboard/playlists/abc-123/preview");
  });

  it("mantém rota do browser quando host fica para trás após navegação interna", () => {
    window.history.replaceState({}, "", "/apps/tv-dashboard/playlists/xyz/share");

    const { result } = renderHook(({ hostPath }) => useTvDashboardPath(hostPath), {
      initialProps: { hostPath: "/apps/tv-dashboard/playlists/xyz" },
    });

    expect(result.current).toBe("/apps/tv-dashboard/playlists/xyz/share");
  });
});
