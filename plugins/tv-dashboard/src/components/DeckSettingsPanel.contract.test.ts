import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

describe("DeckSettingsPanel kit controls", () => {
  const source = readFileSync(
    resolve(dirname(fileURLToPath(import.meta.url)), "./DeckSettingsPanel.tsx"),
    "utf8",
  );

  it("usa ToolbarSelectField / TdRibbonSelect em vez de NativeSelect na ribbon", () => {
    expect(source).toContain("ToolbarSelectField");
    expect(source).toContain("TdRibbonSelect");
    expect(source).not.toContain("TdNativeSelectField");
  });
});

describe("SectionPropertiesPanel kit controls", () => {
  const source = readFileSync(
    resolve(dirname(fileURLToPath(import.meta.url)), "./SectionPropertiesPanel.tsx"),
    "utf8",
  );

  it("não usa select/input HTML crus", () => {
    expect(source).toContain("HostContainedDialog");
    expect(source).toContain("TdRibbonSelect");
    expect(source).toContain("NativeCheckboxControl");
    expect(source).not.toMatch(/<select\b/);
    expect(source).not.toMatch(/<input\b/);
  });
});
