import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

/**
 * Regressão: Design/Layout da tabela sumiam com `selectedTablePart` (coluna),
 * deixando a sidebar vazia ao marcar/desmarcar colunas após foco no palco.
 */
describe("ComunicadoElementInspector table block sections", () => {
  it("mantém seções Design/Layout mesmo com parte/coluna selecionada", () => {
    const source = readFileSync(resolve(__dirname, "./ComunicadoElementInspector.tsx"), "utf8");
    expect(source).toContain("keepTableBlockSections");
    expect(source).toContain("showTableBlockSections");
    expect(source).toMatch(
      /keepTableBlockSections\s*=\s*[\s\S]*panelFocus === "tableDesign"[\s\S]*panelFocus === "tableLayout"/,
    );
    expect(source).toMatch(
      /showTableBlockSections\s*=\s*[\s\S]*!selectedTablePart \|\| keepTableBlockSections/,
    );
  });
});
