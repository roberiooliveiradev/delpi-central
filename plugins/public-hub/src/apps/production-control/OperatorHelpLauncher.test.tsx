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
import { OperatorHelpLauncher } from "./OperatorHelpLauncher.tsx";
import { PROCESS_ISSUE_REASONS } from "./processIssue.ts";

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

const ACTIVE_FEEDBACK = {
  id: "fb-1",
  productionOrder: "24640401002",
  operationCode: "03",
  reportedWorkCenter: "CT-63",
  feedbackType: "cannot_produce",
  reasonCode: "missing_material",
  note: "Falta parafuso",
  status: "open",
  createdAt: "2026-10-09T10:00:00Z",
  acknowledgedAt: null,
  resolvedAt: null,
  materials: [
    {
      productCode: "100001",
      description: "MATERIAL A",
      unit: "PC",
      status: "pending",
    },
  ],
};

const MATERIALS = {
  branch: "02",
  production_order: "24640401002",
  operation_code: "03",
  items: [
    {
      product_code: "100001",
      description: "MATERIAL A",
      unit: "PC",
      original_qty: 10,
      open_qty: 5,
      consumed_qty: 5,
      commitment_count: 0,
    },
    {
      product_code: "100002",
      description: "MATERIAL B",
      unit: "PC",
      original_qty: 8,
      open_qty: 0,
      consumed_qty: 8,
      commitment_count: 0,
    },
  ],
  summary: { material_count: 2, commitment_count: 0 },
};

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
    identifyOpen: false,
    ...overrides,
  };
}

function stubFetch(handler: (url: string, init?: RequestInit) => Response) {
  const calls: { url: string; init?: RequestInit }[] = [];
  vi.stubGlobal(
    "fetch",
    async (url: string | URL | Request, init?: RequestInit) => {
      calls.push({ url: String(url), init });
      return handler(String(url), init);
    },
  );
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
      <OperatorHelpLauncher
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

async function openSheet() {
  const launcher = screen.getByRole("button", { name: /Pedir ajuda/ });
  fireEvent.click(launcher);
  return launcher;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("OperatorHelpLauncher — launcher", () => {
  it("renders only the compact launcher, no permanent request cards", () => {
    stubFetch(() => okEnvelope({ items: [] }));
    setup(sessionCtx("identified"));
    expect(
      screen.getByRole("button", { name: /Pedir ajuda/ }),
    ).toBeInTheDocument();
    // área fixa antiga e destinos não ocupam a página
    expect(screen.queryByText("Solicitações do operador")).toBeNull();
    expect(screen.queryByText("Produção / PCP")).toBeNull();
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("opens a single dialog surface and closes back to the launcher", async () => {
    stubFetch(() => okEnvelope({ items: [] }));
    setup(sessionCtx("identified"));
    const launcher = await openSheet();
    const dialogs = screen.getAllByRole("dialog");
    expect(dialogs).toHaveLength(1);
    fireEvent.click(screen.getByRole("button", { name: "Fechar janela" }));
    expect(screen.queryByRole("dialog")).toBeNull();
    await waitFor(() => expect(launcher).toHaveFocus());
  });

  it("Escape closes the sheet when idle", async () => {
    stubFetch(() => okEnvelope({ items: [] }));
    setup(sessionCtx("identified"));
    await openSheet();
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    fireEvent.keyDown(window, { key: "Escape" });
    expect(screen.queryByRole("dialog")).toBeNull();
  });
});

describe("OperatorHelpLauncher — sessão", () => {
  it("anonymous shows a single identify CTA inside the sheet", async () => {
    stubFetch(() => okEnvelope({ items: [] }));
    const openIdentify = vi.fn();
    setup(sessionCtx("anonymous", { openIdentify }));
    await openSheet();
    expect(
      screen.getByText("Identifique-se para enviar uma solicitação."),
    ).toBeInTheDocument();
    const ctas = screen.getAllByRole("button", {
      name: "Identificar operador",
    });
    expect(ctas).toHaveLength(1);
    expect(screen.queryByText("Produção / PCP")).toBeNull();
    fireEvent.click(ctas[0]);
    expect(openIdentify).toHaveBeenCalledTimes(1);
  });

  it("restoring shows the checking message inside the sheet", async () => {
    stubFetch(() => okEnvelope({ items: [] }));
    setup(sessionCtx("restoring"));
    await openSheet();
    expect(
      screen.getByText("Verificando identificação do operador…"),
    ).toBeInTheDocument();
  });
});

describe("OperatorHelpLauncher — destinos", () => {
  it("offers PCP and Processos destinations", async () => {
    stubFetch(() => okEnvelope({ items: [] }));
    setup(sessionCtx("identified"));
    await openSheet();
    expect(screen.getByText("Produção / PCP")).toBeInTheDocument();
    expect(screen.getByText("Processos")).toBeInTheDocument();
    expect(
      screen.getByText("O que você precisa comunicar?"),
    ).toBeInTheDocument();
  });

  it("Voltar returns to destination selection", async () => {
    stubFetch(() => okEnvelope({ items: [] }));
    setup(sessionCtx("identified"));
    await openSheet();
    fireEvent.click(screen.getByText("Processos"));
    expect(
      screen.getByText("Qual problema você encontrou?"),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Voltar" }));
    expect(screen.getByText("Produção / PCP")).toBeInTheDocument();
  });
});

describe("OperatorHelpLauncher — fluxo Processos", () => {
  it("lists the six reasons as compact rows and advances on pick", async () => {
    stubFetch(() => okEnvelope({ items: [] }));
    setup(sessionCtx("identified"));
    await openSheet();
    fireEvent.click(screen.getByText("Processos"));
    for (const item of PROCESS_ISSUE_REASONS) {
      expect(screen.getByText(item.label)).toBeInTheDocument();
    }
    fireEvent.click(
      screen.getByText("Ferramenta não informada ou não vinculada"),
    );
    expect(
      screen.getByLabelText(/Código da ferramenta \(opcional\)/),
    ).toBeInTheDocument();
  });

  it("shows material field only for material_not_linked", async () => {
    stubFetch(() => okEnvelope({ items: [] }));
    setup(sessionCtx("identified"));
    await openSheet();
    fireEvent.click(screen.getByText("Processos"));
    fireEvent.click(
      screen.getByText("Matéria-prima não vinculada à operação"),
    );
    expect(
      screen.getByLabelText(/Código do material \(opcional\)/),
    ).toBeInTheDocument();
    expect(screen.queryByLabelText(/Código da ferramenta/)).toBeNull();
  });

  it("Voltar preserves the Processos draft while the sheet is open", async () => {
    stubFetch(() => okEnvelope({ items: [] }));
    setup(sessionCtx("identified"));
    await openSheet();
    fireEvent.click(screen.getByText("Processos"));
    fireEvent.click(
      screen.getByText("Ferramenta não informada ou não vinculada"),
    );
    fireEvent.change(screen.getByLabelText(/Código da ferramenta/), {
      target: { value: "F12345" },
    });
    fireEvent.change(screen.getByLabelText(/Observação/), {
      target: { value: "rascunho do operador" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Voltar" }));
    // volta aos motivos e avança de novo — o rascunho continua
    fireEvent.click(
      screen.getByText("Ferramenta não informada ou não vinculada"),
    );
    expect(screen.getByLabelText(/Código da ferramenta/)).toHaveValue(
      "F12345",
    );
    expect(screen.getByLabelText(/Observação/)).toHaveValue(
      "rascunho do operador",
    );
  });

  it("submits only the public contract and confirms the request number", async () => {
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
    await openSheet();
    fireEvent.click(screen.getByText("Processos"));
    fireEvent.click(
      screen.getByText("Ferramenta não informada ou não vinculada"),
    );
    fireEvent.change(screen.getByLabelText(/Código da ferramenta/), {
      target: { value: "F12345" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Enviar para Processos" }),
    );

    expect(
      await screen.findByText(
        "Solicitação REQ-2026-000123 enviada para Processos.",
      ),
    ).toBeInTheDocument();
    // mesma superfície — nunca modal sobre modal
    expect(screen.getAllByRole("dialog")).toHaveLength(1);

    const post = calls.find((c) => c.url.includes("/process-issues"));
    const headers = post!.init?.headers as Record<string, string>;
    expect(headers["X-Delpi-Bench-Session"]).toBe("sess-1");
    expect(String(headers["Idempotency-Key"] ?? "").length).toBeGreaterThan(0);
    const body = JSON.parse(String(post!.init?.body));
    expect(body.issueCode).toBe("tool_not_linked");
    expect(body.toolCode).toBe("F12345");
    expect(body.branch).toBeUndefined();
    expect(body.workCenter).toBeUndefined();

    fireEvent.click(screen.getByRole("button", { name: "Concluir" }));
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("error keeps the sheet open with the draft", async () => {
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
    await openSheet();
    fireEvent.click(screen.getByText("Processos"));
    fireEvent.click(screen.getByText("Outro problema de processo"));
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
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByLabelText(/Observação/)).toHaveValue(
      "detalhe do operador",
    );
  });

  it("retry reuses the same Idempotency-Key for the same payload", async () => {
    const calls = stubFetch((url) => {
      if (url.includes("/process-issues")) {
        return new Response(
          JSON.stringify({ success: false, message: "down" }),
          { status: 503, headers: { "Content-Type": "application/json" } },
        );
      }
      return okEnvelope({ items: [] });
    });
    setup(sessionCtx("identified"));
    await openSheet();
    fireEvent.click(screen.getByText("Processos"));
    fireEvent.click(screen.getByText("Outro problema de processo"));
    const send = () =>
      fireEvent.click(
        screen.getByRole("button", { name: "Enviar para Processos" }),
      );
    send();
    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
    send();
    await waitFor(() => {
      const posts = calls.filter((c) => c.url.includes("/process-issues"));
      expect(posts).toHaveLength(2);
      const keyOf = (c: { init?: RequestInit }) =>
        (c.init?.headers as Record<string, string>)["Idempotency-Key"];
      expect(keyOf(posts[0])).toBe(keyOf(posts[1]));
    });
  });

  it("cancel discards the attempt and closes without sending", async () => {
    const calls = stubFetch(() => okEnvelope({ items: [] }));
    setup(sessionCtx("identified"));
    await openSheet();
    fireEvent.click(screen.getByText("Processos"));
    fireEvent.click(screen.getByText("Outro problema de processo"));
    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(
      calls.find((c) => c.url.includes("/process-issues")),
    ).toBeUndefined();
  });
});

describe("OperatorHelpLauncher — fluxo PCP", () => {
  it("runs materials + note + submit inside the same surface", async () => {
    const calls = stubFetch((url, init) => {
      if (url.includes("/operations/materials")) {
        return okEnvelope(MATERIALS);
      }
      if (url.includes("/operator-feedbacks") && init?.method === "POST") {
        return okEnvelope(ACTIVE_FEEDBACK, 201);
      }
      return okEnvelope({ items: [] });
    });
    setup(sessionCtx("identified"));
    await openSheet();
    fireEvent.click(screen.getByText("Produção / PCP"));
    // materiais só carregam dentro do fluxo
    const checkbox = await screen.findByRole("checkbox", {
      name: /100001/,
    });
    fireEvent.click(checkbox);
    fireEvent.change(screen.getByLabelText(/Observação/), {
      target: { value: "Faltou o parafuso" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Enviar aviso ao PCP" }),
    );
    expect(
      await screen.findByText("PCP informado"),
    ).toBeInTheDocument();
    expect(screen.getAllByRole("dialog")).toHaveLength(1);

    const post = calls.find(
      (c) => c.url.includes("/operator-feedbacks") && c.init?.method === "POST",
    );
    const body = JSON.parse(String(post!.init?.body));
    expect(body.feedbackType).toBe("cannot_produce");
    expect(body.reasonCode).toBe("missing_material");
    expect(body.materialCodes).toEqual(["100001"]);
    expect(body.note).toBe("Faltou o parafuso");
  });

  it("requires at least one material before sending", async () => {
    stubFetch((url) => {
      if (url.includes("/operations/materials")) {
        return okEnvelope(MATERIALS);
      }
      return okEnvelope({ items: [] });
    });
    setup(sessionCtx("identified"));
    await openSheet();
    fireEvent.click(screen.getByText("Produção / PCP"));
    await screen.findByRole("checkbox", { name: /100001/ });
    fireEvent.click(
      screen.getByRole("button", { name: "Enviar aviso ao PCP" }),
    );
    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Selecione pelo menos um material",
      ),
    );
  });

  it("shows the compact badge on the launcher and Em andamento in the sheet", async () => {
    stubFetch((url) => {
      if (url.includes("/operator-feedbacks/active")) {
        return okEnvelope({ items: [ACTIVE_FEEDBACK] });
      }
      return okEnvelope({ items: [] });
    });
    setup(sessionCtx("identified"));
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: /Pedir ajuda — PCP informado/ }),
      ).toBeInTheDocument(),
    );
    await openSheet();
    expect(screen.getByText("Em andamento")).toBeInTheDocument();
    expect(screen.getByText("Falta de matéria-prima")).toBeInTheDocument();
    expect(screen.getByText("PCP informado")).toBeInTheDocument();
    expect(screen.getByText("Aguardando separação")).toBeInTheDocument();
  });
});
