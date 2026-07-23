import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const base = dirname(fileURLToPath(import.meta.url));

/**
 * Botão direito com trecho selecionado → menu de tipografia parcial
 * (não o menu de bloco/palco nem o menu nativo do browser).
 */
describe("ComunicadoTextSelectionContextMenu (contrato)", () => {
  const textBlock = readFileSync(join(base, "ComunicadoEditorTextBlock.tsx"), "utf8");
  const shapeBlock = readFileSync(join(base, "ComunicadoEditorShapeBlock.tsx"), "utf8");
  const composer = readFileSync(join(base, "ComunicadoComposer.tsx"), "utf8");
  const menu = readFileSync(join(base, "ComunicadoTextSelectionContextMenu.tsx"), "utf8");
  const selection = readFileSync(
    join(base, "../hooks/comunicadoEditor/useComunicadoEditorSelection.ts"),
    "utf8",
  );

  it("editores inline abrem o menu no contextmenu com seleção parcial", () => {
    expect(textBlock).toContain("onContextMenu={handleEditorContextMenu}");
    expect(textBlock).toContain("openTextFormatContextMenu");
    expect(textBlock).toMatch(/live\.end > live\.start/);
    expect(shapeBlock).toContain("onContextMenu={handleEditorContextMenu}");
    expect(shapeBlock).toContain("openTextFormatContextMenu");
    expect(shapeBlock).toMatch(/live\.end > live\.start/);
  });

  it("composer monta o menu e, em edição, redireciona botão direito com trecho", () => {
    expect(composer).toContain("ComunicadoTextSelectionContextMenu");
    expect(composer).toContain("textFormatContextMenu");
    expect(composer).toContain("closeTextFormatContextMenu");
    expect(composer).toMatch(/if \(editingTextId\)/);
    expect(composer).toContain("openTextFormatContextMenu");
    expect(composer).toContain("lastPartialTextEditSelection");
  });

  it("menu oferece tipografia do trecho e preserva foco da edição", () => {
    expect(menu).toContain("toggleEditingTextRunStyle");
    expect(menu).toContain("applyEditingTextRunStylePatch");
    expect(menu).toContain("PRESERVE_TEXT_EDIT_FOCUS_ATTR");
    expect(menu).toMatch(/onMouseDown[\s\S]*preventDefault/);
    expect(menu).toContain("requestRibbonTab(\"format\")");
    expect(selection).toContain("openTextFormatContextMenu");
    expect(selection).toContain("closeTextFormatContextMenu");
    expect(selection).toContain("textFormatContextMenu");
  });
});
