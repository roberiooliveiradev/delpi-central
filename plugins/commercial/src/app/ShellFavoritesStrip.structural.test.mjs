#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));

describe("ShellFavoritesStrip", () => {
  it("PluginShell monta favoritos no slot secondary da TopBar", () => {
    const shell = readFileSync(join(here, "PluginShell.tsx"), "utf8");
    assert.match(shell, /ShellFavoritesStrip/);
    assert.match(shell, /secondary=\{<ShellFavoritesStrip/);
  });

  it("usa popover AnchoredPanelPortal e store compartilhado", () => {
    const strip = readFileSync(join(here, "ShellFavoritesStrip.tsx"), "utf8");
    assert.match(strip, /AnchoredPanelPortal/);
    assert.match(strip, /subscribeHomeFavorites/);
    assert.match(strip, /refreshHomeFavorites/);
    assert.match(strip, /cm-shell-favorites__trigger/);
    assert.match(strip, /favoritesEmpty/);
  });

  it("HomePage publica favoritos no store (sync topbar)", () => {
    const home = readFileSync(
      join(here, "../features/home/HomePage.tsx"),
      "utf8",
    );
    assert.match(home, /subscribeHomeFavorites/);
    assert.match(home, /setHomeFavoritesLocal/);
    assert.match(home, /replaceHomeFavorites/);
    assert.doesNotMatch(home, /putHomeFavorites\(/);
  });
});
