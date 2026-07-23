import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

describe("FormatRibbonFrameSection — sem popover interno", () => {
  it("não monta tile Posição / AnchoredPanelPortal aninhado", () => {
    const src = readFileSync(resolve(__dirname, "./FormatRibbonFrameSection.tsx"), "utf8");
    expect(src).not.toContain("FrameSizeBandOrInline");
    expect(src).not.toContain("td-frame-size-entry");
    expect(src).not.toContain("AnchoredPanelPortal");
    expect(src).toContain('groupId="frame-size"');
    expect(src).toContain('label="Tamanho e posição"');
  });
});
