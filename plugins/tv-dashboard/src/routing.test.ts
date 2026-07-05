import { describe, it, expect } from "vitest";

import {
  newPlaylistPath,
  parseTvDashboardRoute,
  playlistPath,
  playlistPreviewPath,
  playlistSharePath,
} from "./routing";

describe("parseTvDashboardRoute", () => {
  it("parses list", () => {
    expect(parseTvDashboardRoute("/apps/tv-dashboard")).toEqual({ view: "list" });
  });

  it("parses new playlist", () => {
    expect(parseTvDashboardRoute("/apps/tv-dashboard/playlists/new")).toEqual({ view: "new" });
  });

  it("parses editor preview and share", () => {
    const id = "abc-123";
    expect(parseTvDashboardRoute(playlistPath(id))).toEqual({ view: "edit", id });
    expect(parseTvDashboardRoute(playlistPreviewPath(id))).toEqual({ view: "preview", id });
    expect(parseTvDashboardRoute(playlistSharePath(id))).toEqual({ view: "share", id });
  });

  it("supports legacy uuid path", () => {
    expect(parseTvDashboardRoute("/apps/tv-dashboard/abc-123")).toEqual({ view: "edit", id: "abc-123" });
  });

  it("builds canonical paths", () => {
    expect(newPlaylistPath()).toBe("/apps/tv-dashboard/playlists/new");
  });
});
