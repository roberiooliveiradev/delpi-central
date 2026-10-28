import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

const viewerState = {
  viewer: null as {
    firstName: string | null;
    capabilities: { access: boolean; manage: boolean; accessDre: boolean };
  } | null,
  loading: true,
  errorStatus: null as number | null,
  reload: vi.fn(),
};

vi.mock("../../app/ViewerContext", () => ({
  useViewerContext: () => viewerState,
}));

vi.mock("@delpi/plugin-ui/index", async () => await import("../../test/pluginUiMock"));

import { HomePage } from "./HomePage";

afterEach(() => {
  cleanup();
  viewerState.viewer = null;
  viewerState.loading = true;
  viewerState.errorStatus = null;
  window.localStorage.clear();
  window.history.replaceState(null, "", "/apps/controllership-finance");
});

function setViewer(
  firstName: string | null,
  capabilities: { access: boolean; manage: boolean; accessDre: boolean },
) {
  viewerState.viewer = { firstName, capabilities };
  viewerState.loading = false;
  viewerState.errorStatus = null;
}

describe("HomePage", () => {
  it("exibe loading enquanto o contexto carrega", () => {
    render(<HomePage basePath="/apps/controllership-finance" />);
    expect(screen.getByText("Carregando contexto…")).toBeTruthy();
  });

  it("renderiza o hub com ACCESS — catálogo, busca e eventos honestos", async () => {
    setViewer("Ana", { access: true, manage: false, accessDre: false });
    render(<HomePage basePath="/apps/controllership-finance" />);
    expect(screen.getByText("Caminhos e funcionalidades")).toBeTruthy();
    expect(screen.getByText("Eventos e interações")).toBeTruthy();
    // Estado honesto: eventos sem fonte conectada = indisponível, não zero.
    expect(
      screen.getByText("Eventos operacionais indisponíveis nesta versão."),
    ).toBeTruthy();
    // Catálogo contém apenas a rota implementada.
    expect(screen.getAllByText("Início").length).toBeGreaterThan(0);
    expect(screen.queryByText("Minhas tarefas")).toBeNull();
    expect(screen.queryByText("Visão geral")).toBeNull();
  });

  it("403 do viewer-context exibe estado de acesso restrito", async () => {
    viewerState.loading = false;
    viewerState.errorStatus = 403;
    render(<HomePage basePath="/apps/controllership-finance" />);
    expect(screen.getByText("Acesso restrito")).toBeTruthy();
    expect(screen.queryByText("Caminhos e funcionalidades")).toBeNull();
  });

  it("falha da BFF mantém o launcher utilizável (degradação independente)", async () => {
    viewerState.loading = false;
    viewerState.errorStatus = 503;
    render(<HomePage basePath="/apps/controllership-finance" />);
    await waitFor(() =>
      expect(screen.getByText("Contexto indisponível")).toBeTruthy(),
    );
    // Launcher continua montado.
    expect(screen.getByText("Caminhos e funcionalidades")).toBeTruthy();
    expect(screen.getAllByText("Início").length).toBeGreaterThan(0);
  });

  it("busca ?q= filtra o catálogo", async () => {
    setViewer("Ana", { access: true, manage: false, accessDre: false });
    window.history.replaceState(
      null,
      "",
      "/apps/controllership-finance?q=inicio",
    );
    render(<HomePage basePath="/apps/controllership-finance" />);
    const search = screen.getByLabelText(
      "Buscar caminhos e funcionalidades",
    ) as HTMLInputElement;
    expect(search.value).toBe("inicio");
    expect(screen.getAllByText("Início").length).toBeGreaterThan(0);
  });

  it("busca sem resultado mostra estado vazio honesto", async () => {
    setViewer("Ana", { access: true, manage: false, accessDre: false });
    window.history.replaceState(
      null,
      "",
      "/apps/controllership-finance?q=zzz-nada",
    );
    render(<HomePage basePath="/apps/controllership-finance" />);
    await waitFor(() =>
      expect(screen.getByText("Nenhum caminho encontrado")).toBeTruthy(),
    );
  });

  it("usuário somente-DRE vê somente Fechamento Mensal (RW03)", async () => {
    setViewer("Bruno", { access: false, manage: false, accessDre: true });
    render(
      <HomePage basePath="/apps/controllership-finance" homeView="dre_home" />,
    );
    expect(screen.getByText("Caminhos e funcionalidades")).toBeTruthy();
    // Único módulo autorizado: Central de Fechamento → Fechamento Mensal.
    expect(screen.getByText("Central de Fechamento")).toBeTruthy();
    expect(screen.getByText("Fechamento Mensal")).toBeTruthy();
    // Nenhuma superfície interna aparece para o público externo.
    expect(screen.queryByText("Relatórios e divergências")).toBeNull();
    expect(screen.queryByText("Administração do checklist")).toBeNull();
    expect(screen.queryByText("Documentos do fechamento")).toBeNull();
    expect(screen.queryByText("Catálogos governados")).toBeNull();
    expect(screen.queryByText("Meu perfil")).toBeNull();
    expect(screen.queryByText("Portal")).toBeNull();
  });

  it("usuário interno não vê a seção DRE duplicada", async () => {
    setViewer("Ana", { access: true, manage: false, accessDre: false });
    render(<HomePage basePath="/apps/controllership-finance" />);
    expect(screen.getByText("Fechamento mensal")).toBeTruthy();
    // «Fechamento Mensal» (rótulo da rota DRE) não aparece para o interno.
    expect(screen.queryByText("Fechamento Mensal")).toBeNull();
  });

  it("últimos acessos registra a visita à home", async () => {
    setViewer("Ana", { access: true, manage: false, accessDre: false });
    render(<HomePage basePath="/apps/controllership-finance" />);
    await waitFor(() =>
      expect(screen.getByText("Últimos acessos")).toBeTruthy(),
    );
  });
});
