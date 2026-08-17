import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));

describe("mesmo tamanho — contrato de source", () => {
  it("ribbon Organizar expõe tile após Alinhar e clique = ambos", () => {
    const source = readFileSync(
      join(here, "../components/formatRibbon/FormatRibbonOrganizeGroup.tsx"),
      "utf8",
    );
    expect(source).toContain("sameSizeSelected");
    expect(source).toContain('sameSizeSelected("both")');
    expect(source.indexOf('label="Alinhar"')).toBeLessThan(source.indexOf("label={H.sameSize}"));
  });

  it("menu de contexto tem ContextMenuSub de Mesmo tamanho", () => {
    const source = readFileSync(
      join(here, "../components/ComunicadoStageContextMenu.tsx"),
      "utf8",
    );
    expect(source).toContain("ContextMenuSub label={C.sameSize}");
    expect(source).toContain('sameSizeSelected("both")');
    expect(source).toContain('sameSizeSelected("width")');
    expect(source).toContain('sameSizeSelected("height")');
  });
});
