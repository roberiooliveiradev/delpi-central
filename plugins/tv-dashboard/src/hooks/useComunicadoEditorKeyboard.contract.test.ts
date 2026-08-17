import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

describe("useComunicadoEditorKeyboard — Ctrl+A", () => {
  it("seleciona todos os ids visíveis do palco e não rouba o atalho em campo editável", () => {
    const src = readFileSync(join(here, "useComunicadoEditorKeyboard.ts"), "utf8");
    expect(src).toContain('key === "a"');
    expect(src).toContain("listStageSelectableIds");
    expect(src).toContain("isEditableKeyboardTarget");
  });
});
