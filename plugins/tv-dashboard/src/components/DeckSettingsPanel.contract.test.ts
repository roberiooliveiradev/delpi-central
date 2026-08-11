import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

describe("DeckSettingsPanel kit controls", () => {
  const source = readFileSync(
    resolve(dirname(fileURLToPath(import.meta.url)), "./DeckSettingsPanel.tsx"),
    "utf8",
  );

  it("usa a galeria visual do kit para transições", () => {
    expect(source).toContain("TransitionGallery");
    expect(source).toContain("PRESENTATION_TRANSITION_STYLES");
    expect(source).not.toContain("ToolbarSelectField");
    expect(source).not.toContain("TdRibbonSelect");
    expect(source).not.toContain("TdNativeSelectField");
    expect(source).toContain("td-deck-ribbon-tile-popover--transition");
    expect(source).not.toMatch(
      /panelLabel="Transição da (tela|programação)"\s+panelClassName="td-deck-ribbon-tile-popover--narrow"/,
    );
  });
});

describe("SectionPropertiesPanel kit controls", () => {
  const source = readFileSync(
    resolve(dirname(fileURLToPath(import.meta.url)), "./SectionPropertiesPanel.tsx"),
    "utf8",
  );

  it("não usa select/input HTML crus", () => {
    expect(source).toContain("HostContainedDialog");
    expect(source).toContain("TransitionGallery");
    expect(source).toContain("PRESENTATION_TRANSITION_STYLES");
    expect(source).toContain("NativeCheckboxControl");
    expect(source).not.toMatch(/<select\b/);
    expect(source).not.toMatch(/<input\b/);
  });
});
