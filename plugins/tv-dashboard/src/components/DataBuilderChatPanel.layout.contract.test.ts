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
 * Layout do catálogo: chrome + main + draft tray; sem Assistente IA.
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

  it("não expõe Assistente IA nem composer de chat", () => {
    expect(source).not.toContain('data-discovery="ai"');
    expect(source).not.toContain("discoveryMode");
    expect(source).not.toContain("td-data-builder-chat__composer");
    expect(source).not.toContain("modeAi");
    expect(source).toContain('data-discovery="search"');
    expect(source).toContain("DataRouteCatalogPanel");
  });

  it("microcopy de catálogo sem Filial/Período globais no topo", () => {
    expect(content).toContain("draftCount");
    expect(content).toContain("adjustFilters");
    expect(content).toContain("catalogHint");
    expect(content).toContain("Fontes de dados");
    expect(content).not.toContain("Assistente IA");
    expect(content).not.toContain("modeAi");
    expect(content).not.toContain("sessionHint");
    expect(content).not.toContain("branchLabel");
  });
});
