import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const root = join(dirname(fileURLToPath(import.meta.url)), "../..");

describe("Settings workspace sidebar boundary", () => {
  it("settings shell monta a sidebar compartilhada sem a variante flat", () => {
    const shell = readFileSync(
      join(root, "ui/settings/SettingsWorkspaceShell.tsx"),
      "utf8",
    );
    expect(shell).toMatch(/SettingsWorkspaceSidebar/);
    expect(shell).toMatch(/tm-processo-workspace-sidebar-shell/);
    // Settings usa o layout lateral (grid) — a classe `--flat` é exclusiva do
    // Process Workspace, que permanece sem sidebar.
    expect(shell).not.toMatch(/tm-processo-workspace--flat/);
    expect(shell).toMatch(/tm-processo-workspace-sidebar__resize-handle/);
  });

  it("CSS não esconde a sidebar fora do workspace flat", () => {
    const css = readFileSync(join(root, "index.css"), "utf8");
    // display:none só é permitido dentro do boundary `.tm-processo-workspace--flat`.
    // display:none sem o boundary `--flat` é a regressão que escondia a
    // sidebar de Configurações — não pode voltar.
    expect(css).not.toMatch(
      /\.dashboard-transformometro\s+\.tm-processo-workspace-sidebar-shell\s*\{\s*display:\s*none/,
    );
    expect(css).toMatch(
      /\.tm-processo-workspace--flat\s+\.tm-processo-workspace-sidebar-shell\s*\{\s*display:\s*none/,
    );
    // Layout lateral canônico do workspace com sidebar (Settings).
    expect(css).toMatch(
      /\.tm-processo-workspace\s*\{[^}]*grid-template-columns:\s*var\(--tm-workspace-sidebar-width/,
    );
  });

  it("process workspace continua flat e sem sidebar de pastas", () => {
    const shell = readFileSync(
      join(root, "ui/processes/ProcessWorkspaceShell.tsx"),
      "utf8",
    );
    expect(shell).toMatch(/tm-processo-workspace--flat/);
    expect(shell).not.toMatch(/SettingsWorkspaceSidebar|ProcessWorkspaceSidebar/);
  });

  it("sidebar recolhida mantém rail visível (expandir + pesquisar)", () => {
    const sidebar = readFileSync(
      join(root, "ui/settings/SettingsWorkspaceSidebar.tsx"),
      "utf8",
    );
    expect(sidebar).toMatch(/tm-processo-workspace-sidebar--collapsed/);
    expect(sidebar).toMatch(/tm-processo-workspace-sidebar__rail-btn/);
    expect(sidebar).toMatch(/aria-label="Expandir barra lateral"/);
    expect(sidebar).toMatch(/aria-label="Pesquisar nas configurações"/);
  });
});
