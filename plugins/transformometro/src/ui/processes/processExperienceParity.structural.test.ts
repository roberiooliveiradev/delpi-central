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

  it("lista move filtros primários e presentation controls para o Hero", () => {
    const page = readFileSync(join(root, "ui/pages/ProcessesPage.tsx"), "utf8");
    expect(page).toMatch(/highlights=\{heroHighlights\}/);
    expect(page).toMatch(/tm-processo-list-hero-controls/);
    expect(page).toMatch(/hideBrowseToggle/);
    expect(page).toMatch(/hideRecordCount/);
    expect(page).toMatch(/hideListToolbar/);
    expect(page).toMatch(/ProcessListPresentationControls/);
  });

  it("workspace overflow usa menu canônico e highlight de arquivos", () => {
    const chrome = readFileSync(join(root, "ui/processes/ProcessWorkspaceChrome.tsx"), "utf8");
    expect(chrome).toMatch(/AnchoredPanelPortal/);
    expect(chrome).toMatch(/ContextMenuItem/);
    expect(chrome).toMatch(/id: "arquivos"/);
    expect(chrome).not.toMatch(/tm-processo-workspace-chrome__more-menu/);
  });
});

describe("Hero consolidation density", () => {
  it("chrome integra presence slot e highlights de instância/revisão", () => {
    const chrome = readFileSync(join(root, "ui/processes/ProcessWorkspaceChrome.tsx"), "utf8");
    expect(chrome).toMatch(/heroExtras/);
    expect(chrome).toMatch(/instanceHighlights/);
    expect(chrome).toMatch(/revisionHighlights/);
    expect(chrome).toMatch(/revisionActions/);
    expect(chrome).toMatch(/Excluir revisão/);
  });

  it("revisão deixa de renderizar identity card quando chrome owns identity", () => {
    const toolbar = readFileSync(
      join(root, "ui/revision/registration/RevisionActivateToolbar.tsx"),
      "utf8",
    );
    const panel = readFileSync(join(root, "ui/pages/RevisionRegistrationPanel.tsx"), "utf8");
    expect(toolbar).toMatch(/chromeOwnsIdentity/);
    expect(toolbar).toMatch(/if \(chromeOwnsIdentity\) return null/);
    expect(panel).toMatch(/chromeOwnsIdentity=\{chromeOwnsIdentity\}/);
    expect(panel).toMatch(/ds-rateio-diag/);
  });

  it("instância omite summary duplicado no read view embutido", () => {
    const page = readFileSync(join(root, "ui/pages/InstanceDetailPage.tsx"), "utf8");
    const read = readFileSync(join(root, "components/instance/InstanceReadView.tsx"), "utf8");
    expect(page).toMatch(/omitHeroSummary=\{embedded\}/);
    expect(read).toMatch(/omitHeroSummary/);
  });
});
