import { describe, expect, it } from "vitest";

import type { Playlist, Slide } from "../api/tvDashboardApi";
import { buildDeckEditorSnapshot, cloneDeckEditorSnapshot, pushDeckHistory } from "./deckEditorHistory";

function slide(id: string, sortOrder: number): Slide {
  return {
    id,
    playlistId: "pl-1",
    sortOrder,
    slideType: "native",
    title: `Slide ${id}`,
    isActive: true,
    nativeScreenKey: "custom_message",
    nativeConfig: { blocks: [] },
  };
}

function playlist(slides: Slide[]): Playlist {
  return {
    id: "pl-1",
    publicToken: "tok",
    name: "Test",
    viewportProfile: "16:9",
    transitionStyle: "fade",
    defaultDurationSec: 30,
    globalRefreshSec: 30,
    isActive: true,
    viewCount: 0,
    slides,
  };
}

describe("deckEditorHistory", () => {
  it("captura config ao vivo do slide personalizado", () => {
    const pl = playlist([slide("a", 0)]);
    const snap = buildDeckEditorSnapshot(pl, "a", { blocks: [{ id: "1" }] }, "a");
    expect(snap.playlist.slides?.[0]?.nativeConfig).toEqual({ blocks: [{ id: "1" }] });
  });

  it("empilha snapshots com limite", () => {
    const base = buildDeckEditorSnapshot(playlist([slide("a", 0)]), "a");
    const past = pushDeckHistory([], base);
    expect(past).toHaveLength(1);
    expect(cloneDeckEditorSnapshot(past[0]!).playlist.slides).toHaveLength(1);
  });

  it("isola nativeConfig aninhado entre snapshots (rotação/borda)", () => {
    const live = {
      blocks: [{ id: "b1", style: { rotation: 0, borderRadius: 0 } }],
    };
    const snap = buildDeckEditorSnapshot(playlist([slide("a", 0)]), "a", live, "a");
    const past = pushDeckHistory([], snap);
    const stored = past[0]!.playlist.slides![0]!.nativeConfig as {
      blocks: Array<{ style: { rotation: number; borderRadius: number } }>;
    };
    live.blocks[0]!.style.rotation = 25;
    live.blocks[0]!.style.borderRadius = 40;
    expect(stored.blocks[0]!.style.rotation).toBe(0);
    expect(stored.blocks[0]!.style.borderRadius).toBe(0);
  });
});
