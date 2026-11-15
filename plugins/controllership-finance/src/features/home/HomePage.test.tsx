import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

const viewerState = {
  viewer: null as {
    firstName: string | null;
    capabilities: {
      access: boolean;
      manage: boolean;
      accessDre: boolean;
      lnfAccess: boolean;
    };
  } | null,
  loading: true,
  errorStatus: null as number | null,
  reload: vi.fn(),
};

vi.mock("../../app/ViewerContext", () => ({
  useViewerContext: () => viewerState,
}));

vi.mock("../../app/homeFavoritesStore", () => ({
  subscribeHomeFavorites: () => () => undefined,
  refreshHomeFavorites: async () => [],
  replaceHomeFavorites: async (items: unknown) => items,
  setHomeFavoritesLocal: () => undefined,
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
  capabilities: {
    access: boolean;
    manage: boolean;
    accessDre: boolean;
    lnfAccess: boolean;
  },
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
    setViewer("Ana", { access: true, manage: false, accessDre: false, lnfAccess: false });
    render(<HomePage basePath="/apps/controllership-finance" />);
    expect(screen.getByText("Caminhos e funcionalidades")).toBeTruthy();
    expect(screen.getByText("Eventos e interações")).toBeTruthy();
    // Estado honesto: eventos sem fonte conectada = indisponível, não zero.
    expect(
      screen.getByText("Eventos operacionais indisponíveis nesta versão."),
    ).toBeTruthy();
    expect(screen.getByText("Central de Fechamento")).toBeTruthy();
    expect(screen.getByText("Notas fiscais")).toBeTruthy();
    expect(screen.getByText("Auditoria de Entradas")).toBeTruthy();
    expect(screen.queryByText("Portal")).toBeNull();
    expect(screen.queryByText("Meu perfil")).toBeNull();
    expect(screen.queryByText("Lançamento de notas fiscais")).toBeNull();
    expect(screen.queryByText("Administração")).toBeNull();
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
    // Launcher continua montado (access default enquanto viewer null).
    expect(screen.getByText("Caminhos e funcionalidades")).toBeTruthy();
    expect(screen.getByText("Central de Fechamento")).toBeTruthy();
  });

  it("busca ?q= filtra o catálogo", async () => {
    setViewer("Ana", { access: true, manage: false, accessDre: false, lnfAccess: false });
    window.history.replaceState(
      null,
      "",
      "/apps/controllership-finance?q=fechamento",
    );
    render(<HomePage basePath="/apps/controllership-finance" />);
    const search = screen.getByLabelText(
      "Buscar caminhos e funcionalidades",
    ) as HTMLInputElement;
    expect(search.value).toBe("fechamento");
    expect(screen.getByText("Fechamento mensal")).toBeTruthy();
  });

  it("com lnfAccess exibe o link do app LNF no card Notas fiscais", async () => {
    setViewer("Ana", { access: true, manage: false, accessDre: false, lnfAccess: true });
    render(<HomePage basePath="/apps/controllership-finance" />);
    expect(screen.getByText("Lançamento de notas fiscais")).toBeTruthy();
  });

  it("com manage exibe o card Administração", async () => {
    setViewer("Ana", { access: true, manage: true, accessDre: false, lnfAccess: false });
    render(<HomePage basePath="/apps/controllership-finance" />);
    expect(screen.getByText("Administração")).toBeTruthy();
    expect(screen.getByText("Administração do checklist")).toBeTruthy();
  });

  it("busca sem resultado mostra estado vazio honesto", async () => {
    setViewer("Ana", { access: true, manage: false, accessDre: false, lnfAccess: false });
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

  it("usuário somente-DRE vê a MESMA Home com somente Fechamento Mensal (RW04)", async () => {
    setViewer("Bruno", {
      access: false,
      manage: false,
      accessDre: true,
      lnfAccess: false,
    });
    render(<HomePage basePath="/apps/controllership-finance" />);
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
    setViewer("Ana", { access: true, manage: false, accessDre: false, lnfAccess: false });
    render(<HomePage basePath="/apps/controllership-finance" />);
    expect(screen.getByText("Fechamento mensal")).toBeTruthy();
    // «Fechamento Mensal» (rótulo da rota DRE) não aparece para o interno.
    expect(screen.queryByText("Fechamento Mensal")).toBeNull();
  });

  it("não lista Início nos caminhos do hub (D7)", async () => {
    setViewer("Ana", { access: true, manage: false, accessDre: false, lnfAccess: false });
    render(<HomePage basePath="/apps/controllership-finance" />);
    expect(screen.getByText("Fechamento mensal")).toBeTruthy();
    expect(screen.queryByText("Início")).toBeNull();
  });
});
