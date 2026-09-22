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

  it("workspace overflow usa menu canônico e highlights factuais do chrome", () => {
    const chrome = readFileSync(join(root, "ui/processes/ProcessWorkspaceChrome.tsx"), "utf8");
    expect(chrome).toMatch(/AnchoredPanelPortal/);
    expect(chrome).toMatch(/ContextMenuItem/);
    expect(chrome).toMatch(/id: "melhorias"/);
    expect(chrome).toMatch(/id: "revisoes"/);
    expect(chrome).not.toMatch(/id: "arquivos"/);
    expect(chrome).not.toMatch(/tm-processo-workspace-chrome__more-menu/);
  });
});

describe("Hero consolidation density", () => {
  it("chrome mantém hero do processo em todos os escopos e nav de seção legível", () => {
    const chrome = readFileSync(join(root, "ui/processes/ProcessWorkspaceChrome.tsx"), "utf8");
    expect(chrome).toMatch(/heroExtras/);
    expect(chrome).toMatch(/instanceHighlights/);
    expect(chrome).toMatch(/revisionHighlights/);
    expect(chrome).toMatch(/revisionActions/);
    expect(chrome).toMatch(/Excluir revisão/);
    expect(chrome).toMatch(/aria-label="Processo"/);
    expect(chrome).toMatch(/tm-processo-workspace-chrome__nested-hero/);
    expect(chrome).toMatch(/tm-processo-workspace-chrome__section-nav/);
    expect(chrome).not.toMatch(/TmUnderlineNav\s*\n(?:[^\n]*\n){0,6}[^\n]*density="compact"/);
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

  it("sync de heroExtras no workspace respeita Rules of Hooks (efeito antes de early return)", () => {
    for (const rel of ["ui/pages/ProcessDetailPage.tsx", "ui/pages/InstanceDetailPage.tsx"]) {
      const source = readFileSync(join(root, rel), "utf8");
      const heroEffect = source.indexOf("onHeroExtrasChange(");
      const loadingReturn = source.indexOf("if (loading && !");
      expect(heroEffect).toBeGreaterThan(-1);
      expect(loadingReturn).toBeGreaterThan(-1);
      expect(heroEffect).toBeLessThan(loadingReturn);
      expect(source).toMatch(/embeddedActive \|\| !onHeroExtrasChange/);
    }
  });
});
