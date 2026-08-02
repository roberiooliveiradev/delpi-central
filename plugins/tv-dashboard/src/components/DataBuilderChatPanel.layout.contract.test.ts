import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const here = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(join(here, "DataBuilderChatPanel.tsx"), "utf8");
const content = readFileSync(
  join(here, "../content/dataBuilderChatContent.ts"),
  "utf8",
);

/**
 * Layout do Assistente: chrome (modos) + main dominante + draft tray.
 * Filtros de filial/período só no detalhe Testar/Adicionar (não no topo).
 */
describe("DataBuilderChatPanel layout contract", () => {
  it("usa zonas chrome / main / draft-tray sem barra de sessão no topo", () => {
    expect(source).toContain('className="td-data-builder-chat__chrome"');
    expect(source).toContain('className="td-data-builder-chat__main"');
    expect(source).toContain('className="td-data-builder-chat__draft-tray"');
    expect(source).not.toContain('className="td-data-builder-chat__session"');
    expect(source).not.toContain('className="td-data-builder-chat__config"');
    expect(source).toContain("onTestRoute={handleTestCatalogRoute}");
  });

  it("composer IA fica dentro da zona main (não abaixo do rascunho)", () => {
    const mainIdx = source.indexOf('className="td-data-builder-chat__main"');
    const composerIdx = source.indexOf('className="td-data-builder-chat__composer"');
    const trayIdx = source.indexOf('className="td-data-builder-chat__draft-tray"');
    expect(mainIdx).toBeGreaterThan(-1);
    expect(composerIdx).toBeGreaterThan(mainIdx);
    expect(trayIdx).toBeGreaterThan(composerIdx);
  });

  it("Search e IA têm marcadores de discovery distintos", () => {
    expect(source).toContain('data-discovery="search"');
    expect(source).toContain('data-discovery="ai"');
    expect(source).toContain("DataRouteCatalogPanel");
  });

  it("microcopy sem Filial/Período globais no topo", () => {
    expect(content).toContain("draftCount");
    expect(content).toContain("adjustFilters");
    expect(content).toContain("modeSearchHint");
    expect(content).not.toContain("sessionHint");
    expect(content).not.toContain("branchLabel");
    expect(content).not.toContain("periodDaysLabel");
    expect(content).not.toContain("configTitle");
    expect(content).not.toContain("configHint");
  });
});
