import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

describe("CanvasTableContextMenu (contrato)", () => {
  const menu = readFileSync(join(here, "CanvasTableContextMenu.tsx"), "utf8");
  const editor = readFileSync(join(here, "ComunicadoEditorBlockView.tsx"), "utf8");

  it("usa ContextMenu do kit com portalScopeClassName do MFE", () => {
    expect(menu).toMatch(/ContextMenu/);
    expect(menu).toMatch(/portalScopeClassName=\{TV_DASHBOARD_ROOT_CLASS\}/);
    expect(menu).not.toMatch(/position:\s*absolute/);
  });

  it("EditorCanvasTableBlock monta o menu e passa onCellContextMenu", () => {
    expect(editor).toContain("CanvasTableContextMenu");
    expect(editor).toContain("onCellContextMenu");
  });

  it("expõe Copiar/Recortar/Colar via session clipboard (sem execCommand)", () => {
    expect(menu).toContain('label="Copiar"');
    expect(menu).toContain('label="Recortar"');
    expect(menu).toContain('label="Colar"');
    expect(menu).toContain("serializeCanvasTableClipboard");
    expect(menu).toContain("setCanvasTableSessionClipboard");
    expect(menu).not.toContain("execCommand");
  });

  it("Quebrar texto usa toggle canônico (não só pre-wrap fixo)", () => {
    expect(menu).toContain("nextCanvasTableWhiteSpaceToggle");
    expect(menu).toContain('label="Quebrar texto"');
    expect(menu).toContain('label="Não quebrar"');
  });
});
