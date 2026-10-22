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
import { ProductionRunControls } from "./ProductionRunControls.tsx";
import {
  clearPendingHandoffIntent,
  pendingHandoffIntents,
} from "./runHandoff.ts";

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
  tool: "",
  resource: null,
  product_code: "10045678",
  product_description: "Componente X",
  unit: "PC",
  planned_qty: 100,
  produced_qty: 50,
  pending_qty: 50,
  pa_product_code: null,
  pa_product_description: null,
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

const RUN = {
  id: "run-a-1",
  branch: "02",
  workCenter: "CT-63",
  productionOrder: "24640401002",
  operationCode: "03",
  deviceId: "dev-1",
  operatorCode: "001234",
  operatorName: "Maria Silva",
  status: "running",
  startedAt: "2026-10-09T10:00:00Z",
  endedAt: null,
  piecesTotal: 40,
  plannedQty: 100,
  targetPieces: 100,
  remainingPieces: 60,
  progressPercent: 40,
  targetReached: false,
  overproductionPieces: null,
  countedPieces: 40,
  device: {
    deviceId: "dev-1",
    name: "Contador CT-63",
    counter: 1040,
    counterEpoch: 1,
    online: true,
    status: "ok",
    lastSeenAt: "2026-10-09T10:00:00Z",
    pollIntervalMs: 1000,
  },
};

const NEXT_OP = {
  productionOrder: "24640401003",
  operationCode: "05",
  operationDescription: "ROSCA",
  productCode: "10045679",
  productDescription: "Componente Y",
  pendingQty: 30,
  queuePosition: 2,
  queueSize: 4,
};

const HANDOFF_RESULT = {
  requestId: "req-1",
  replayed: false,
  transitionAt: "2026-10-09T10:05:00Z",
  boundary: { counter: 1040, counterEpoch: 1 },
  auditId: "audit-1",
  completedRun: { ...RUN, status: "completed", endedAt: "2026-10-09T10:05:00Z" },
  newRun: {
    ...RUN,
    id: "run-b-1",
    productionOrder: "24640401003",
    operationCode: "05",
    piecesTotal: 0,
    countedPieces: 0,
    status: "running",
  },
};

const TIMELINE = {
  runId: "run-a-1",
  branch: "02",
  workCenter: "CT-63",
  status: "running",
  referenceAt: "2026-10-09T10:00:00Z",
  summary: { elapsedSeconds: 300, producingSeconds: 300, stoppedSeconds: 0, stopCount: 0 },
  items: [],
};

const SESSION: BenchSessionSnapshot = {
  sessionToken: "sess-1",
  expiresAt: null,
  branch: "02",
  workCenter: "CT-63",
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
    logout: vi.fn(),
    invalidate: vi.fn(),
    openIdentify: vi.fn(),
    identifyOpen: false,
    ...overrides,
  };
}

type FetchCall = { url: string; init?: RequestInit };

function okEnvelope(data: unknown, status = 200) {
  return new Response(JSON.stringify({ success: true, data }), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function failEnvelope(message: string, status: number, data?: unknown) {
  return new Response(JSON.stringify({ success: false, message, data }), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

type Handlers = {
  preview?: (call: FetchCall) => Response | Promise<Response>;
  handoff?: (call: FetchCall) => Response | Promise<Response>;
  activeRun?: () => unknown;
};

function stubCockpitFetch(handlers: Handlers = {}) {
  const calls: FetchCall[] = [];
  vi.stubGlobal(
    "fetch",
    async (url: string | URL | Request, init?: RequestInit) => {
      const call = { url: String(url), init };
      calls.push(call);
      const target = call.url;
      const method = init?.method ?? "GET";
      if (target.includes("/runs/active")) {
        return okEnvelope(handlers.activeRun?.() ?? RUN);
      }
      if (target.includes("/timeline")) {
        return okEnvelope(TIMELINE);
      }
      if (target.includes("/downtimes/pending")) {
        return okEnvelope({ items: [] });
      }
      if (target.includes("handoff-preview")) {
        return (
          (await handlers.preview?.(call)) ??
          okEnvelope({ currentRun: RUN, nextOperation: NEXT_OP, available: true, block: null })
        );
      }
      if (target.includes("/handoff") && method === "POST") {
        return (
          (await handlers.handoff?.(call)) ?? okEnvelope(HANDOFF_RESULT)
        );
      }
      if (target.endsWith("/stop") && method === "POST") {
        return okEnvelope({ ...RUN, status: "completed", endedAt: "2026-10-09T10:06:00Z" });
      }
      if (target.includes("downtime-reasons")) {
        return okEnvelope({
          items: [
            { code: "setup", label: "Setup", category: "preparacao", requiresNote: false },
          ],
        });
      }
      return okEnvelope({});
    },
  );
  return calls;
}

const posts = (calls: FetchCall[]) =>
  calls.filter((call) => (call.init?.method ?? "GET") === "POST");
const handoffPosts = (calls: FetchCall[]) =>
  posts(calls).filter((call) => call.url.includes("/handoff"));

function renderControls(
  overrides: {
    onHandoffCompleted?: () => void;
    runUpdatedSignal?: number;
  } = {},
) {
  return render(
    <OperatorSessionContext.Provider value={sessionCtx()}>
      <ProductionRunControls
        token="tok-1"
        branch="02"
        workCenter="CT-63"
        operation={OPERATION}
        runUpdatedSignal={overrides.runUpdatedSignal ?? 0}
        onHandoffCompleted={overrides.onHandoffCompleted}
      />
    </OperatorSessionContext.Provider>,
  );
}



async function openFinishSheet() {
  const finish = await screen.findByRole("button", { name: /Encerrar/i });
  fireEvent.click(finish);
  return screen.findByRole("dialog");
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  clearPendingHandoffIntent("run-a-1");
});

describe("troca guiada de OP (E2)", () => {
  it("Encerrar abre o modal de decisão sem gravar nada (AC-01/02)", async () => {
    const calls = stubCockpitFetch();
    renderControls();
    const dialog = await openFinishSheet();

    expect(dialog).toBeInTheDocument();
    expect(screen.getByText("Finalizar operação")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Encerrar produção/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Ir para a próxima OP/i }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Cancelar/i })).toBeInTheDocument();
    // Apenas leituras — nenhum POST até escolha explícita.
    expect(posts(calls)).toHaveLength(0);
  });

  it("Cancelar fecha a interface e deixa o run intacto (AC-03)", async () => {
    const calls = stubCockpitFetch();
    renderControls();
    await openFinishSheet();

    fireEvent.click(screen.getByRole("button", { name: /Cancelar/i }));

    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );
    expect(posts(calls)).toHaveLength(0);
    // Run ainda ativo na tela — contagem continua exibida.
    expect(
      (await screen.findAllByText(/Contando|Peças contadas/)).length,
    ).toBeGreaterThan(0);
  });

  it("'Encerrar produção' executa o Stop tradicional (AC-04)", async () => {
    const calls = stubCockpitFetch();
    renderControls();
    await openFinishSheet();

    fireEvent.click(
      screen.getByRole("button", { name: /Encerrar produção/i }),
    );

    await waitFor(() => {
      const stops = posts(calls).filter((call) => call.url.endsWith("/stop"));
      expect(stops).toHaveLength(1);
    });
    expect(handoffPosts(calls)).toHaveLength(0);
  });

  it("sem próxima OP: troca indisponível e Stop preservado (AC-07)", async () => {
    stubCockpitFetch({
      preview: () =>
        okEnvelope({
          currentRun: RUN,
          nextOperation: null,
          available: false,
          block: {
            code: "no_next_operation",
            message: "Não há próxima OP disponível para este posto.",
          },
        }),
    });
    renderControls();
    await openFinishSheet();

    const nextButton = await screen.findByRole("button", {
      name: /Ir para a próxima OP/i,
    });
    await waitFor(() => expect(nextButton).toBeDisabled());
    expect(
      await screen.findByText(/Não há próxima OP disponível/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Encerrar produção/i }),
    ).toBeEnabled();
  });

  it("falha da prévia: troca indisponível com retry e Stop preservado (AC-07)", async () => {
    let previewCalls = 0;
    stubCockpitFetch({
      preview: () => {
        previewCalls += 1;
        return failEnvelope("Prévia indisponível.", 503);
      },
    });
    renderControls();
    await openFinishSheet();

    expect(
      await screen.findByText(/Troca indisponível/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Encerrar produção/i }),
    ).toBeEnabled();

    fireEvent.click(screen.getByRole("button", { name: /Tentar novamente/i }));
    await waitFor(() => expect(previewCalls).toBe(2));
  });

  it("prévia bloqueada por parada sem motivo abre classificação existente (E2.RQ-07)", async () => {
    let runReads = 0;
    stubCockpitFetch({
      activeRun: () => {
        runReads += 1;
        // Após a reconciliação o snapshot traz a pendência detectada pelo backend.
        return runReads > 1
          ? {
              ...RUN,
              pendingDowntime: {
                id: "dt-pend-1",
                runId: RUN.id,
                reasonCode: null,
                reasonLabel: null,
                category: null,
                note: null,
                confirmed: false,
                source: "operator_pause",
                startedAt: "2026-10-09T09:50:00Z",
                endedAt: "2026-10-09T09:55:00Z",
              },
              pendingDowntimeCount: 1,
            }
          : RUN;
      },
      preview: () =>
        okEnvelope({
          currentRun: RUN,
          nextOperation: NEXT_OP,
          available: false,
          block: {
            code: "pending_classification",
            message: "Classifique a parada antes de trocar de OP.",
          },
        }),
    });
    renderControls();
    await openFinishSheet();

    expect(
      await screen.findByText(/Classifique a parada antes de trocar de OP/),
    ).toBeInTheDocument();
    const nextButton = screen.getByRole("button", {
      name: /Ir para a próxima OP/i,
    });
    expect(nextButton).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: /Informar motivo/i }));

    // Sai da finalização e abre o modal de motivo já existente.
    await waitFor(() =>
      expect(screen.queryByText("Finalizar operação")).not.toBeInTheDocument(),
    );
    expect(
      await screen.findByText("Por que a produção parou?"),
    ).toBeInTheDocument();
  });

  it("handoff bem-sucedido: um POST E1 e reconciliação (AC-05/06/10)", async () => {
    const calls = stubCockpitFetch();
    const onHandoffCompleted = vi.fn();
    renderControls({ onHandoffCompleted });
    await openFinishSheet();

    // Aguarda a prévia habilitar a opção.
    const nextButton = await screen.findByRole("button", {
      name: /Ir para a próxima OP/i,
    });
    await waitFor(() => expect(nextButton).toBeEnabled());
    expect(await screen.findByText(/24640401003/)).toBeInTheDocument();

    fireEvent.click(nextButton);

    await waitFor(() => expect(onHandoffCompleted).toHaveBeenCalledTimes(1));
    const request = handoffPosts(calls);
    expect(request).toHaveLength(1);
    const body = JSON.parse(String(request[0]!.init?.body)) as {
      requestId: string;
      branch: string;
      workCenter: string;
      expectedNext: { productionOrder: string; operationCode: string };
      website: string;
    };
    expect(body.requestId).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/,
    );
    expect(body.branch).toBe("02");
    expect(body.workCenter).toBe("CT-63");
    expect(body.expectedNext).toEqual({
      productionOrder: "24640401003",
      operationCode: "05",
    });
    // Sem Play após handoff: nenhum POST em /runs (start) foi feito.
    expect(
      posts(calls).filter((call) => /\/runs(\?|$)/.test(call.url)),
    ).toHaveLength(0);
    // Reconciliação: estado autoritativo relido.
    await waitFor(() =>
      expect(
        calls.filter((call) => call.url.includes("/runs/active")).length,
      ).toBeGreaterThanOrEqual(2),
    );
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("duplo clique não duplica o POST (AC-09)", async () => {
    let release: (value: Response) => void = () => undefined;
    const calls = stubCockpitFetch({
      handoff: () =>
        new Promise<Response>((resolve) => {
          release = resolve;
        }),
    });
    renderControls();
    await openFinishSheet();

    const nextButton = await screen.findByRole("button", {
      name: /Ir para a próxima OP/i,
    });
    await waitFor(() => expect(nextButton).toBeEnabled());
    fireEvent.click(nextButton);
    fireEvent.click(nextButton);
    fireEvent.click(nextButton);

    release(okEnvelope(HANDOFF_RESULT));
    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );
    expect(handoffPosts(calls)).toHaveLength(1);
  });

  it("count_boundary_stale revalida a prévia e exige nova escolha (AC-08)", async () => {
    let previewCalls = 0;
    let handoffCalls = 0;
    const calls = stubCockpitFetch({
      preview: () => {
        previewCalls += 1;
        return okEnvelope({
          currentRun: RUN,
          nextOperation: NEXT_OP,
          available: true,
          block: null,
        });
      },
      handoff: () => {
        handoffCalls += 1;
        if (handoffCalls === 1) {
          return failEnvelope(
            "A contagem avançou desde a prévia.",
            409,
            { code: "count_boundary_stale" },
          );
        }
        return okEnvelope(HANDOFF_RESULT);
      },
    });
    renderControls();
    await openFinishSheet();

    const nextButton = await screen.findByRole("button", {
      name: /Ir para a próxima OP/i,
    });
    await waitFor(() => expect(nextButton).toBeEnabled());
    fireEvent.click(nextButton);

    // Nova prévia automática — operador reconfirma explicitamente.
    await waitFor(() => expect(previewCalls).toBe(2));
    expect(handoffPosts(calls)).toHaveLength(1);

    await waitFor(() => expect(nextButton).toBeEnabled());
    fireEvent.click(nextButton);
    await waitFor(() => expect(handoffPosts(calls)).toHaveLength(2));
    // Nova intenção = nova chave idempotente.
    const first = JSON.parse(String(handoffPosts(calls)[0]!.init?.body));
    const second = JSON.parse(String(handoffPosts(calls)[1]!.init?.body));
    expect(first.requestId).not.toBe(second.requestId);
  });

  it("resultado incerto reusa o mesmo requestId no retry (AC-09)", async () => {
    let handoffCalls = 0;
    const calls = stubCockpitFetch({
      handoff: () => {
        handoffCalls += 1;
        if (handoffCalls === 1) {
          return Promise.reject(new TypeError("network down"));
        }
        return okEnvelope({ ...HANDOFF_RESULT, replayed: true });
      },
    });
    renderControls();
    await openFinishSheet();

    const nextButton = await screen.findByRole("button", {
      name: /Ir para a próxima OP/i,
    });
    await waitFor(() => expect(nextButton).toBeEnabled());
    fireEvent.click(nextButton);

    expect(
      await screen.findByText(/A resposta não chegou/i),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Tentar novamente/i }));

    await waitFor(() => expect(handoffPosts(calls)).toHaveLength(2));
    const first = JSON.parse(String(handoffPosts(calls)[0]!.init?.body));
    const second = JSON.parse(String(handoffPosts(calls)[1]!.init?.body));
    expect(first.requestId).toBe(second.requestId);
    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );
  });

  it("queue_changed recarrega a prévia — escolha explícita obrigatória (AC-08)", async () => {
    let previewCalls = 0;
    stubCockpitFetch({
      preview: () => {
        previewCalls += 1;
        return okEnvelope({
          currentRun: RUN,
          nextOperation: NEXT_OP,
          available: true,
          block: null,
        });
      },
      handoff: () =>
        failEnvelope("A fila publicada mudou.", 409, { code: "queue_changed" }),
    });
    renderControls();
    await openFinishSheet();

    const nextButton = await screen.findByRole("button", {
      name: /Ir para a próxima OP/i,
    });
    await waitFor(() => expect(nextButton).toBeEnabled());
    fireEvent.click(nextButton);

    await waitFor(() => expect(previewCalls).toBe(2));
    expect(await screen.findByText(/fila publicada mudou/i)).toBeInTheDocument();
  });

  it("pending_classification abre o fluxo de motivo existente (AC-08)", async () => {
    let refreshSeen = false;
    const calls = stubCockpitFetch({
      activeRun: () => {
        // Após o 409, a reconciliação expõe a parada pendente do backend.
        if (!refreshSeen) return RUN;
        return {
          ...RUN,
          pendingDowntime: {
            id: "dt-pend-1",
            runId: "run-a-1",
            reasonCode: null,
            reasonLabel: null,
            category: null,
            note: null,
            confirmed: false,
            source: "system",
            startedAt: "2026-10-09T09:50:00Z",
            endedAt: "2026-10-09T09:55:00Z",
          },
          pendingDowntimeCount: 1,
        };
      },
      handoff: () => {
        refreshSeen = true;
        return failEnvelope(
          "Há uma parada sem motivo informado.",
          409,
          { code: "pending_classification" },
        );
      },
    });
    renderControls();
    await openFinishSheet();

    const nextButton = await screen.findByRole("button", {
      name: /Ir para a próxima OP/i,
    });
    await waitFor(() => expect(nextButton).toBeEnabled());
    fireEvent.click(nextButton);

    expect(await screen.findByText("Parada sem motivo")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Informar motivo/i }));

    // Modal de motivo existente abre — classificação nunca é automática.
    expect(
      await screen.findByText(/Por que a produção parou/i),
    ).toBeInTheDocument();
    expect(handoffPosts(calls)).toHaveLength(1);
  });

  it("run_not_active reconcilia o estado autoritativo (AC-10)", async () => {
    const calls = stubCockpitFetch({
      handoff: () =>
        failEnvelope("Run encerrado.", 409, { code: "run_not_active" }),
    });
    renderControls();
    await openFinishSheet();

    const nextButton = await screen.findByRole("button", {
      name: /Ir para a próxima OP/i,
    });
    await waitFor(() => expect(nextButton).toBeEnabled());
    const activeBefore = calls.filter((call) =>
      call.url.includes("/runs/active"),
    ).length;
    fireEvent.click(nextButton);

    expect(await screen.findByText(/Produção já atualizada/i)).toBeInTheDocument();
    await waitFor(() =>
      expect(
        calls.filter((call) => call.url.includes("/runs/active")).length,
      ).toBeGreaterThan(activeBefore),
    );
  });

  it("resultado incerto bloqueia Stop/troca; fechar preserva a intenção (RW-01)", async () => {
    let handoffCalls = 0;
    const calls = stubCockpitFetch({
      handoff: () => {
        handoffCalls += 1;
        if (handoffCalls === 1) {
          return Promise.reject(new TypeError("network down"));
        }
        return okEnvelope({ ...HANDOFF_RESULT, replayed: true });
      },
    });
    renderControls();
    await openFinishSheet();

    const nextButton = await screen.findByRole("button", {
      name: /Ir para a próxima OP/i,
    });
    await waitFor(() => expect(nextButton).toBeEnabled());
    fireEvent.click(nextButton);

    // Resultado desconhecido: Stop e nova troca ficam bloqueados até a
    // reconciliação segura — nenhuma escrita contraditória sai.
    await screen.findByText(/A resposta não chegou/i);
    expect(
      screen.getByRole("button", { name: /Encerrar produção/i }),
    ).toBeDisabled();
    expect(nextButton).toBeDisabled();

    // Cancelar reconcilia e fecha, mas a intenção NÃO morre.
    fireEvent.click(screen.getByRole("button", { name: /Cancelar/i }));
    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );

    // Reabrir a finalização restaura o retry da MESMA intenção.
    await openFinishSheet();
    await screen.findByText(/A resposta não chegou/i);
    fireEvent.click(screen.getByRole("button", { name: /Tentar novamente/i }));

    await waitFor(() => expect(handoffPosts(calls)).toHaveLength(2));
    const bodies = handoffPosts(calls).map((call) =>
      JSON.parse(String(call.init?.body)),
    );
    expect(bodies[0].requestId).toBe(bodies[1].requestId);
    expect(bodies[0].expectedNext).toEqual(bodies[1].expectedNext);
    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );
  });

  it("remount card↔detalhe preserva a intenção incerta (RW-01)", async () => {
    let handoffCalls = 0;
    const calls = stubCockpitFetch({
      handoff: () => {
        handoffCalls += 1;
        if (handoffCalls === 1) {
          return Promise.reject(new TypeError("network down"));
        }
        return okEnvelope({ ...HANDOFF_RESULT, replayed: true });
      },
    });
    const first = renderControls();
    await openFinishSheet();

    const nextButton = await screen.findByRole("button", {
      name: /Ir para a próxima OP/i,
    });
    await waitFor(() => expect(nextButton).toBeEnabled());
    fireEvent.click(nextButton);
    await screen.findByText(/A resposta não chegou/i);

    // Navegação card→detalhe desmonta o controlador — a intenção fica
    // no registro do módulo e sobrevive.
    first.unmount();
    renderControls();
    await openFinishSheet();

    await screen.findByText(/A resposta não chegou/i);
    fireEvent.click(screen.getByRole("button", { name: /Tentar novamente/i }));

    await waitFor(() => expect(handoffPosts(calls)).toHaveLength(2));
    const bodies = handoffPosts(calls).map((call) =>
      JSON.parse(String(call.init?.body)),
    );
    expect(bodies[0].requestId).toBe(bodies[1].requestId);
  });

  it("conflito impeditivo trava nova escrita até a recuperação (RW-02)", async () => {
    const calls = stubCockpitFetch({
      handoff: () =>
        failEnvelope("Há uma parada sem motivo informado.", 409, {
          code: "pending_classification",
        }),
    });
    renderControls();
    await openFinishSheet();

    const nextButton = await screen.findByRole("button", {
      name: /Ir para a próxima OP/i,
    });
    await waitFor(() => expect(nextButton).toBeEnabled());
    fireEvent.click(nextButton);

    await screen.findByText("Parada sem motivo");
    // Conflito impeditivo: a opção fica desabilitada e um clique (mesmo
    // forçado) não gera uma segunda escrita — a recuperação prevista é
    // classificar a parada primeiro.
    await waitFor(() => expect(nextButton).toBeDisabled());
    fireEvent.click(nextButton);
    expect(handoffPosts(calls)).toHaveLength(1);
  });

  it("Stop com falha mantém o modal aberto e a ação recuperável (RW-03)", async () => {
    let stopCalls = 0;
    const calls = stubCockpitFetch();
    const originalFetch = globalThis.fetch;
    vi.stubGlobal("fetch", async (url: string | URL | Request, init?: RequestInit) => {
      const target = String(url);
      if (target.endsWith("/stop") && (init?.method ?? "GET") === "POST") {
        stopCalls += 1;
        if (stopCalls === 1) {
          return failEnvelope("Falha ao encerrar.", 500);
        }
      }
      return originalFetch(url, init);
    });
    renderControls();
    await openFinishSheet();

    fireEvent.click(
      screen.getByRole("button", { name: /Encerrar produção/i }),
    );

    // Falha do Stop: modal permanece aberto, erro visível, sem handoff.
    expect(
      await screen.findByText(/Não foi possível encerrar a produção/i),
    ).toBeInTheDocument();
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(handoffPosts(calls)).toHaveLength(0);

    // Ação recuperável: nova tentativa encerra e fecha a decisão.
    fireEvent.click(
      screen.getByRole("button", { name: /Encerrar produção/i }),
    );
    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );
    expect(stopCalls).toBe(2);
  });

  it("sem fonte criptográfica nenhum POST sai — falha recuperável (RW-04)", async () => {
    const calls = stubCockpitFetch();
    vi.stubGlobal("crypto", {});
    renderControls();
    await openFinishSheet();

    const nextButton = await screen.findByRole("button", {
      name: /Ir para a próxima OP/i,
    });
    await waitFor(() => expect(nextButton).toBeEnabled());
    fireEvent.click(nextButton);

    expect(
      await screen.findByText(/identificador seguro/i),
    ).toBeInTheDocument();
    expect(handoffPosts(calls)).toHaveLength(0);
  });

  it("readback falho após POST confirmado não vira mutação incerta (RW-05)", async () => {
    let handoffDone = false;
    const calls = stubCockpitFetch({
      handoff: () => {
        handoffDone = true;
        return okEnvelope(HANDOFF_RESULT);
      },
      activeRun: () => {
        // Após a confirmação, a releitura do run falha — o resultado
        // confirmado continua válido e nenhum POST adicional sai.
        if (handoffDone) throw new Error("readback down");
        return RUN;
      },
    });
    const onHandoffCompleted = vi.fn();
    renderControls({ onHandoffCompleted });
    await openFinishSheet();

    const nextButton = await screen.findByRole("button", {
      name: /Ir para a próxima OP/i,
    });
    await waitFor(() => expect(nextButton).toBeEnabled());
    fireEvent.click(nextButton);

    await waitFor(() => expect(onHandoffCompleted).toHaveBeenCalledTimes(1));
    // Sem tela de "resposta não chegou" e sem retry de escrita.
    expect(screen.queryByText(/A resposta não chegou/i)).not.toBeInTheDocument();
    expect(handoffPosts(calls)).toHaveLength(1);
    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );
  });

  it("run substituído invalida a decisão — Stop antigo não toca o novo run (RW-06)", async () => {
    let activeRun: unknown = RUN;
    const calls = stubCockpitFetch({
      activeRun: () => activeRun,
      // run_not_active → a reconciliação substitui o run sob o modal aberto.
      handoff: () =>
        failEnvelope("Run encerrado.", 409, { code: "run_not_active" }),
    });
    renderControls();
    await openFinishSheet();

    // Modal aberto para o run A; o conflito dispara a reconciliação que
    // traz o run B (outra OP) como ativo neste posto.
    const nextButton = await screen.findByRole("button", {
      name: /Ir para a próxima OP/i,
    });
    await waitFor(() => expect(nextButton).toBeEnabled());
    activeRun = { ...RUN, id: "run-b-1", productionOrder: "24640401003", operationCode: "05" };
    fireEvent.click(nextButton);

    // A decisão antiga é invalidada e apresenta a situação atual.
    expect(
      await screen.findByText(/A produção ativa deste posto mudou/i),
    ).toBeInTheDocument();

    // Nenhuma das duas escritas fica disponível para o run B.
    expect(
      screen.queryByRole("button", { name: /Encerrar produção/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /Ir para a próxima OP/i }),
    ).not.toBeInTheDocument();
    const stopPosts = calls.filter(
      (call) =>
        (call.init?.method ?? "GET") === "POST" && call.url.endsWith("/stop"),
    );
    expect(stopPosts).toHaveLength(0);
    expect(handoffPosts(calls)).toHaveLength(1);
  });

  it("timeout 504 é incerto — retry repete body e requestId idênticos (RW-07)", async () => {
    const bodies: unknown[] = [];
    let handoffCalls = 0;
    const onHandoffCompleted = vi.fn();
    const calls = stubCockpitFetch({
      handoff: (call) => {
        handoffCalls += 1;
        bodies.push(JSON.parse(String(call.init?.body)));
        return handoffCalls === 1
          ? new Response("Gateway Timeout", { status: 504 })
          : okEnvelope(HANDOFF_RESULT);
      },
    });
    renderControls({ onHandoffCompleted });
    await openFinishSheet();

    const nextButton = await screen.findByRole("button", {
      name: /Ir para a próxima OP/i,
    });
    await waitFor(() => expect(nextButton).toBeEnabled());
    fireEvent.click(nextButton);

    // 504: commit não comprovável — tela incerta, nenhuma escrita paralela.
    expect(
      await screen.findByText(/A resposta não chegou/i),
    ).toBeInTheDocument();
    expect(handoffPosts(calls)).toHaveLength(1);

    fireEvent.click(screen.getByRole("button", { name: /Tentar novamente/i }));
    await waitFor(() => expect(onHandoffCompleted).toHaveBeenCalledTimes(1));

    // Retry idempotente: exatamente o mesmo payload, mesma chave.
    expect(handoffPosts(calls)).toHaveLength(2);
    expect(bodies).toHaveLength(2);
    expect(bodies[1]).toEqual(bodies[0]);
  });

  it("intenção incerta bloqueia Pause/Resume/Stop fora do modal e sobrevive a remount e F5 (RW-08)", async () => {
    const bodies: unknown[] = [];
    let failOnce = true;
    stubCockpitFetch({
      handoff: (call) => {
        bodies.push(JSON.parse(String(call.init?.body)));
        if (failOnce) {
          failOnce = false;
          return Promise.reject(new TypeError("network down"));
        }
        return okEnvelope(HANDOFF_RESULT);
      },
    });
    const view = renderControls();
    await openFinishSheet();

    const nextButton = await screen.findByRole("button", {
      name: /Ir para a próxima OP/i,
    });
    await waitFor(() => expect(nextButton).toBeEnabled());
    fireEvent.click(nextButton);
    expect(
      await screen.findByText(/A resposta não chegou/i),
    ).toBeInTheDocument();

    // Fechar o modal NÃO libera escritas: a intenção segue sem resolução.
    fireEvent.click(screen.getByRole("button", { name: /Cancelar/i }));
    await waitFor(() =>
      expect(screen.queryByText(/A resposta não chegou/i)).not.toBeInTheDocument(),
    );
    const pauseBtn = await screen.findByRole("button", { name: /Pausar/i });
    expect(pauseBtn).toBeDisabled();

    // Remount (navegação card↔detalhe): o bloqueio vem do registro do
    // módulo — continua sem reabrir o modal.
    view.unmount();
    const remounted = renderControls();
    expect(
      await screen.findByRole("button", { name: /Pausar/i }),
    ).toBeDisabled();

    // F5: a memória do módulo zera; o sessionStorage reidrata a intenção.
    pendingHandoffIntents.clear();
    remounted.unmount();
    const afterReload = renderControls();
    expect(
      await screen.findByRole("button", { name: /Pausar/i }),
    ).toBeDisabled();

    // A recuperação: reabrir a finalização cai direto na tela de retry
    // com o MESMO requestId — Stop continua bloqueado em estado incerto.
    fireEvent.click(await screen.findByRole("button", { name: /^Encerrar$/i }));
    expect(
      await screen.findByText(/A resposta não chegou/i),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Encerrar produção/i }),
    ).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: /Tentar novamente/i }));
    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );
    expect(bodies).toHaveLength(2);
    expect(bodies[1]).toEqual(bodies[0]);
    afterReload.unmount();
  });

  it("cancelar o motivo não reabre a finalização (RW-09)", async () => {
    const calls = stubCockpitFetch({
      activeRun: () => ({
        ...RUN,
        downtime: {
          id: "dt-open-1",
          runId: RUN.id,
          reasonCode: null,
          reasonLabel: null,
          category: null,
          note: null,
          confirmed: false,
          source: "operator_pause",
          startedAt: "2026-10-09T09:50:00Z",
          endedAt: null,
        },
      }),
    });
    renderControls();
    // A parada sem motivo abre o modal de motivo automaticamente.
    await screen.findByText(/Por que a produção parou/i);

    // Encerrar marca a retomada e mantém o modal de motivo.
    fireEvent.click(await screen.findByRole("button", { name: /^Encerrar$/i }));

    // Cancelar o motivo: volta ao estado anterior — a finalização NÃO
    // reabre e nenhuma prévia é consultada.
    const previewCallsBefore = calls.filter((call) =>
      call.url.includes("handoff-preview"),
    ).length;
    fireEvent.click(screen.getAllByRole("button", { name: /^Fechar$/i }).at(-1)!);
    await waitFor(() =>
      expect(
        screen.queryByText(/Por que a produção parou/i),
      ).not.toBeInTheDocument(),
    );
    expect(screen.queryByText("Finalizar operação")).not.toBeInTheDocument();
    expect(
      calls.filter((call) => call.url.includes("handoff-preview")),
    ).toHaveLength(previewCallsBefore);
  });

  it("classificar o motivo reabre a finalização com prévia nova (RW-09)", async () => {
    stubCockpitFetch({
      activeRun: () => ({
        ...RUN,
        downtime: {
          id: "dt-open-1",
          runId: RUN.id,
          reasonCode: null,
          reasonLabel: null,
          category: null,
          note: null,
          confirmed: false,
          source: "operator_pause",
          startedAt: "2026-10-09T09:50:00Z",
          endedAt: null,
        },
      }),
      preview: () =>
        okEnvelope({ currentRun: RUN, nextOperation: NEXT_OP, available: true, block: null }),
    });
    renderControls();
    await screen.findByText(/Por que a produção parou/i);

    fireEvent.click(await screen.findByRole("button", { name: /^Encerrar$/i }));

    // Classificação confirmada → finalização reabre com prévia nova.
    fireEvent.click(await screen.findByRole("option", { name: /^Setup$/i }));
    fireEvent.click(screen.getByRole("button", { name: /Confirmar motivo/i }));

    expect(await screen.findByText("Finalizar operação")).toBeInTheDocument();
    const nextButton = await screen.findByRole("button", {
      name: /Ir para a próxima OP/i,
    });
    await waitFor(() => expect(nextButton).toBeEnabled());
  });
});
