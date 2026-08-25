import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

import {
  applyPlaybackCursorToIndex,
  resolvePresentationPlaybackClientId,
} from "./playbackCursor";
import { parsePresentationRealtimeEvent } from "./usePresentationRealtime";

describe("applyPlaybackCursorToIndex", () => {
  const slides = [{ id: "a" }, { id: "b" }, { id: "c" }];

  it("resolve por slideId", () => {
    expect(applyPlaybackCursorToIndex(slides, "b", 0)).toBe(1);
  });

  it("usa fallbackIndex quando slideId sumiu", () => {
    expect(applyPlaybackCursorToIndex(slides, "gone", 2)).toBe(2);
    expect(applyPlaybackCursorToIndex(slides, "gone", 99)).toBe(2);
  });

  it("retorna null sem slides ou sem fallback útil", () => {
    expect(applyPlaybackCursorToIndex([], "a", 0)).toBeNull();
    expect(applyPlaybackCursorToIndex(slides, "gone", null)).toBeNull();
  });
});

describe("parsePresentationRealtimeEvent playback_cursor", () => {
  it("aceita cursor válido", () => {
    const event = parsePresentationRealtimeEvent({
      type: "playback_cursor",
      slideId: "slide-1",
      clientId: "tv-a",
      index: 2,
      playlistId: "pl-1",
    });
    expect(event).toMatchObject({
      type: "playback_cursor",
      slideId: "slide-1",
      clientId: "tv-a",
      index: 2,
    });
  });

  it("rejeita cursor sem slideId/clientId", () => {
    expect(
      parsePresentationRealtimeEvent({
        type: "playback_cursor",
        clientId: "tv-a",
      }),
    ).toBeNull();
  });
});

describe("resolvePresentationPlaybackClientId", () => {
  beforeEach(() => {
    sessionStorage.clear();
  });
  afterEach(() => {
    sessionStorage.clear();
  });

  it("reutiliza o mesmo id na sessão", () => {
    const a = resolvePresentationPlaybackClientId("token-1");
    const b = resolvePresentationPlaybackClientId("token-1");
    expect(a).toBe(b);
    expect(a.length).toBeGreaterThan(4);
  });
});
