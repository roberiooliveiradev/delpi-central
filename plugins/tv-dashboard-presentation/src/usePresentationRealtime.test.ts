import { describe, expect, it, vi } from "vitest";

import { buildPublicPresentationWsUrl } from "./usePresentationRealtime";

describe("usePresentationRealtime urls", () => {
  it("monta URL pública com token", () => {
    vi.stubGlobal("window", {
      location: { protocol: "https:", host: "portal.exemplo.com" },
    } as Window & typeof globalThis);
    expect(buildPublicPresentationWsUrl("abc 123")).toBe(
      "wss://portal.exemplo.com/apps/tv-dashboard-api/public/present/abc%20123/ws",
    );
    vi.unstubAllGlobals();
  });
});
