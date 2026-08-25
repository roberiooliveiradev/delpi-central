import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

describe("slide timing UX contract", () => {
  it("aba Slide herda duração e filmstrip mostra badge efetivo", () => {
    const panel = readFileSync(join(here, "DeckSettingsPanel.tsx"), "utf8");
    const filmstrip = readFileSync(join(here, "SlideFilmstrip.tsx"), "utf8");
    const css = readFileSync(join(here, "../index.css"), "utf8");

    expect(panel).toContain("Herdar duração");
    expect(panel).toContain("durationSec: null");
    expect(panel).toContain("resolveSlideDurationSec");
    expect(panel).toContain("onCommit");
    expect(filmstrip).toContain("td-deck-filmstrip__timing");
    expect(filmstrip).toContain("resolveSlideDurationSec");
    expect(css).toMatch(/\.td-deck-filmstrip__timing--override\s*\{/);
    expect(css).toMatch(/\.td-deck-slide-timing__badge\s*\{/);
  });

  it("DeckWorkspace encaminha a duração da programação ao filmstrip", () => {
    const workspace = readFileSync(join(here, "DeckWorkspace.tsx"), "utf8");
    const page = readFileSync(join(here, "../pages/PlaylistEditorPage.tsx"), "utf8");

    expect(page).toContain("defaultDurationSec: playlist.defaultDurationSec");
    expect(workspace).toContain("defaultDurationSec");
    expect(workspace).toContain("defaultDurationSec={defaultDurationSec}");
    expect(workspace).toContain("defaultTransitionStyle={defaultTransitionStyle}");
  });
});
