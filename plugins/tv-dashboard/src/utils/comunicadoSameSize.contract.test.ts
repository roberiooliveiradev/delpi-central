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
    const alignAt = source.indexOf('label="Alinhar"');
    const sameAt = source.indexOf('label="Igualar"');
    expect(alignAt).toBeGreaterThanOrEqual(0);
    expect(sameAt).toBeGreaterThan(alignAt);
    expect(source.slice(sameAt, sameAt + 500)).toContain('sameSizeSelected("both")');
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
