import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@delpi/plugin-ui/index", async () => await import("../test/pluginUiMock"));

import { CfFeedbackMessage, CfQueryErrorBanner } from "./cfFeedbackUi";

afterEach(() => {
  cleanup();
});

describe("CfFeedbackMessage", () => {
  it("renderiza título e descrição com role=status do componente do kit", () => {
    render(
      <CfFeedbackMessage intent="info" title="Título informativo">
        Descrição contextual.
      </CfFeedbackMessage>,
    );
    expect(screen.getByText("Título informativo")).toBeTruthy();
    expect(screen.getByText("Descrição contextual.")).toBeTruthy();
    expect(screen.getAllByRole("status").length).toBeGreaterThan(0);
  });

  it("renderiza ação contextual opcional", () => {
    render(
      <CfFeedbackMessage
        intent="error"
        title="Falha"
        action={<button type="button">Tentar novamente</button>}
      />,
    );
    expect(
      screen.getByRole("button", { name: "Tentar novamente" }),
    ).toBeTruthy();
  });
});

describe("CfQueryErrorBanner — catálogo de falhas", () => {
  it("scope_unavailable — gate de dataset (não RBAC, não vazio)", () => {
    render(
      <CfQueryErrorBanner
        error={{ status: 403, code: "scope_unavailable", message: "x" }}
        dataset="o estoque histórico"
      />,
    );
    expect(screen.getByText("Consulta ainda não habilitada")).toBeTruthy();
    expect(screen.queryByText("Acesso restrito")).toBeNull();
  });

  it("S2S_* — credencial técnica pendente", () => {
    render(
      <CfQueryErrorBanner
        error={{ status: 403, code: "S2S_SCOPE_DENIED", message: "x" }}
        dataset="o estoque histórico"
      />,
    );
    expect(screen.getByText("Integração de dados pendente")).toBeTruthy();
    expect(screen.queryByText("Acesso restrito")).toBeNull();
  });

  it("401 — sessão expirada", () => {
    render(
      <CfQueryErrorBanner
        error={{ status: 401, code: null, message: "x" }}
        dataset="as baixas financeiras"
      />,
    );
    expect(screen.getByText("Sessão expirada")).toBeTruthy();
  });

  it("403 — acesso restrito com o dataset no texto", () => {
    render(
      <CfQueryErrorBanner
        error={{ status: 403, code: null, message: "x" }}
        dataset="as baixas financeiras"
      />,
    );
    expect(screen.getByText("Acesso restrito")).toBeTruthy();
    expect(
      screen.getByText(/autorização para consultar as baixas financeiras/),
    ).toBeTruthy();
  });

  it("503 — origem indisponível com Tentar novamente", () => {
    const onRetry = vi.fn();
    render(
      <CfQueryErrorBanner
        error={{ status: 503, code: null, message: "x" }}
        dataset="o estoque histórico"
        onRetry={onRetry}
      />,
    );
    expect(screen.getByText("Origem indisponível")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("404 — não encontrado com a mensagem real", () => {
    render(
      <CfQueryErrorBanner
        error={{ status: 404, code: null, message: "Recurso ausente" }}
        dataset="o estoque histórico"
      />,
    );
    expect(screen.getByText("Não encontrado")).toBeTruthy();
    expect(screen.getByText("Recurso ausente")).toBeTruthy();
    expect(screen.queryByText("Falha de comunicação")).toBeNull();
  });

  it("409 — regra de negócio não é falha de comunicação", () => {
    render(
      <CfQueryErrorBanner
        error={{
          status: 409,
          code: "no_published_template",
          message: "Não há versão publicada vigente para a competência.",
        }}
        dataset="o checklist"
      />,
    );
    expect(screen.getByText("Operação não permitida")).toBeTruthy();
    expect(
      screen.getByText("Não há versão publicada vigente para a competência."),
    ).toBeTruthy();
    expect(screen.queryByText("Falha de comunicação")).toBeNull();
  });

  it("erro genérico — mensagem real exposta com retry", () => {
    render(
      <CfQueryErrorBanner
        error={{ status: 0, code: null, message: "Falha de rede X" }}
        dataset="as baixas financeiras"
        onRetry={() => {}}
      />,
    );
    expect(screen.getByText("Falha de comunicação")).toBeTruthy();
    expect(screen.getByText("Falha de rede X")).toBeTruthy();
  });
});
