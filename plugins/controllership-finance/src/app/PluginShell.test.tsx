import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

const viewerState = {
  viewer: null as {
    firstName: string | null;
    capabilities: { access: boolean; manage: boolean; accessDre: boolean };
  } | null,
  loading: false,
  errorStatus: null as number | null,
  reload: vi.fn(),
};

vi.mock("../app/ViewerContext", () => ({
  useViewerContext: () => viewerState,
}));

vi.mock("@delpi/plugin-ui/index", async () => await import("../test/pluginUiMock"));

import { PluginShell } from "./PluginShell";

const BASE = "/apps/controllership-finance";

afterEach(() => {
  cleanup();
  viewerState.viewer = null;
  viewerState.loading = false;
  viewerState.errorStatus = null;
  window.history.replaceState(null, "", BASE);
});

function renderShell(view: "home" | "received_documents" = "home") {
  return render(
    <PluginShell view={view} basePath={BASE}>
      <div>conteúdo</div>
    </PluginShell>,
  );
}

describe("PluginShell", () => {
  it("renderiza topbar canônica somente com rotas implementadas", () => {
    viewerState.viewer = {
      firstName: "Ana",
      capabilities: { access: true, manage: false, accessDre: false },
    };
    renderShell();
    expect(screen.getByText("Início")).toBeTruthy();
    // «Minhas tarefas» implementada, mas fora da navegação nesta
    // release (decisão de escopo GO CLARA-COMPLETE §18).
    expect(screen.queryByText("Minhas tarefas")).toBeNull();
    // Rotas futuras não aparecem como navegáveis.
    for (const label of [
      "Visão geral",
      "Sala de interação",
      "Administração",
      "Ajuda",
    ]) {
      expect(screen.queryByText(label)).toBeNull();
    }
    expect(screen.getByText("conteúdo")).toBeTruthy();
  });

  it("saudação usa o primeiro nome do viewer-context", () => {
    viewerState.viewer = {
      firstName: "Ana",
      capabilities: { access: true, manage: false, accessDre: false },
    };
    renderShell();
    expect(screen.getByText("Olá, Ana")).toBeTruthy();
  });

  it("identidade ausente cai no fallback seguro", () => {
    viewerState.viewer = null;
    renderShell();
    expect(screen.getByText(/^Olá$/)).toBeTruthy();
  });

  it("Ctrl+K abre a paleta de comandos", () => {
    viewerState.viewer = {
      firstName: "Ana",
      capabilities: { access: true, manage: false, accessDre: false },
    };
    renderShell();
    expect(screen.queryByRole("dialog")).toBeNull();
    fireEvent.keyDown(window, { key: "k", ctrlKey: true });
    expect(screen.getByRole("dialog")).toBeTruthy();
  });

  it("gatilho de busca na topbar abre a paleta", () => {
    viewerState.viewer = {
      firstName: "Ana",
      capabilities: { access: true, manage: false, accessDre: false },
    };
    renderShell();
    fireEvent.click(
      screen.getByLabelText("Abrir busca do Portal Controladoria & Finanças"),
    );
    expect(screen.getByRole("dialog")).toBeTruthy();
  });

  it("viewer somente-DRE vê a MESMA top bar com «Início» (RW04)", () => {
    viewerState.viewer = {
      firstName: "Bruno",
      capabilities: { access: false, manage: false, accessDre: true },
    };
    renderShell("home");
    // Exatamente um item «Início» — o mesmo da experiência interna.
    expect(screen.getAllByText("Início")).toHaveLength(1);
    expect(screen.getByText("Acesso DRE")).toBeTruthy();
    // Busca restrita continua disponível para o público DRE.
    fireEvent.click(
      screen.getByLabelText("Abrir busca do Portal Controladoria & Finanças"),
    );
    expect(screen.getByRole("dialog")).toBeTruthy();
  });

  it("viewer com access + accessDre não vê Início duplicado", () => {
    viewerState.viewer = {
      firstName: "Ana",
      capabilities: { access: true, manage: false, accessDre: true },
    };
    renderShell();
    expect(screen.getAllByText("Início")).toHaveLength(1);
    expect(screen.getByText("Acesso ao portal")).toBeTruthy();
  });
});
