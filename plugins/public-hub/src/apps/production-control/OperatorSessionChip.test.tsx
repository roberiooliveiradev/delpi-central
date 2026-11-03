import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { BenchSessionSnapshot } from "./api.ts";
import {
  OperatorSessionContext,
  type OperatorSessionContextValue,
} from "./OperatorSessionContext.ts";
import { OperatorSessionChip } from "./OperatorSessionProvider.tsx";

const SESSION: BenchSessionSnapshot = {
  sessionToken: "sess-1",
  expiresAt: null,
  branch: "01",
  workCenter: "CT-01",
  operatorCode: "001234",
  operatorName: "Maria Silva",
};

function sessionCtx(
  overrides: Partial<OperatorSessionContextValue> = {},
): OperatorSessionContextValue {
  return {
    session: SESSION,
    status: "identified",
    identify: vi.fn(),
    logout: vi.fn().mockResolvedValue(undefined),
    invalidate: vi.fn(),
    openIdentify: vi.fn(),
    identifyOpen: false,
    ...overrides,
  };
}

function renderChip(ctx: OperatorSessionContextValue) {
  return render(
    <OperatorSessionContext.Provider value={ctx}>
      <OperatorSessionChip />
    </OperatorSessionContext.Provider>,
  );
}

describe("OperatorSessionChip — troca com OP em andamento", () => {
  it("positivo: troca encerra a sessão e pede a próxima matrícula", async () => {
    const logout = vi.fn().mockResolvedValue(undefined);
    const openIdentify = vi.fn();
    renderChip(sessionCtx({ logout, openIdentify }));

    fireEvent.click(screen.getByRole("button", { name: "Trocar operador" }));

    await waitFor(() => {
      expect(logout).toHaveBeenCalledTimes(1);
      expect(openIdentify).toHaveBeenCalledTimes(1);
    });
    expect(
      screen.queryByText(/produção em andamento/i),
    ).not.toBeInTheDocument();
  });

  it("irmão: sem sessão, Identificar abre o modal", () => {
    const openIdentify = vi.fn();
    renderChip(
      sessionCtx({
        session: null,
        status: "anonymous",
        openIdentify,
      }),
    );

    fireEvent.click(screen.getByRole("button", { name: "Identificar" }));
    expect(openIdentify).toHaveBeenCalledTimes(1);
  });

  it("negativo: não exibe bloqueio legado de produção em andamento", () => {
    renderChip(sessionCtx());
    expect(
      screen.queryByText(/Encerrar a produção antes de trocar/i),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText(/produção em andamento neste posto/i),
    ).not.toBeInTheDocument();
  });
});
