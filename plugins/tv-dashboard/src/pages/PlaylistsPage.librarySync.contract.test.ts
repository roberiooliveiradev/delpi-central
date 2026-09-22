import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

describe("playlist library live sync contract", () => {
  it("PlaylistsPage uses usePlaylistLibrarySync soft refresh", () => {
    const page = readFileSync(join(__dirname, "PlaylistsPage.tsx"), "utf8");
    expect(page).toMatch(/usePlaylistLibrarySync/);
    expect(page).toMatch(/useLibrarySoftRefreshOnFocus/);
    expect(page).toMatch(/softLoad|load\(\{\s*soft:\s*true\s*\}\)/);
  });

  it("usePlaylistLibrarySync polls access token", () => {
    const hook = readFileSync(
      join(__dirname, "../hooks/usePlaylistLibrarySync.ts"),
      "utf8",
    );
    expect(hook).toMatch(/setInterval\(syncToken/);
    expect(hook).toMatch(/buildPlaylistLibraryWsUrl/);
  });
});
