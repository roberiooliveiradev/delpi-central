import { describe, expect, it } from "vitest";

import type { Playlist } from "../api/tvDashboardApi";
import { filterPlaylists } from "./PlaylistsPage";

function pl(partial: Partial<Playlist> & Pick<Playlist, "id" | "name">): Playlist {
  return {
    publicToken: "tok",
    viewportProfile: "1080p",
    transitionStyle: "fade",
    defaultDurationSec: 30,
    globalRefreshSec: 60,
    isActive: true,
    viewCount: 0,
    lastPresentedAt: null,
    ...partial,
  };
}

describe("filterPlaylists", () => {
  const items = [
    pl({ id: "1", name: "PPM", isActive: true, lastPresentedAt: "2026-07-20T10:00:00Z", viewCount: 9 }),
    pl({
      id: "2",
      name: "GR - Engenharia",
      isActive: true,
      lastPresentedAt: "2026-07-21T16:00:00Z",
      viewCount: 799,
    }),
    pl({ id: "3", name: "Teste", isActive: false, lastPresentedAt: null, viewCount: 1 }),
  ];

  it("Recentes ordena pela última exibição", () => {
    const ids = filterPlaylists(items, "recent", "").map((item) => item.id);
    expect(ids).toEqual(["2", "1", "3"]);
  });

  it("Ativas / Inativas filtram status", () => {
    expect(filterPlaylists(items, "active", "").map((i) => i.id)).toEqual(["2", "1"]);
    expect(filterPlaylists(items, "inactive", "").map((i) => i.id)).toEqual(["3"]);
  });

  it("busca por nome", () => {
    expect(filterPlaylists(items, "recent", "eng").map((i) => i.id)).toEqual(["2"]);
  });
});
