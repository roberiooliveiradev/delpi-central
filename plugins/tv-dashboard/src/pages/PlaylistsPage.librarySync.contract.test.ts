import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

describe("playlist library live sync contract", () => {
  it("PlaylistsPage uses usePlaylistLibrarySync soft refresh", () => {
    const page = readFileSync(join(__dirname, "PlaylistsPage.tsx"), "utf8");
    expect(page).toMatch(/usePlaylistLibrarySync/);
    expect(page).toMatch(/load\(\{\s*soft:\s*true\s*\}\)/);
  });
});
