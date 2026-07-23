import { afterEach, describe, expect, it, vi } from "vitest";

import {
  isAdminProtectedMediaUrl,
  rewriteAdminMediaUrlsForBrowser,
  withBrowserMediaAccessToken,
} from "./browserSafeMediaUrl";
import { configureHttpClient } from "./httpClient";

describe("browserSafeMediaUrl", () => {
  afterEach(() => {
    configureHttpClient(() => undefined);
  });

  it("reconhece só mídia admin protegida", () => {
    expect(
      isAdminProtectedMediaUrl("/apps/tv-dashboard-api/playlists/p1/media/a1"),
    ).toBe(true);
    expect(
      isAdminProtectedMediaUrl("/apps/tv-dashboard-api/public/present/tok/media/a1"),
    ).toBe(false);
  });

  it("anexa access_token quando há JWT", () => {
    configureHttpClient(() => "jwt-token");
    expect(withBrowserMediaAccessToken("/apps/tv-dashboard-api/playlists/p1/media/a1")).toBe(
      "/apps/tv-dashboard-api/playlists/p1/media/a1?access_token=jwt-token",
    );
  });

  it("não duplica access_token nem altera URL pública", () => {
    configureHttpClient(() => "jwt-token");
    const already =
      "/apps/tv-dashboard-api/playlists/p1/media/a1?access_token=jwt-token";
    expect(withBrowserMediaAccessToken(already)).toBe(already);
    expect(
      withBrowserMediaAccessToken("/apps/tv-dashboard-api/public/present/tok/media/a1"),
    ).toBe("/apps/tv-dashboard-api/public/present/tok/media/a1");
  });

  it("reescreve recursivamente payloads de preview", () => {
    configureHttpClient(() => "tok");
    const rewritten = rewriteAdminMediaUrlsForBrowser({
      slides: [
        {
          native: {
            data: {
              background: {
                type: "image",
                url: "/apps/tv-dashboard-api/playlists/p1/media/bg",
              },
              blocks: [
                { type: "image", url: "/apps/tv-dashboard-api/playlists/p1/media/img" },
              ],
            },
          },
        },
      ],
    });
    expect(rewritten.slides[0].native.data.background.url).toContain("access_token=tok");
    expect(rewritten.slides[0].native.data.blocks[0].url).toContain("access_token=tok");
  });
});
