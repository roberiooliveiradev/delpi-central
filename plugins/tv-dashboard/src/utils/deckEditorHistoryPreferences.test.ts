import { afterEach, beforeEach, describe, expect, it } from "vitest";

import type { Playlist, Slide } from "../api/tvDashboardApi";
import { buildDeckEditorSnapshot } from "./deckEditorHistory";
import {
  clearDeckEditorHistory,
  normalizeDeckEditorHistoryStore,
  readDeckEditorHistory,
  writeDeckEditorHistory,
} from "./deckEditorHistoryPreferences";

function slide(id: string): Slide {
  return {
    id,
    playlistId: "pl-1",
    sortOrder: 0,
    slideType: "native",
    title: `Slide ${id}`,
    isActive: true,
    nativeScreenKey: "custom_message",
    nativeConfig: { blocks: [] },
  };
}

function playlist(): Playlist {
  return {
    id: "pl-1",
    publicToken: "tok",
    name: "Test",
    viewportProfile: "1080p",
    transitionStyle: "fade",
    defaultDurationSec: 30,
    globalRefreshSec: 30,
    isActive: true,
    viewCount: 0,
    slides: [slide("a")],
  };
}

describe("deckEditorHistoryPreferences", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  afterEach(() => {
    window.localStorage.clear();
  });

  it("persiste e restaura past/future", () => {
    const snap = buildDeckEditorSnapshot(playlist(), "a");
    writeDeckEditorHistory("pl-1", [snap], []);
    const stored = readDeckEditorHistory("pl-1");
    expect(stored?.past).toHaveLength(1);
    expect(stored?.future).toHaveLength(0);
    expect(stored?.past[0]?.selectedSlideId).toBe("a");
    expect(stored?.past[0]?.playlist.id).toBe("pl-1");
  });

  it("ignora JSON inválido e limpa sob demanda", () => {
    expect(normalizeDeckEditorHistoryStore({ version: 99 })).toBeNull();
    writeDeckEditorHistory("pl-1", [buildDeckEditorSnapshot(playlist(), "a")], []);
    clearDeckEditorHistory("pl-1");
    expect(readDeckEditorHistory("pl-1")).toBeNull();
  });
});
