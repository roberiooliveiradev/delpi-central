import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

describe("SlideCurrentRibbon batch actions", () => {
  it("age na lista do filmstrip e exporta a seleção", () => {
    const ribbon = readFileSync(join(here, "SlideCurrentRibbon.tsx"), "utf8");
    const chrome = readFileSync(join(here, "DeckEditorChrome.tsx"), "utf8");
    const page = readFileSync(join(here, "../pages/PlaylistEditorPage.tsx"), "utf8");

    expect(ribbon).toContain("selectedSlides");
    expect(ribbon).toContain("onDuplicate(targets)");
    expect(ribbon).toContain("onToggleActive(targets)");
    expect(ribbon).toContain("onRemove(targets)");
    expect(ribbon).toContain("onExportPng");
    expect(chrome).toContain("selectedSlides={selectedSlides}");
    expect(page).toContain("handleDuplicateSlides(targets)");
    expect(page).toContain("handleToggleSlidesActive(targets)");
    expect(page).toContain("handleRemoveSlides(targets)");
    expect(page).toContain("slideBatchDuplicated");
    expect(page).toContain("resolveExportSlideTargets");
    expect(page).toContain("exportSlidesPptx");
    expect(page).toContain("exportSlidesToPdf");
  });
});
