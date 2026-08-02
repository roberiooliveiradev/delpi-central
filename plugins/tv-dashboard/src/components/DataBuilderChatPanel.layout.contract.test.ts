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
 * Layout do Assistente: session bar + main dominante + draft tray.
 * Search ≠ composer; IA ≠ catálogo; chrome compartilhado.
 */
describe("DataBuilderChatPanel layout contract", () => {
  it("usa zonas chrome / main / draft-tray", () => {
    expect(source).toContain('className="td-data-builder-chat__chrome"');
    expect(source).toContain('className="td-data-builder-chat__main"');
    expect(source).toContain('className="td-data-builder-chat__draft-tray"');
    expect(source).toContain('className="td-data-builder-chat__session"');
    expect(source).not.toContain('className="td-data-builder-chat__config"');
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

  it("microcopy de sessão/bandeja sem card Configuração", () => {
    expect(content).toContain("sessionHint");
    expect(content).toContain("draftCount");
    expect(content).toContain("adjustFilters");
    expect(content).not.toContain("configTitle");
    expect(content).not.toContain("configHint");
  });
});
