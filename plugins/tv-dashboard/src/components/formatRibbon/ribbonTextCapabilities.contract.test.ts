/**
 * RIBBON-TEXT-001 — matrices de contrato (Ribbon / Text / Ownership).
 */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const typography = readFileSync(
  resolve(__dirname, "./FormatRibbonTypographySections.tsx"),
  "utf8",
);
const spacing = readFileSync(resolve(__dirname, "./ParagraphSpacingMenu.tsx"), "utf8");
const textBlock = readFileSync(
  resolve(__dirname, "../ComunicadoEditorTextBlock.tsx"),
  "utf8",
);
const patchService = readFileSync(
  resolve(
    __dirname,
    "../../../../../tv-dashboard-api/tv_app/application/services/data/presentation_mutation/patch_service.py",
  ),
  "utf8",
);

describe("RIBBON-TEXT-001 matrices", () => {
  it("Ribbon: sub/sup, case, indent, bump size, paragraph spacing", () => {
    expect(typography).toContain("Subscript");
    expect(typography).toContain("Superscript");
    expect(typography).toContain("transformSelectedTextCase");
    expect(typography).toContain("IndentIncrease");
    expect(typography).toContain("IndentDecrease");
    expect(typography).toContain("fontSizeMode: \"delta\"");
    expect(typography).toContain("paragraphSpacingBefore");
    expect(typography).toContain("paragraphSpacingAfter");
    expect(typography).toContain("updateSelectedTextFormatStyle");
    expect(typography).not.toMatch(/text-transform:\s*uppercase/i);
  });

  it("ParagraphSpacing: Antes/Depois separados de letterSpacing", () => {
    expect(spacing).toContain("Espaçamento antes do parágrafo");
    expect(spacing).toContain("Espaçamento depois do parágrafo");
    expect(spacing).toContain("Entre caracteres");
    expect(spacing).toContain("onParagraphSpacingBefore");
  });

  it("A11y: Ctrl+B/I/U e Ctrl+= / Ctrl+Shift+= sub/sup", () => {
    expect(textBlock).toContain('key === "b"');
    expect(textBlock).toContain('key === "i"');
    expect(textBlock).toContain('key === "u"');
    expect(textBlock).toContain("subscript");
    expect(textBlock).toContain("superscript");
  });

  it("Ownership: BE ops transform_text_case + bump_font_size + style normalize", () => {
    expect(patchService).toContain("_op_transform_text_case");
    expect(patchService).toContain("_op_bump_font_size");
    expect(patchService).toContain("normalize_block_text_style");
    expect(patchService).toContain('"transform_text_case"');
    expect(patchService).toContain('"bump_font_size"');
    expect(patchService).toContain("range_start");
  });

  it("Opcionais classificados (não implementados nesta entrega)", () => {
    expect(typography).not.toContain("formatPainter");
    expect(typography).not.toContain("showFormattingMarks");
    expect(typography).not.toMatch(/multilevel|nestedList/i);
  });
});
