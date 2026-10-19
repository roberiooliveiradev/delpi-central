/** @vitest-environment jsdom */
import { act, fireEvent, render, renderHook, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { BenchSessionSnapshot } from "./api.ts";
import { PostActivityCard } from "./PostActivityCard.tsx";
import { PostActivityPage } from "./PostActivityPage.tsx";
import {
  OperatorSessionContext,
  type OperatorSessionContextValue,
} from "./OperatorSessionContext.ts";
import { useWorkCenterActivity } from "./useWorkCenterActivity.ts";

const TODAY = {
  source: "mes",
  branch: "02",
  workCenter: "CT-63",
  reason: "bound_counter",
  date: "2026-10-19",
  timezone: "America/Sao_Paulo",
  from: "2026-10-19T03:00:00Z",
  to: "2026-10-19T16:00:00Z",
  referenceAt: "2026-10-19T16:00:00Z",
  summary: {
    producingSeconds: 7200,
    stoppedSeconds: 1800,
    stopCount: 1,
    pendingReasonCount: 1,
  },
  items: [
    {
      stateEventId: "se-1",
      runId: "run-1",
      productionOrder: "OP-10",
      operationCode: "10",
      state: "producing",
      startedAt: "2026-10-19T12:00:00Z",
      endedAt: "2026-10-19T13:00:00Z",
      source: "operator",
      effectiveDurationSeconds: 3600,
      downtime: null,
    },
    {
      stateEventId: "se-2",
      runId: "run-1",
      productionOrder: "OP-10",
      operationCode: "10",
      state: "stopped",
      startedAt: "2026-10-19T13:00:00Z",
      endedAt: "2026-10-19T13:30:00Z",
      source: "system",
      effectiveDurationSeconds: 1800,
      downtime: {
        id: "dt-1",
        reasonCode: null,
        reasonLabel: null,
        category: null,
        note: null,
        confirmed: false,
        source: "system",
        pendingReason: true,
      },
    },
  ],
};

const TOTVS = {
  source: "totvs",
  branch: "02",
  workCenter: "CT-63",
  reason: "no_bound_counter",
  referenceAt: "2026-10-19T16:00:00Z",
};

function ok(data: unknown, status = 200): Response {
  return new Response(JSON.stringify({ success: true, data }), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function errEnvelope(message: string, status: number): Response {
  return new Response(JSON.stringify({ success: false, message }), {
    status,
    headers: { "Content-Type": "application/json" },
  });
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

function renderWithSession(
  ui: React.ReactElement,
  ctx: OperatorSessionContextValue,
) {
  return render(
    <OperatorSessionContext.Provider value={ctx}>
      {ui}
    </OperatorSessionContext.Provider>,
  );
}

const PAGE_PROPS = {
  token: "tok",
  branch: "02",
  workCenter: "CT-63",
  workCenterName: "Corte 63",
  runRealtimeEvent: null,
  realtimeConnected: true,
  onBack: vi.fn(),
};

afterEach(() => vi.unstubAllGlobals());

describe("fetchMesWorkCenterToday (cliente)", () => {
  it("sends session header and returns mes payload", async () => {
    const calls = stubFetch(() => ok(TODAY));
    const hook = renderHook(() =>
      useWorkCenterActivity({
        token: "tok",
        sessionToken: "sess-1",
        branch: "02",
        workCenter: "CT-63",
      }),
    );
    await waitFor(() => expect(hook.result.current.data?.source).toBe("mes"));
    expect(calls[0].url).toContain("/mes/work-centers/today?branch=02&workCenter=CT-63");
    expect(calls[0].init?.headers).toMatchObject({
      "X-Delpi-Bench-Session": "sess-1",
    });
  });

  it("keeps totvs as totvs — never an empty mes history", async () => {
    stubFetch(() => ok(TOTVS));
    const hook = renderHook(() =>
      useWorkCenterActivity({
        token: "tok",
        sessionToken: "sess-1",
        branch: "02",
        workCenter: "CT-63",
      }),
    );
    await waitFor(() => expect(hook.result.current.data?.source).toBe("totvs"));
    expect(hook.result.current.error).toBeNull();
  });

  it("503 surfaces retryable unavailability", async () => {
    stubFetch(() => errEnvelope("Fonte indisponível", 503));
    const hook = renderHook(() =>
      useWorkCenterActivity({
        token: "tok",
        sessionToken: "sess-1",
        branch: "02",
        workCenter: "CT-63",
      }),
    );
    await waitFor(() => expect(hook.result.current.error?.retryable).toBe(true));
    expect(hook.result.current.data).toBeNull();
  });

  it("401 clears data and invalidates the session", async () => {
    const onAuthError = vi.fn();
    stubFetch(() => errEnvelope("Sessão inválida", 401));
    const hook = renderHook(() =>
      useWorkCenterActivity({
        token: "tok",
        sessionToken: "sess-old",
        branch: "02",
        workCenter: "CT-63",
        onAuthError,
      }),
    );
    await waitFor(() => expect(onAuthError).toHaveBeenCalledTimes(1));
    expect(hook.result.current.data).toBeNull();
    expect(hook.result.current.error).toBeNull();
  });

  it("ignores a response from a stale work center", async () => {
    let resolveFirst: ((v: Response) => void) | null = null;
    stubFetch((url) => {
      if (url.includes("CT-OLD")) {
        return new Promise<Response>((r) => {
          resolveFirst = r;
        });
      }
      return Promise.resolve(ok({ ...TODAY, workCenter: "CT-63" }));
    });
    const hook = renderHook(
      ({ wc }) =>
        useWorkCenterActivity({
          token: "tok",
          sessionToken: "sess-1",
          branch: "02",
          workCenter: wc,
        }),
      { initialProps: { wc: "CT-OLD" } },
    );
    hook.rerender({ wc: "CT-63" });
    // resposta tardia do CT antigo chega depois da troca: não aplica,
    // e a reconciliação pendente dispara o GET do novo CT.
    await act(async () => {
      resolveFirst?.(ok({ ...TODAY, workCenter: "CT-OLD" }));
      await Promise.resolve();
    });
    await waitFor(() =>
      expect(hook.result.current.data?.workCenter).toBe("CT-63"),
    );
  });

  it("does not fetch without a session token", async () => {
    const calls = stubFetch(() => ok(TODAY));
    const hook = renderHook(() =>
      useWorkCenterActivity({
        token: "tok",
        sessionToken: null,
        branch: "02",
        workCenter: "CT-63",
      }),
    );
    await waitFor(() => expect(hook.result.current.loading).toBe(false));
    expect(calls.length).toBe(0);
    expect(hook.result.current.data).toBeNull();
  });
});

describe("PostActivityCard", () => {
  it("shows compact summary with pending badge", async () => {
    stubFetch(() => ok(TODAY));
    renderWithSession(
      <PostActivityCard
        token="tok"
        branch="02"
        workCenter="CT-63"
        runRealtimeEvent={null}
        realtimeConnected
        onOpen={vi.fn()}
      />,
      sessionCtx("identified"),
    );
    await waitFor(() =>
      expect(screen.getByText(/1 sem motivo/)).toBeInTheDocument(),
    );
    expect(screen.getByText("Atividade do posto")).toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument(); // badge
  });

  it("invites identification when there is no session", () => {
    const calls = stubFetch(() => ok(TODAY));
    renderWithSession(
      <PostActivityCard
        token="tok"
        branch="02"
        workCenter="CT-63"
        runRealtimeEvent={null}
        realtimeConnected
        onOpen={vi.fn()}
      />,
      sessionCtx("anonymous"),
    );
    expect(
      screen.getByText(/Identifique-se para ver paradas/),
    ).toBeInTheDocument();
    expect(calls.length).toBe(0);
  });
});

describe("PostActivityPage", () => {
  it("renders official summary and a classifiable pending stop", async () => {
    stubFetch(() => ok(TODAY));
    renderWithSession(
      <PostActivityPage {...PAGE_PROPS} />,
      sessionCtx("identified"),
    );
    await waitFor(() =>
      expect(screen.getByText("Parada")).toBeInTheDocument(),
    );
    // resumo vem da API, não de soma local
    expect(screen.getByText("02:00:00")).toBeInTheDocument(); // producing
    expect(screen.getAllByText("00:30:00").length).toBeGreaterThan(0); // stopped
    expect(screen.getByText(/sem motivo/)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Informar motivo" }),
    ).toBeInTheDocument();
    expect(screen.getAllByText(/OP-10/).length).toBeGreaterThan(0);
  });

  it("classifies by runId + downtimeId and refreshes", async () => {
    const calls = stubFetch((url) => {
      if (url.includes("/downtime-reasons")) {
        return ok({ items: [{ code: "maintenance", label: "Manutenção", category: "x", requiresNote: false }] });
      }
      if (url.includes("/classify")) {
        return ok({ id: "dt-1", reasonCode: "maintenance", confirmed: true });
      }
      return ok(TODAY);
    });
    renderWithSession(
      <PostActivityPage {...PAGE_PROPS} />,
      sessionCtx("identified"),
    );
    const classifyBtn = await screen.findByRole("button", {
      name: "Informar motivo",
    });
    fireEvent.click(classifyBtn);
    const reasonBtn = await screen.findByRole("option", {
      name: "Manutenção",
    });
    fireEvent.click(reasonBtn);
    fireEvent.click(screen.getByRole("button", { name: "Confirmar motivo" }));
    await waitFor(() =>
      expect(
        calls.some(
          (c) =>
            c.url.includes("/runs/run-1/downtimes/dt-1/classify") &&
            c.init?.method === "POST",
        ),
      ).toBe(true),
    );
    const classifyCall = calls.find((c) => c.url.includes("/classify"));
    expect(classifyCall?.init?.headers).toMatchObject({
      "X-Delpi-Bench-Session": "sess-1",
    });
  });

  it("stopped without downtime shows no classify action", async () => {
    stubFetch(() =>
      ok({
        ...TODAY,
        items: [
          { ...TODAY.items[1], downtime: null },
        ],
      }),
    );
    renderWithSession(
      <PostActivityPage {...PAGE_PROPS} />,
      sessionCtx("identified"),
    );
    await waitFor(() =>
      expect(screen.getByText("Motivo não disponível")).toBeInTheDocument(),
    );
    expect(
      screen.queryByRole("button", { name: /motivo/i }),
    ).not.toBeInTheDocument();
  });

  it("totvs renders the controlled notice", async () => {
    stubFetch(() => ok(TOTVS));
    renderWithSession(
      <PostActivityPage {...PAGE_PROPS} />,
      sessionCtx("identified"),
    );
    await waitFor(() =>
      expect(screen.getByText(/não possui sensoriamento MES/)).toBeInTheDocument(),
    );
  });

  it("503 offers a retry", async () => {
    stubFetch(() => errEnvelope("Fonte indisponível", 503));
    renderWithSession(
      <PostActivityPage {...PAGE_PROPS} />,
      sessionCtx("identified"),
    );
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: /Tentar novamente/ }),
      ).toBeInTheDocument(),
    );
  });

  it("anonymous session shows identification guidance", () => {
    const ctx = sessionCtx("anonymous");
    renderWithSession(<PostActivityPage {...PAGE_PROPS} />, ctx);
    expect(screen.getByText(/Identifique-se para ver/)).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: "Identificar operador" }),
    );
    expect(ctx.openIdentify).toHaveBeenCalled();
  });
});
