/** @vitest-environment jsdom */
import "@testing-library/jest-dom/vitest";
import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { BenchSessionSnapshot, MachineLoadOperation } from "./api.ts";
import { OperatorSessionContext } from "./OperatorSessionContext.ts";
import type { OperatorSessionContextValue } from "./OperatorSessionContext.ts";
import { OperatorRequestsPanel } from "./OperatorRequestsPanel.tsx";

const OPERATION = {
  work_center: "CT-63",
  work_center_name: "Montagem 03",
  scheduled_date: "2026-10-09",
  scheduled_start_time: "07:30",
  scheduled_end_date: "2026-10-09",
  scheduled_end_time: "17:30",
  production_order: "24640401002",
  operation_code: "03",
  operation_description: "MONTAGEM",
  tool: "F99999",
  resource: null,
  product_code: "10045678",
  product_description: "Componente X",
  unit: "PC",
  planned_qty: 100,
  produced_qty: 50,
  pending_qty: 50,
  pa_product_code: "90264238",
  pa_product_description: "Produto acabado",
  pa_due_date: "2026-10-15",
  due_date: "2026-10-15",
  production_status: "not_started",
  is_in_production: false,
  production_started_date: null,
  production_started_time: null,
  active_operator_name: null,
  active_operator_count: null,
  appointment_count: null,
  last_appointment_date: null,
} satisfies MachineLoadOperation;

function sessionCtx(
  status: "restoring" | "anonymous" | "identified",
  overrides: Partial<OperatorSessionContextValue> = {},
): OperatorSessionContextValue {
  const session: BenchSessionSnapshot | null =
    status === "identified"
      ? {
          sessionToken: "sess-1",
          expiresAt: null,
          branch: "02",
          workCenter: "CT-63",
          operatorCode: "001234",
          operatorName: "Maria Silva",
        }
      : null;
  return {
    session,
    status,
    identify: vi.fn(),
    logout: vi.fn(),
    invalidate: vi.fn(),
    openIdentify: vi.fn(),
    ...overrides,
  };
}

function stubFetch(handler: (url: string, init?: RequestInit) => Response) {
  const calls: { url: string; init?: RequestInit }[] = [];
  vi.stubGlobal("fetch", async (url: string | URL | Request, init?: RequestInit) => {
    calls.push({ url: String(url), init });
    return handler(String(url), init);
  });
  return calls;
}

const okEnvelope = (data: unknown, status = 200) =>
  new Response(JSON.stringify({ success: true, data }), {
    status,
    headers: { "Content-Type": "application/json" },
  });

function setup(ctx: OperatorSessionContextValue) {
  return render(
    <OperatorSessionContext.Provider value={ctx}>
      <OperatorRequestsPanel
        token="tok"
        branch="02"
        operation={OPERATION}
        workCenter="CT-63"
        realtimeConnected
        resyncSignal={0}
        feedbackRealtimeEvent={null}
      />
    </OperatorSessionContext.Provider>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("OperatorRequestsPanel", () => {
  it("anonymous shows a single identify CTA and no destinations", () => {
    const openIdentify = vi.fn();
    setup(sessionCtx("anonymous", { openIdentify }));
    expect(
      screen.getByText("Solicitações do operador"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Identifique-se para enviar solicitações desta operação.",
      ),
    ).toBeInTheDocument();
    const ctas = screen.getAllByRole("button", { name: "Identificar operador" });
    expect(ctas).toHaveLength(1);
    fireEvent.click(ctas[0]);
    expect(openIdentify).toHaveBeenCalledTimes(1);
    // nenhum destino visível sem sessão
    expect(screen.queryByText("Produção / PCP")).toBeNull();
    expect(screen.queryByText("Processos")).toBeNull();
  });

  it("restoring shows the checking message", () => {
    setup(sessionCtx("restoring"));
    expect(
      screen.getByText("Verificando identificação do operador…"),
    ).toBeInTheDocument();
  });

  it("identified shows both destinations", async () => {
    stubFetch(() => okEnvelope({ items: [] }));
    setup(sessionCtx("identified"));
    expect(screen.getByText("Produção / PCP")).toBeInTheDocument();
    expect(screen.getByText("Processos")).toBeInTheDocument();
    // fluxo PCP embedded: CTA aparece após o GET de ativos resolver
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Informar ao PCP" }),
      ).toBeInTheDocument(),
    );
    expect(
      screen.getByRole("button", { name: "Informar Processos" }),
    ).toBeInTheDocument();
  });

  it("Informar Processos opens the dedicated modal", async () => {
    stubFetch(() => okEnvelope({ items: [] }));
    setup(sessionCtx("identified"));
    fireEvent.click(
      await screen.findByRole("button", { name: "Informar Processos" }),
    );
    expect(
      await screen.findByRole("heading", {
        name: "Informar problema de processo",
      }),
    ).toBeInTheDocument();
    // abrir o modal NÃO dispara consultas de materiais/desenho/etc.
    const urls = (
      globalThis.fetch as unknown as ReturnType<typeof vi.fn>
    ).mock?.calls?.map((c: unknown[]) => String(c[0])) ?? [];
    for (const url of urls) {
      expect(url).not.toContain("materials");
      expect(url).not.toContain("drawings");
    }
  });

  it("submitting sends only the public contract and confirms the number", async () => {
    const calls = stubFetch((url) => {
      if (url.includes("/process-issues")) {
        return okEnvelope(
          {
            requestId: "req-9",
            requestNumber: "REQ-2026-000123",
            status: "submitted",
            message: "ok",
          },
          201,
        );
      }
      return okEnvelope({ items: [] });
    });
    setup(sessionCtx("identified"));

    fireEvent.click(
      await screen.findByRole("button", { name: "Informar Processos" }),
    );
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Ferramenta não informada ou não vinculada",
      }),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Enviar para Processos" }),
    );

    const confirmation = await screen.findByText(
      "Solicitação REQ-2026-000123 enviada para Processos.",
    );
    expect(confirmation).toHaveAttribute("role", "status");
    // modal fechou
    expect(screen.queryByRole("dialog")).toBeNull();

    const post = calls.find((c) => c.url.includes("/process-issues"));
    expect(post).toBeTruthy();
    const headers = post!.init?.headers as Record<string, string>;
    expect(headers["X-Delpi-Bench-Session"]).toBe("sess-1");
    expect(String(headers["Idempotency-Key"] ?? "").length).toBeGreaterThan(0);
    const body = JSON.parse(String(post!.init?.body));
    expect(body.issueCode).toBe("tool_not_linked");
    expect(body.branch).toBeUndefined();
    expect(body.workCenter).toBeUndefined();
  });

  it("error keeps the modal open with the draft", async () => {
    stubFetch((url) => {
      if (url.includes("/process-issues")) {
        return new Response(
          JSON.stringify({ success: false, message: "down" }),
          { status: 503, headers: { "Content-Type": "application/json" } },
        );
      }
      return okEnvelope({ items: [] });
    });
    setup(sessionCtx("identified"));
    fireEvent.click(
      await screen.findByRole("button", { name: "Informar Processos" }),
    );
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Outro problema de processo",
      }),
    );
    fireEvent.change(screen.getByLabelText(/Observação/), {
      target: { value: "detalhe do operador" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Enviar para Processos" }),
    );
    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Não foi possível enviar a solicitação para Processos",
      ),
    );
    // modal segue aberto; rascunho preservado
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByLabelText(/Observação/)).toHaveValue(
      "detalhe do operador",
    );
    expect(
      screen.getByRole("button", { name: "Outro problema de processo" }),
    ).toHaveAttribute("aria-pressed", "true");
  });

  it("cancel discards the attempt and closes without sending", async () => {
    const calls = stubFetch(() => okEnvelope({ items: [] }));
    setup(sessionCtx("identified"));
    fireEvent.click(
      await screen.findByRole("button", { name: "Informar Processos" }),
    );
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Outro problema de processo",
      }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(calls.find((c) => c.url.includes("/process-issues"))).toBeUndefined();
  });
});
