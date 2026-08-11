import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import {
  formatSlideTransitionLabel,
  resolveSlideDurationSec,
  resolveSlideTransitionStyle,
  slideDurationIsOverride,
} from "./slideTimingInheritance";

describe("slideTimingInheritance", () => {
  it("resolve duração slide → seção → playlist", () => {
    expect(
      resolveSlideDurationSec({
        slideDuration: 12,
        sectionDefault: 20,
        playlistDefault: 30,
      }),
    ).toBe(12);
    expect(
      resolveSlideDurationSec({
        slideDuration: null,
        sectionDefault: 20,
        playlistDefault: 30,
      }),
    ).toBe(20);
    expect(
      resolveSlideDurationSec({
        slideDuration: null,
        sectionDefault: null,
        playlistDefault: 30,
      }),
    ).toBe(30);
  });

  it("resolve transição e marca override", () => {
    expect(
      resolveSlideTransitionStyle({
        slideTransition: null,
        sectionTransition: "slide",
        playlistTransition: "fade",
      }),
    ).toBe("slide");
    expect(slideDurationIsOverride(null)).toBe(false);
    expect(slideDurationIsOverride(10)).toBe(true);
    expect(formatSlideTransitionLabel("slide")).toBe("Deslizar");
  });

  it("cria tela personalizada herdando duração e transição", () => {
    const page = readFileSync(
      join(dirname(fileURLToPath(import.meta.url)), "../pages/PlaylistEditorPage.tsx"),
      "utf8",
    );
    const addCustomSlide = page.match(
      /async function handleAddCustomSlide[\s\S]*?async function handleAddSection/,
    )?.[0] ?? page;

    expect(addCustomSlide).toMatch(/durationSec:\s*null/);
    expect(addCustomSlide).toMatch(/transitionStyle:\s*null/);
    expect(addCustomSlide).not.toMatch(/durationSec:\s*customCatalogItem\?\.defaultDurationSec\s*\?\?\s*30/);
  });
});
