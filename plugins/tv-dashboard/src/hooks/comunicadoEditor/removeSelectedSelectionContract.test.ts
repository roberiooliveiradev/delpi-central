import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

/**
 * Excluir bloco não deve auto-selecionar o «próximo» do slide.
 */
describe("removeSelected selection contract", () => {
  it("limpa seleção após excluir (não pega nextBlocks[0])", () => {
    const here = dirname(fileURLToPath(import.meta.url));
    const src = readFileSync(join(here, "useComunicadoEditorBlocks.ts"), "utf8");
    const removeFn = src.slice(src.indexOf("const removeSelected = useCallback"));
    expect(removeFn).toMatch(/selectBlocksByIds\(\[\]\)/);
    expect(removeFn).not.toMatch(/selectBlocksByIds\(nextBlocks\[0\]/);
  });
});
