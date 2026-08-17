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
    assert.doesNotMatch(
      shell,
      /<\/CommercialTopBar>\s*<ShellFavoritesStrip/,
    );
    const strip = readFileSync(join(here, "ShellFavoritesStrip.tsx"), "utf8");
    assert.match(strip, /getHomeFavorites/);
    assert.match(strip, /putHomeFavorites/);
    assert.match(strip, /CommercialHubChipRow/);
    assert.match(strip, /CommercialRouteChip/);
  });
});
