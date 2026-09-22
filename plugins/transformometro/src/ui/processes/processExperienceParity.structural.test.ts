import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const root = join(dirname(fileURLToPath(import.meta.url)), "../..");

describe("Process experience parity wiring", () => {
  it("workspace usa path + underline nav sem sidebar de pastas", () => {
    const page = readFileSync(join(root, "ui/pages/ProcessWorkspacePage.tsx"), "utf8");
    const chrome = readFileSync(join(root, "ui/processes/ProcessWorkspaceChrome.tsx"), "utf8");
    const shell = readFileSync(join(root, "ui/processes/ProcessWorkspaceShell.tsx"), "utf8");
    expect(page).toMatch(/ProcessWorkspaceChrome/);
    expect(chrome).toMatch(/TmPagePath/);
    expect(chrome).toMatch(/TmUnderlineNav/);
    expect(chrome).toMatch(/TmPageHero/);
    expect(shell).not.toMatch(/ProcessWorkspaceSidebar/);
    expect(shell).toMatch(/tm-processo-workspace--flat/);
  });

  it("lista move filtros primários para o Hero", () => {
    const page = readFileSync(join(root, "ui/pages/ProcessesPage.tsx"), "utf8");
    expect(page).toMatch(/highlights=\{heroHighlights\}/);
    expect(page).toMatch(/tm-processo-list-hero-controls/);
    expect(page).toMatch(/hideBrowseToggle/);
  });
});
