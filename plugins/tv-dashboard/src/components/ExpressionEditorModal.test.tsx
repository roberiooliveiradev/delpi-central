// @vitest-environment happy-dom
import { Component, type ReactNode } from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { ParamExpressionSupport } from "../hooks/useParamExpressionCapability";
import {
  buildExpressionParamValue,
  type ParamExpressionSpec,
} from "../utils/paramExpressions";
import type { ExpressionEditRequest } from "./comunicadoEditorContextCore";
import { ExpressionEditorModal } from "./ExpressionEditorModal";

const SUPPORT: ParamExpressionSupport = {
  enabled: true,
  loading: false,
  functions: [
    {
      name: "Date.AddMonths",
      kind: "scalar",
      signature: "Date.AddMonths(value, months) as date",
      parameters: ["value", "months"],
    },
  ],
  registryVersion: "1",
};

const TODAY_EXPR = buildExpressionParamValue({
  kind: "identifier",
  value: "today",
});

class ProbeBoundary extends Component<
  { children: ReactNode },
  { error: string | null }
> {
  state = { error: null as string | null };
  static getDerivedStateFromError(error: unknown) {
    return { error: String((error as Error)?.stack ?? error) };
  }
  render() {
    return this.state.error ? (
      <div data-testid="boundary-error">{this.state.error}</div>
    ) : (
      this.props.children
    );
  }
}

function freshRequest(overrides: Partial<ExpressionEditRequest> = {}): ExpressionEditRequest {
  return {
    paramKey: "start_date",
    paramLabel: "Início",
    spec: TODAY_EXPR,
    apply: vi.fn(),
    ...overrides,
  };
}

afterEach(() => cleanup());

describe("ExpressionEditorModal", () => {
  it("draft local: «Cancelar» fecha sem chamar apply — expressão preservada", () => {
    const request = freshRequest();
    const onClose = vi.fn();
    // Host real do MFE — o resolver de portal escolhe o primeiro
    // `.dashboard-tv-dashboard` em ordem de DOM (sem ele, o próprio wrapper
    // do portal seria eleito host no re-render).
    render(
      <div className="dashboard-tv-dashboard">
        <ProbeBoundary>
          <ExpressionEditorModal
            open
            request={request}
            support={SUPPORT}
            onClose={onClose}
          />
        </ProbeBoundary>
      </div>,
    );
    // Edita o draft via template (troca o AST localmente).
    const template = screen
      .queryAllByRole("button")
      .find((el) => el.className.includes("catalog__chip"));
    if (template) fireEvent.click(template);
    const boundaryError = screen.queryByTestId("boundary-error");
    if (boundaryError) {
      console.log("BOUNDARY:", boundaryError.textContent?.slice(0, 1200));
    }
    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(onClose).toHaveBeenCalledTimes(1);
    expect(request.apply).not.toHaveBeenCalled();
  });

  it("«Aplicar expressão» grava o draft via request.apply — AST intacto", () => {
    const request = freshRequest();
    render(
      <div className="dashboard-tv-dashboard">
        <ExpressionEditorModal
          open
          request={request}
          support={SUPPORT}
          onClose={vi.fn()}
        />
      </div>,
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Aplicar expressão" }),
    );
    expect(request.apply).toHaveBeenCalledTimes(1);
    const applied = request.apply.mock.calls[0][0] as ParamExpressionSpec;
    expect(applied).toEqual(TODAY_EXPR);
    expect(applied.expression?.expression).toEqual({
      kind: "identifier",
      value: "today",
    });
  });

  it("«Pré-visualizar» envia o draft ao backend e exibe o resultado resolvido", async () => {
    const request = freshRequest();
    const onPreview = vi.fn().mockResolvedValue({
      paramExpressions: [
        { param: "start_date", resolved: "2024-08-15", expectedType: "date" },
      ],
      effectiveParams: {},
    });
    render(
      <div className="dashboard-tv-dashboard">
        <ExpressionEditorModal
          open
          request={request}
          support={SUPPORT}
          onPreview={onPreview}
          onClose={vi.fn()}
        />
      </div>,
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Pré-visualizar" }),
    );
    await waitFor(() => expect(onPreview).toHaveBeenCalledTimes(1));
    expect(onPreview.mock.calls[0][0]).toEqual(TODAY_EXPR);
    expect(
      await screen.findByText(/Resultado do backend: 2024-08-15/),
    ).toBeTruthy();
  });

  it("X e Escape fecham sem chamar apply", () => {
    const request = freshRequest();
    const onClose = vi.fn();
    render(
      <div className="dashboard-tv-dashboard">
        <ExpressionEditorModal open request={request} support={SUPPORT} onClose={onClose} />
      </div>,
    );
    fireEvent.click(screen.getByRole("button", { name: "Fechar editor de expressão" }));
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(2);
    expect(request.apply).not.toHaveBeenCalled();
  });

  it("workbench host-contained: dialog no root do MFE, sem drawer nem portal no body", () => {
    const request = freshRequest();
    const tree = (open: boolean) => (
      <div className="dashboard-tv-dashboard">
        <ExpressionEditorModal open={open} request={request} support={SUPPORT} onClose={vi.fn()} />
      </div>
    );
    // O editor já está montado quando o usuário abre a expressão.
    const { container, rerender } = render(tree(false));
    rerender(tree(true));
    const host = container.querySelector(".dashboard-tv-dashboard")!;
    const dialog = screen.getByRole("dialog", { name: "Expressão — Início" });
    expect(dialog.getAttribute("aria-modal")).toBe("true");
    expect(dialog.getAttribute("aria-describedby")).toBeTruthy();
    const portal = dialog.closest('[data-modal-contained="true"]');
    expect(portal).toBeTruthy();
    expect(portal!.parentElement).toBe(host);
    expect(dialog.classList.contains("delpi-ui-modal--host-fill")).toBe(true);
    expect(document.querySelector(".delpi-ui-drawer")).toBeNull();
    expect(
      Array.from(document.body.children).some((child) =>
        child.matches('[data-modal-contained="true"]'),
      ),
    ).toBe(false);
  });

  it("sem callback de preview o botão «Pré-visualizar» não aparece", () => {
    render(
      <div className="dashboard-tv-dashboard">
        <ExpressionEditorModal
          open
          request={freshRequest()}
          support={SUPPORT}
          onClose={vi.fn()}
        />
      </div>,
    );
    expect(
      screen.queryByRole("button", { name: "Pré-visualizar" }),
    ).toBeNull();
    expect(
      screen.getByRole("button", { name: "Aplicar expressão" }),
    ).toBeTruthy();
  });
});
