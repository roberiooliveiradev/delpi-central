import { describe, expect, it, vi } from "vitest";

import {
  buildPublicPresentationWsUrl,
  isTvDashboardPortalPath,
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

  it("aceita seleção remota validada pelo servidor", () => {
    expect(
      parsePresentationRealtimeEvent({
        type: "selection_update",
        playlistId: "playlist-1",
        slideId: "slide-a",
        clientId: "editor-1",
        displayName: "Ana Silva",
        selectedIds: ["block-1", "block-2"],
        updatedAt: 123,
      }),
    ).toEqual({
      type: "selection_update",
      playlistId: "playlist-1",
      slideId: "slide-a",
      clientId: "editor-1",
      displayName: "Ana Silva",
      selectedIds: ["block-1", "block-2"],
      updatedAt: 123,
    });
  });

  it("rejeita seleção remota com IDs inválidos", () => {
    expect(
      parsePresentationRealtimeEvent({
        type: "selection_update",
        slideId: "slide-a",
        clientId: "editor-1",
        displayName: "Ana",
        selectedIds: ["block-1", 2],
      }),
    ).toBeNull();
  });

  it("aceita meeting_laser / meeting_ink_stroke / meeting_ink_clear", () => {
    expect(
      parsePresentationRealtimeEvent({
        type: "meeting_laser",
        slideId: "s1",
        clientId: "tv-a",
        x: 0.25,
        y: 0.75,
        visible: true,
      }),
    ).toEqual({
      type: "meeting_laser",
      slideId: "s1",
      clientId: "tv-a",
      x: 0.25,
      y: 0.75,
      visible: true,
    });
    expect(
      parsePresentationRealtimeEvent({
        type: "meeting_ink_stroke",
        slideId: "s1",
        clientId: "tv-a",
        strokeId: "st-1",
        phase: "move",
        points: [{ x: 0.1, y: 0.2 }],
      }),
    ).toMatchObject({ type: "meeting_ink_stroke", strokeId: "st-1", phase: "move" });
    expect(
      parsePresentationRealtimeEvent({
        type: "meeting_ink_clear",
        slideId: "s1",
        clientId: "tv-a",
      }),
    ).toEqual({ type: "meeting_ink_clear", slideId: "s1", clientId: "tv-a" });
  });

  it("rejeita meeting_ink_stroke com phase inválida", () => {
    expect(
      parsePresentationRealtimeEvent({
        type: "meeting_ink_stroke",
        slideId: "s1",
        clientId: "tv-a",
        strokeId: "st-1",
        phase: "draw",
        points: [],
      }),
    ).toBeNull();
  });
});

describe("isTvDashboardPortalPath", () => {
  it("reconhece só rotas do plugin TV no portal", () => {
    expect(isTvDashboardPortalPath("/apps/tv-dashboard")).toBe(true);
    expect(isTvDashboardPortalPath("/apps/tv-dashboard/playlists/x")).toBe(true);
    expect(isTvDashboardPortalPath("/apps/controle-mp")).toBe(false);
    expect(isTvDashboardPortalPath("/")).toBe(false);
    // Link público da TV — fora do plugin; guarda de path não deve valer sem presence.
    expect(isTvDashboardPortalPath("/p/tv-dashboard/present/tok")).toBe(false);
  });
});
