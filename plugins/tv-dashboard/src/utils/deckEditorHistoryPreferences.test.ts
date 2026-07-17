import { afterEach, beforeEach, describe, expect, it } from "vitest";

import {
  clearDeckEditorHistory,
  DECK_EDITOR_HISTORY_POINTER_LIMIT,
  normalizeDeckEditorHistoryStore,
  readDeckEditorHistory,
  writeDeckEditorHistory,
} from "./deckEditorHistoryPreferences";

describe("deckEditorHistoryPreferences", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  afterEach(() => {
    window.localStorage.clear();
  });

  it("persiste somente IDs e revisões de past/future", () => {
    writeDeckEditorHistory("pl-1", [{ snapshotId: "snap-1", revision: 4 }], []);
    const stored = readDeckEditorHistory("pl-1");
    expect(stored?.past).toHaveLength(1);
    expect(stored?.future).toHaveLength(0);
    expect(stored?.past[0]).toEqual({ snapshotId: "snap-1", revision: 4 });
    expect(window.localStorage.getItem("td-deck-editor-history:pl-1")).not.toContain("playlist");
  });

  it("rejeita snapshots legados e limpa sob demanda", () => {
    expect(normalizeDeckEditorHistoryStore({ version: 99 })).toBeNull();
    expect(
      normalizeDeckEditorHistoryStore({
        version: 2,
        updatedAt: 1,
        past: [{ playlist: { id: "pl-1" } }],
        future: [],
      })?.past,
    ).toEqual([]);
    window.localStorage.setItem(
      "td-deck-editor-history:legacy",
      JSON.stringify({ version: 1, updatedAt: 1, past: [{ playlist: { id: "legacy" } }], future: [] }),
    );
    expect(readDeckEditorHistory("legacy")).toBeNull();
    expect(window.localStorage.getItem("td-deck-editor-history:legacy")).toBeNull();
    writeDeckEditorHistory("pl-1", [{ snapshotId: "snap-1", revision: 1 }], []);
    clearDeckEditorHistory("pl-1");
    expect(readDeckEditorHistory("pl-1")).toBeNull();
  });

  it("mantém até 500 ponteiros por pilha", () => {
    const pointers = Array.from(
      { length: DECK_EDITOR_HISTORY_POINTER_LIMIT + 1 },
      (_, revision) => ({ snapshotId: `snap-${revision}`, revision }),
    );
    writeDeckEditorHistory("pl-500", pointers, pointers);

    const stored = readDeckEditorHistory("pl-500");
    expect(stored?.past).toHaveLength(DECK_EDITOR_HISTORY_POINTER_LIMIT);
    expect(stored?.future).toHaveLength(DECK_EDITOR_HISTORY_POINTER_LIMIT);
    expect(stored?.past[0]).toEqual({ snapshotId: "snap-1", revision: 1 });
  });
});
