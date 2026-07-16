import { describe, expect, it, vi } from "vitest";

import {
  buildPublicPresentationWsUrl,
  parsePresentationRealtimeEvent,
} from "./usePresentationRealtime";

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

describe("parsePresentationRealtimeEvent", () => {
  it("normaliza atualização de presença", () => {
    expect(
      parsePresentationRealtimeEvent({
        type: "presence_update",
        playlistId: "playlist-1",
        peers: [
          { clientId: "1", displayName: "Ana", role: "editor" },
          { clientId: "2", displayName: "TV", role: "viewer" },
          { clientId: "inválido", displayName: "X", role: "admin" },
        ],
      }),
    ).toEqual({
      type: "presence_update",
      playlistId: "playlist-1",
      peers: [
        { clientId: "1", displayName: "Ana", role: "editor" },
        { clientId: "2", displayName: "TV", role: "viewer" },
      ],
    });
  });

  it("rejeita frame sem tipo", () => {
    expect(parsePresentationRealtimeEvent({ peers: [] })).toBeNull();
  });

  it("aceita rascunho de slide em tempo real", () => {
    expect(
      parsePresentationRealtimeEvent({
        type: "slide_draft",
        playlistId: "playlist-1",
        slideId: "slide-a",
        clientId: "editor-1",
        nativeConfig: { title: "Olá" },
      }),
    ).toEqual({
      type: "slide_draft",
      playlistId: "playlist-1",
      slideId: "slide-a",
      clientId: "editor-1",
      nativeConfig: { title: "Olá" },
    });
  });

  it("rejeita slide_draft sem nativeConfig", () => {
    expect(
      parsePresentationRealtimeEvent({
        type: "slide_draft",
        slideId: "slide-a",
        clientId: "editor-1",
      }),
    ).toBeNull();
  });
});
