import { describe, expect, it, beforeEach, afterEach, vi } from "vitest";

import {
  readDataPreviewCache,
  readPlaylistShell,
  resolvedMapsEqual,
  writeDataPreviewCache,
  writePlaylistShell,
} from "./editorSessionCache";
import type { Playlist } from "../api/tvDashboardApi";

describe("editorSessionCache", () => {
  beforeEach(() => {
    window.sessionStorage.clear();
  });

  afterEach(() => {
    window.sessionStorage.clear();
  });

  it("persiste e lê shell da playlist", () => {
    const playlist = {
      id: "pl-1",
      publicToken: "tok",
      name: "Deck",
      viewportProfile: "full_hd",
      transitionStyle: "fade",
      defaultDurationSec: 10,
      globalRefreshSec: 300,
      isActive: true,
      viewCount: 0,
      slides: [],
    } satisfies Playlist;

    writePlaylistShell(playlist);
    expect(readPlaylistShell("pl-1")?.name).toBe("Deck");
    expect(readPlaylistShell("other")).toBeNull();
  });

  it("só devolve data preview quando fingerprint bate", () => {
    writeDataPreviewCache("pl-1", "fp-a", {
      "b1": { kpi: { value: 1, label: "A" } },
    });
    expect(readDataPreviewCache("pl-1", "fp-a")["b1"]?.kpi?.value).toBe(1);
    expect(readDataPreviewCache("pl-1", "fp-b")).toEqual({});
  });

  it("resolvedMapsEqual ignora identidade de referência", () => {
    const a = { b1: { kpi: { value: 1, label: "A" } } };
    const b = { b1: { kpi: { value: 1, label: "A" } } };
    expect(resolvedMapsEqual(a, b)).toBe(true);
    expect(resolvedMapsEqual(a, { b1: { kpi: { value: 2, label: "A" } } })).toBe(false);
  });
});
