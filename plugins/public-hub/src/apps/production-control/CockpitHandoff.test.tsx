/** @vitest-environment jsdom */
import "@testing-library/jest-dom/vitest";
import {
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { MachineLoadOperation } from "./api.ts";
import { OperatorCockpit } from "./CockpitPage.tsx";
import {
  clearPendingHandoffIntent,
  pendingHandoffIntentFor,
  registerPendingHandoffIntent,
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
  production_status: "in_progress",
  is_in_production: true,
  production_started_date: "2026-10-09",
  production_started_time: "10:00",
  active_operator_name: "Maria Silva",
  active_operator_count: 1,
  appointment_count: null,
  last_appointment_date: null,
} satisfies MachineLoadOperation;

const NEXT_ITEM = {
  ...OPERATION,
  production_order: "24640401003",
  operation_code: "05",
  operation_description: "ROSCA",
  product_description: "Componente Y",
  is_in_production: false,
  production_status: "not_started",
  active_operator_name: null,
  active_operator_count: null,
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
  device: null,
};

const RUN_B = {
  ...RUN,
  id: "run-b-1",
  productionOrder: "24640401003",
  operationCode: "05",
  countedPieces: 0,
  piecesTotal: 0,
};

const RUN_FOREIGN = {
  ...RUN,
  id: "run-x-9",
  productionOrder: "99999999999",
  operationCode: "99",
};

const HANDOFF_RESULT = {
  requestId: "req-1",
  replayed: false,
  transitionAt: "2026-10-09T10:05:00Z",
  boundary: { counter: 1040, counterEpoch: 1 },
  auditId: "audit-1",
  completedRun: { ...RUN, status: "completed", endedAt: "2026-10-09T10:05:00Z" },
  newRun: RUN_B,
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

const SESSION = {
  sessionToken: "sess-1",
  expiresAt: null,
  branch: "02",
  workCenter: "CT-63",
  operatorCode: "001234",
  operatorName: "Maria Silva",
};

const PREVIEW = {
  currentRun: RUN,
  nextOperation: {
    productionOrder: "24640401003",
    operationCode: "05",
    operationDescription: "ROSCA",
    productCode: "10045679",
    productDescription: "Componente Y",
    pendingQty: 30,
    queuePosition: 2,
    queueSize: 4,
  },
  available: true,
  block: null,
};

function machineLoadPayload(items: MachineLoadOperation[]) {
  return {
    branch: "02",
    period: { start_date: "2026-10-09", end_date: "2026-10-09" },
    summary: {
      work_center_count: 1,
      operation_count: items.length,
      order_count: items.length,
      in_production_count: 1,
    },
    snapshot: { refreshed_at: "2026-10-09T10:00:00Z", seeded: true },
    work_centers: [
      {
        work_center: "CT-63",
        work_center_name: "Montagem 03",
        operation_count: items.length,
        order_count: items.length,
        in_production_count: 1,
      },
    ],
    selected: {
      work_center: "CT-63",
      requested_work_center: "CT-63",
      items,
    },
  };
}

type FetchCall = { url: string; init?: RequestInit };

function okEnvelope(data: unknown, status = 200) {
  return new Response(JSON.stringify({ success: true, data }), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function failEnvelope(message: string, status: number) {
  return new Response(JSON.stringify({ success: false, message }), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

class FakeWebSocket {
  static instances: FakeWebSocket[] = [];
  static OPEN = 1;
  readyState = 0;
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  url: string;
  constructor(url: string) {
    this.url = url;
    FakeWebSocket.instances.push(this);
  }
  send() {}
  close() {}
  emit(message: unknown) {
    this.onmessage?.({ data: JSON.stringify(message) });
  }
}

type Deferred<T> = {
  promise: Promise<T>;
  resolve: (value: T) => void;
};
function deferred<T>(): Deferred<T> {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((res) => {
    resolve = res;
  });
  return { promise, resolve };
}

type Handlers = {
  /** Sequência de respostas do GET do run ativo (readback controlado). */
  activeRun?: () => unknown;
  /** Sequência controlada de payloads do machine-load (corrida de reload). */
  machineLoad?: (call: FetchCall) => Response | Promise<Response>;
  handoff?: (call: FetchCall) => Response | Promise<Response>;
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
        const value = handlers.activeRun?.() ?? RUN;
        return value instanceof Response
          ? value
          : okEnvelope(value ?? null);
      }
      if (target.includes("/timeline")) return okEnvelope(TIMELINE);
      if (target.includes("/downtimes/pending")) return okEnvelope({ items: [] });
      if (target.includes("handoff-preview")) return okEnvelope(PREVIEW);
      if (target.includes("/handoff") && method === "POST") {
        return (await handlers.handoff?.(call)) ?? okEnvelope(HANDOFF_RESULT);
      }
      if (target.endsWith("/stop") && method === "POST") {
        return okEnvelope({ ...RUN, status: "completed", endedAt: "2026-10-09T10:06:00Z" });
      }
      if (target.includes("bench-sessions/current")) return okEnvelope(SESSION);
      if (target.endsWith("/bench-sessions") && method === "POST") {
        return okEnvelope(SESSION);
      }
      if (target.includes("downtime-source")) {
        return okEnvelope({
          source: "mes",
          reason: "posto CT MES",
          branch: "02",
          workCenter: "CT-63",
          referenceAt: "2026-10-09T10:00:00Z",
        });
      }
      if (target.includes("work-centers/today")) return okEnvelope({ items: [] });
      if (
        target.includes("process-inspections") ||
        target.includes("appointments") ||
        target.includes("materials")
      ) {
        return okEnvelope({
          items: [],
          summary: { inspection_count: 0, appointment_count: 0, produced_qty: 0 },
        });
      }
      if (target.includes("performance")) return okEnvelope(null);
      if (target.includes("/public/machine-load/") && method === "GET") {
        return (
          (await handlers.machineLoad?.(call)) ??
          okEnvelope(machineLoadPayload([OPERATION, NEXT_ITEM]))
        );
      }
      return okEnvelope({});
    },
  );
  return calls;
}

const handoffPosts = (calls: FetchCall[]) =>
  calls.filter(
    (call) =>
      (call.init?.method ?? "GET") === "POST" && call.url.includes("/handoff"),
  );

const detailVisible = () =>
  screen.queryByLabelText("Voltar para a fila") != null;

async function mountCockpit() {
  window.localStorage.setItem("delpi.pcp.cockpit.work-center.02", "CT-63");
  window.sessionStorage.setItem(
    "delpi.pcp.cockpit.bench-session.02.CT-63",
    JSON.stringify(SESSION),
  );
  render(
    <OperatorCockpit
      token="tok-1"
      branch="02"
      initial={machineLoadPayload([OPERATION, NEXT_ITEM])}
    />,
  );
  // Espera a sessão identificar e o card "Agora nesta bancada" subir.
  await screen.findByRole("button", { name: /^Encerrar$/i });
}

async function runHandoffToCompletion() {
  fireEvent.click(await screen.findByRole("button", { name: /^Encerrar$/i }));
  await screen.findByRole("dialog");
  const nextButton = await screen.findByRole("button", {
    name: /Ir para a próxima OP/i,
  });
  await waitFor(() => expect(nextButton).toBeEnabled());
  fireEvent.click(nextButton);
}

describe("readback pós-handoff (E2 rework final)", { timeout: 30000 }, () => {
  beforeEach(() => {
    FakeWebSocket.instances = [];
    vi.stubGlobal("WebSocket", FakeWebSocket);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
    window.localStorage.clear();
    window.sessionStorage.clear();
    // A view do cockpit vive na query string — zera entre testes.
    window.history.replaceState(null, "", window.location.pathname);
    clearPendingHandoffIntent("run-a-1");
    clearPendingHandoffIntent("run-b-1");
  });

  it("readback coerente com newRun reconcilia e navega para a nova OP", async () => {
    let activeRun: unknown = RUN;
    const calls = stubCockpitFetch({ activeRun: () => activeRun });
    await mountCockpit();
    await runHandoffToCompletion();
    // Readback posterior ao POST traz o run novo na fila nova.
    activeRun = RUN_B;
    await waitFor(() => expect(handoffPosts(calls)).toHaveLength(1));
    await waitFor(() => expect(detailVisible()).toBe(true));
    // Nenhum POST extra de escrita saiu durante a reconciliação.
    expect(handoffPosts(calls)).toHaveLength(1);
  });

  it("GET do run ativo falho após POST confirmado mantém Atualizar (read-only)", async () => {
    let activeRun: unknown = RUN;
    let failReadback = false;
    const calls = stubCockpitFetch({
      activeRun: () => (failReadback ? failEnvelope("falha", 500) : activeRun),
    });
    await mountCockpit();
    await runHandoffToCompletion();
    failReadback = true;
    await waitFor(() => expect(handoffPosts(calls)).toHaveLength(1));
    // Falha de leitura NÃO é mutação incerta: aviso de atualização pendente
    // com retry exclusivamente de leitura; nenhum POST novo sai.
    const refresh = await screen.findByRole("button", { name: /Atualizar/i });
    failReadback = false;
    activeRun = RUN_B;
    fireEvent.click(refresh);
    await waitFor(() => expect(detailVisible()).toBe(true));
    expect(handoffPosts(calls)).toHaveLength(1);
  });

  it("run ativo incoerente (outra OP) mantém atualização pendente", async () => {
    let activeRun: unknown = RUN;
    const calls = stubCockpitFetch({ activeRun: () => activeRun });
    await mountCockpit();
    await runHandoffToCompletion();
    // Readback trouxe um run de OUTRA operação — incoerente com newRun.
    activeRun = RUN_FOREIGN;
    await waitFor(() => expect(handoffPosts(calls)).toHaveLength(1));
    await screen.findByRole("button", { name: /Atualizar/i });
    expect(detailVisible()).toBe(false);
    // Recuperação read-only: quando o readback fica coerente, navega.
    activeRun = RUN_B;
    fireEvent.click(screen.getByRole("button", { name: /Atualizar/i }));
    await waitFor(() => expect(detailVisible()).toBe(true));
    expect(handoffPosts(calls)).toHaveLength(1);
  });

  it("reload explícito superado por evento WebSocket ainda navega à OP certa", async () => {
    // Readback pós-POST incoerente (run de outra OP) → "Atualizar" aparece.
    // O retry explícito fica em voo; um reload disparado por WebSocket
    // vence a disputa de geração e traz o estado coerente — a resposta
    // superada do Atualizar é neutra e a navegação ocorre uma única vez.
    let activeRun: unknown = RUN;
    const stuckReload = deferred<Response>();
    let holdMachineLoad = false;
    stubCockpitFetch({
      activeRun: () => activeRun,
      // holdMachineLoad prende apenas o GET do "Atualizar"; o reload do
      // WebSocket resolve normalmente e vence a geração.
      machineLoad: () =>
        holdMachineLoad
          ? stuckReload.promise
          : okEnvelope(machineLoadPayload([OPERATION, NEXT_ITEM])),
    });
    await mountCockpit();
    await runHandoffToCompletion();
    activeRun = RUN_FOREIGN;
    const refresh = await screen.findByRole("button", { name: /Atualizar/i });
    holdMachineLoad = true;
    fireEvent.click(refresh);

    // Evento de fila via WebSocket dispara o reload que vence a geração.
    holdMachineLoad = false;
    activeRun = RUN_B;
    const socket = FakeWebSocket.instances[0];
    expect(socket).toBeDefined();
    socket!.emit({ type: "machine_load_updated", reason: "sequence" });

    // A resposta superada do retry explícito chega depois — neutra.
    stuckReload.resolve(okEnvelope(machineLoadPayload([OPERATION])));

    await waitFor(() => expect(detailVisible()).toBe(true));
    // Aviso resolvido pela leitura coerente — não fica pendente.
    await waitFor(() =>
      expect(
        screen.queryByRole("button", { name: /Atualizar/i }),
      ).not.toBeInTheDocument(),
    );
  });

  it("reload vencedor do WebSocket com GET do run falho mantém pendência e o run conhecido", async () => {
    // POST confirmado → readback automático preso → reload do WebSocket
    // vence a geração mas FALHA o GET do run ativo → nenhuma leitura
    // coerente com newRun foi observada. O aviso deve permanecer
    // pendente (Atualizar read-only) e o último run conhecido NÃO pode
    // ser apagado pela falha HTTP. Nenhum POST extra de handoff sai.
    const activeRun: unknown = RUN;
    let failRunRead = false;
    let holdMachineLoad = false;
    const stuckMachineLoad = deferred<Response>();
    const handoffGate = deferred<Response>();
    const calls = stubCockpitFetch({
      activeRun: () => (failRunRead ? failEnvelope("falha", 500) : activeRun),
      machineLoad: () =>
        holdMachineLoad
          ? stuckMachineLoad.promise
          : okEnvelope(machineLoadPayload([OPERATION, NEXT_ITEM])),
      handoff: () => handoffGate.promise,
    });
    await mountCockpit();
    await runHandoffToCompletion();

    // Confirma o POST com o readback automático já preso na fila.
    holdMachineLoad = true;
    failRunRead = true;
    handoffGate.resolve(okEnvelope(HANDOFF_RESULT));
    await waitFor(() => expect(handoffPosts(calls)).toHaveLength(1));

    // WebSocket dispara o reload vencedor — GET do run falha nele.
    holdMachineLoad = false;
    const socket = FakeWebSocket.instances[0];
    expect(socket).toBeDefined();
    socket!.emit({ type: "machine_load_updated", reason: "sequence" });
    // A resposta superada do readback automático chega depois — neutra.
    stuckMachineLoad.resolve(okEnvelope(machineLoadPayload([OPERATION, NEXT_ITEM])));

    // Pendência permanece até leitura autoritativa coerente; o run A
    // continua na tela (Encerrar ainda existe — não foi apagado).
    await screen.findByRole("button", { name: /Atualizar/i });
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: /^Encerrar$/i }),
      ).toBeInTheDocument(),
    );
    expect(detailVisible()).toBe(false);
    expect(handoffPosts(calls)).toHaveLength(1);
  });

  it("run órfão com troca incerta resolve pela intenção persistida (mesmo requestId)", async () => {
    // Handoff de A ficou sem resposta e o PCP removeu A da fila. O card
    // órfão oferece recuperação pela intenção persistida: mesmo
    // requestId/contexto no POST idempotente — nunca um Stop fallback.
    registerPendingHandoffIntent("run-a-1", {
      requestId: "req-fixed-1",
      branch: "02",
      workCenter: "CT-63",
      expectedNext: { productionOrder: "24640401003", operationCode: "05" },
    });
    let activeRun: unknown = RUN;
    const calls = stubCockpitFetch({
      activeRun: () => activeRun,
      machineLoad: () => okEnvelope(machineLoadPayload([NEXT_ITEM])),
    });
    window.localStorage.setItem("delpi.pcp.cockpit.work-center.02", "CT-63");
    window.sessionStorage.setItem(
      "delpi.pcp.cockpit.bench-session.02.CT-63",
      JSON.stringify(SESSION),
    );
    // Fila sem a OP do run → OrphanRunCard (o counterRun chega via
    // reload disparado pelo evento WebSocket).
    render(
      <OperatorCockpit
        token="tok-1"
        branch="02"
        initial={machineLoadPayload([NEXT_ITEM])}
      />,
    );
    const socket = FakeWebSocket.instances[0];
    expect(socket).toBeDefined();
    await waitFor(() => expect(socket!.onmessage).toBeTruthy());
    socket!.emit({ type: "machine_load_updated", reason: "sequence" });

    // Stop bloqueado enquanto a intenção não resolve; recuperação existe.
    const stopButton = await screen.findByRole("button", {
      name: /Encerrar produção/i,
    });
    expect(stopButton).toBeDisabled();
    const verify = await screen.findByRole("button", {
      name: /Verificar troca pendente/i,
    });

    // Estado autoritativo pós-handoff: o servidor já trocou para B.
    activeRun = RUN_B;
    fireEvent.click(verify);

    await waitFor(() => expect(handoffPosts(calls)).toHaveLength(1));
    const body = JSON.parse(
      String(handoffPosts(calls)[0].init?.body ?? "{}"),
    ) as Record<string, unknown>;
    expect(body.requestId).toBe("req-fixed-1");
    expect(body.expectedNext).toEqual({
      productionOrder: "24640401003",
      operationCode: "05",
    });
    expect(body.branch).toBe("02");
    expect(body.workCenter).toBe("CT-63");

    // Resolvido: o aviso de troca pendente some e a situação autoritativa
    // (run B na fila) volta a oferecer as ações válidas.
    await waitFor(() =>
      expect(
        screen.queryByRole("button", { name: /Verificar troca pendente/i }),
      ).not.toBeInTheDocument(),
    );
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: /^Encerrar$/i }),
      ).toBeEnabled(),
    );
    // Nenhum Stop foi enviado como fallback.
    expect(
      calls.filter(
        (call) =>
          (call.init?.method ?? "GET") === "POST" &&
          call.url.endsWith("/stop"),
      ),
    ).toHaveLength(0);
  });

  it("run órfão: recuperação com 401 preserva a intenção; sessão válida resolve sem Stop (auth-retry-B)", async () => {
    // Caso B: o retry do card órfão recebe 401 — a sessão é validada
    // ANTES da consulta idempotente, logo o 401 não descarta a
    // tentativa original. A intenção permanece e uma sessão válida
    // resolve o pedido original, sem Stop adicional.
    registerPendingHandoffIntent("run-a-1", {
      requestId: "req-fixed-1",
      branch: "02",
      workCenter: "CT-63",
      expectedNext: { productionOrder: "24640401003", operationCode: "05" },
    });
    let activeRun: unknown = RUN;
    let handoffCalls = 0;
    const calls = stubCockpitFetch({
      activeRun: () => activeRun,
      machineLoad: () => okEnvelope(machineLoadPayload([NEXT_ITEM])),
      handoff: () => {
        handoffCalls += 1;
        return handoffCalls === 1
          ? failEnvelope("sessão expirada", 401)
          : okEnvelope(HANDOFF_RESULT);
      },
    });
    window.localStorage.setItem("delpi.pcp.cockpit.work-center.02", "CT-63");
    window.sessionStorage.setItem(
      "delpi.pcp.cockpit.bench-session.02.CT-63",
      JSON.stringify(SESSION),
    );
    render(
      <OperatorCockpit
        token="tok-1"
        branch="02"
        initial={machineLoadPayload([NEXT_ITEM])}
      />,
    );
    const socket = FakeWebSocket.instances[0];
    await waitFor(() => expect(socket!.onmessage).toBeTruthy());
    socket!.emit({ type: "machine_load_updated", reason: "sequence" });

    const verify = await screen.findByRole("button", {
      name: /Verificar troca pendente/i,
    });
    fireEvent.click(verify);

    // 401 no retry: intenção preservada, sessão invalidada pelo
    // provider oficial e a ação de recuperação continua disponível.
    await screen.findByText(/sessão expirou/i);
    expect(pendingHandoffIntentFor("run-a-1")?.requestId).toBe("req-fixed-1");
    expect(
      await screen.findByRole("button", { name: /Verificar troca pendente/i }),
    ).toBeInTheDocument();

    // Reidentificação pela superfície oficial (chip Identificar).
    fireEvent.click(
      await screen.findByRole("button", { name: /^Identificar$/i }),
    );
    const reg = await screen.findByRole("textbox");
    fireEvent.change(reg, { target: { value: "001234" } });
    fireEvent.click(
      screen.getByRole("button", { name: /Entrar no posto/i }),
    );
    await waitFor(() =>
      expect(screen.queryByRole("textbox")).not.toBeInTheDocument(),
    );

    // Sessão válida: a recuperação resolve a intenção ORIGINAL — mesmo
    // requestId/contexto, sem Stop adicional.
    activeRun = RUN_B;
    fireEvent.click(
      await screen.findByRole("button", { name: /Verificar troca pendente/i }),
    );
    await waitFor(() =>
      expect(
        screen.queryByRole("button", { name: /Verificar troca pendente/i }),
      ).not.toBeInTheDocument(),
    );
    const posts = handoffPosts(calls);
    expect(posts).toHaveLength(2);
    const second = JSON.parse(
      String(posts[1].init?.body ?? "{}"),
    ) as Record<string, unknown>;
    expect(second.requestId).toBe("req-fixed-1");
    expect(second.expectedNext).toEqual({
      productionOrder: "24640401003",
      operationCode: "05",
    });
    expect(
      calls.filter(
        (call) =>
          (call.init?.method ?? "GET") === "POST" &&
          call.url.endsWith("/stop"),
      ),
    ).toHaveLength(0);
  });
});
