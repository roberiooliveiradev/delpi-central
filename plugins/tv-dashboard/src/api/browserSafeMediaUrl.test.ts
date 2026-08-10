import { afterEach, describe, expect, it, vi } from "vitest";

import {
  ensureBrowserSafeMediaUrl,
  extractAdminMediaAssetId,
  isAdminProtectedMediaUrl,
  resolveBrowserDisplayMediaUrl,
  resolvePublicMediaToken,
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

  it("resolve URL pública quando há publicToken (fluxo canônico)", () => {
    configureHttpClient(() => "jwt-token");
    expect(resolveBrowserDisplayMediaUrl("p1", "a1", "tok-publico")).toBe(
      "/apps/tv-dashboard-api/public/present/tok-publico/media/a1",
    );
    // Não usa access_token quando há capability pública.
    expect(resolveBrowserDisplayMediaUrl("p1", "a1", "tok-publico")).not.toContain(
      "access_token",
    );
  });

  it("extrai token de publicUrl …/present/{token}", () => {
    expect(
      resolvePublicMediaToken("https://minhadelpi.com.br/apps/tv-dashboard/present/abc.TOK"),
    ).toBe("abc.TOK");
    expect(resolvePublicMediaToken("tok-limpo")).toBe("tok-limpo");
  });

  it("ensureBrowserSafeMediaUrl reescreve admin → pública", () => {
    expect(
      ensureBrowserSafeMediaUrl("/apps/tv-dashboard-api/playlists/p1/media/asset-9", {
        publicToken: "tok",
      }),
    ).toBe("/apps/tv-dashboard-api/public/present/tok/media/asset-9");
    expect(extractAdminMediaAssetId("/apps/tv-dashboard-api/playlists/p1/media/a%2Fb")).toBe(
      "a/b",
    );
  });

  it("fallback access_token quando não há publicToken", () => {
    configureHttpClient(() => "jwt-token");
    expect(resolveBrowserDisplayMediaUrl("p1", "a1")).toBe(
      "/apps/tv-dashboard-api/playlists/p1/media/a1?access_token=jwt-token",
    );
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

  it("reescreve payloads preferindo URL pública", () => {
    configureHttpClient(() => "tok");
    const rewritten = rewriteAdminMediaUrlsForBrowser(
      {
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
      },
      "share-tok",
    );
    expect(rewritten.slides[0].native.data.background.url).toBe(
      "/apps/tv-dashboard-api/public/present/share-tok/media/bg",
    );
    expect(rewritten.slides[0].native.data.blocks[0].url).toBe(
      "/apps/tv-dashboard-api/public/present/share-tok/media/img",
    );
  });

  it("reescreve recursivamente com access_token sem publicToken", () => {
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
