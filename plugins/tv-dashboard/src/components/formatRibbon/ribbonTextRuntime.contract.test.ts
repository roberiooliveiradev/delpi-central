/**
 * RIBBON-TEXT-002 — case/range/ack wiring contracts (click → intent → BE).
 */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const typography = readFileSync(
  resolve(__dirname, "./FormatRibbonTypographySections.tsx"),
  "utf8",
);
const tdSelect = readFileSync(resolve(__dirname, "../tdRibbonUi.tsx"), "utf8");
const blocks = readFileSync(
  resolve(__dirname, "../../hooks/comunicadoEditor/useComunicadoEditorBlocks.ts"),
  "utf8",
);
const ack = readFileSync(resolve(__dirname, "../../utils/mutationAckGeneration.ts"), "utf8");
const selectField = readFileSync(
  resolve(__dirname, "../../../../plugin-ui/src/components/forms/SelectField.tsx"),
  "utf8",
);
const patchService = readFileSync(
  resolve(
    __dirname,
    "../../../../../tv-dashboard-api/tv_app/application/services/data/presentation_mutation/patch_service.py",
  ),
  "utf8",
);

describe("RIBBON-TEXT-002 case/ack/range contracts", () => {
  it("TdRibbonSelect preserva foco do contentEditable", () => {
    expect(tdSelect).toContain("preserveTextEditFocusAttr");
    expect(tdSelect).toContain("PRESERVE_TEXT_EDIT_FOCUS_ATTR");
    expect(selectField).toContain("preserveTextEditFocusAttr");
  });

  it("case usa textCase de apresentação (não mutação destrutiva no ribbon)", () => {
    expect(typography).toContain('applyTextFormatStyle({ textCase: next })');
    expect(typography).toContain("textCaseSelectValue");
    expect(typography).toContain("textCaseActiveLabel");
    expect(typography).toContain('value: "none"');
    expect(typography).toContain('label: "minúsculas"');
    expect(typography).toContain('label: "Misto"');
    expect(typography).not.toContain("transformSelectedTextCase");
    expect(typography).not.toMatch(/value=\"\"[\s\S]*Maiúsculas/);
  });

  it("ack aplica nativeConfig com generation gate", () => {
    expect(ack).toContain("createMutationGenerationGate");
    expect(ack).toContain("isCurrent");
    expect(blocks).toContain("ackUpsertBlocksWithGeneration");
    expect(blocks).not.toMatch(
      /void commitUpsertBlocks\(\{[\s\S]*?\}\)\.catch\(\(\) => undefined\)/,
    );
  });

  it("BE range offsets no handler", () => {
    expect(patchService).toContain("range_start");
    expect(patchService).toContain("start=range_start");
  });

  it("font bump canônico + collapse order tipografia", () => {
    expect(typography).toContain("bumpSelectedFontSize");
    expect(typography).toContain('order={0}');
    expect(typography).toContain('order={1}');
    expect(typography).toContain('order={2}');
  });
});
