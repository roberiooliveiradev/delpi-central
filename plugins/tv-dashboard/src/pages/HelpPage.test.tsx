// @vitest-environment happy-dom
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { HttpRequestError } from "../api/httpClient";
import { HELP_AUTH_NOTE, HELP_LOADING_NOTE, HELP_UNAVAILABLE_NOTE } from "../content/helpGuideContent";
import { HelpPage } from "./HelpPage";

const { fetchProductGuideHelp } = vi.hoisted(() => ({
  fetchProductGuideHelp: vi.fn(),
}));

vi.mock("../api/tvDashboardApi", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/tvDashboardApi")>();
  return { ...actual, fetchProductGuideHelp };
});

const TOPICS = [
  { id: "tv_dashboard_overview", title: "Visão geral", summary: "Guia do produto." },
  ...[
    "playlist",
    "slide",
    "block_types",
    "data_sources",
    "data_models",
    "data_bindings",
    "filters_and_layering",
    "display_formats",
    "data_route_discovery",
    "visual_verification",
  ].map((id) => ({ id, title: id, summary: `Semântica ${id}.` })),
];

function props() {
  return { onNavigate: vi.fn(), onBack: vi.fn() };
}

afterEach(() => {
  cleanup();
  fetchProductGuideHelp.mockReset();
});

describe("HelpPage", () => {
  it("mostra loading explícito enquanto carrega", async () => {
    fetchProductGuideHelp.mockReturnValue(new Promise(() => {}));
    render(<HelpPage {...props()} />);
    expect((await screen.findAllByText(HELP_LOADING_NOTE)).length).toBeGreaterThan(0);
    // links locais visíveis já no loading
    expect(screen.getAllByText("Visão geral").length).toBeGreaterThan(0);
  });

  it("renderiza semântica do Product Guide + navegação local", async () => {
    fetchProductGuideHelp.mockResolvedValue({
      schema: "product_guide_help_v1",
      registry_version: "1.0.0",
      topics: TOPICS,
    });
    render(<HelpPage {...props()} />);
    expect((await screen.findAllByText("Guia do produto.")).length).toBeGreaterThan(0);
    expect(await screen.findByText("Semântica playlist.")).toBeTruthy();
    // navegação local permanece (GuideTable)
    expect(screen.getAllByText("Quero…").length).toBeGreaterThan(0);
    expect(screen.getByText("Card «Nova programação»")).toBeTruthy();
  });

  it("5xx/rede: nota de indisponibilidade explícita + retry, links locais intactos", async () => {
    fetchProductGuideHelp.mockRejectedValue(new HttpRequestError("Erro HTTP 503", 503));
    render(<HelpPage {...props()} />);
    expect((await screen.findAllByText(HELP_UNAVAILABLE_NOTE)).length).toBeGreaterThan(0);
    expect(screen.getByText("Tentar novamente")).toBeTruthy();
    expect(screen.getByText("Card «Nova programação»")).toBeTruthy();
  });

  it("401/403: nota de autenticação, não finge conteúdo", async () => {
    fetchProductGuideHelp.mockRejectedValue(
      new HttpRequestError("Não autorizado.", 401),
    );
    render(<HelpPage {...props()} />);
    expect((await screen.findAllByText(HELP_AUTH_NOTE)).length).toBeGreaterThan(0);
  });

  it("404: nota de configuração/drift", async () => {
    fetchProductGuideHelp.mockRejectedValue(new HttpRequestError("Not found", 404));
    render(<HelpPage {...props()} />);
    const notes = await screen.findAllByText(/configuração de ajuda não encontrada/i);
    expect(notes.length).toBeGreaterThan(0);
  });

  it("índice vazio = falha de configuração, não sucesso", async () => {
    fetchProductGuideHelp.mockResolvedValue({
      schema: "product_guide_help_v1",
      topics: [],
    });
    render(<HelpPage {...props()} />);
    const notes = await screen.findAllByText(/configuração de ajuda não encontrada/i);
    expect(notes.length).toBeGreaterThan(0);
  });
});
