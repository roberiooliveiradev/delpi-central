/** @vitest-environment jsdom */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { BenchSessionSnapshot } from "./api.ts";
import { CockpitActivityProvider } from "./CockpitActivityProvider.tsx";
import { MesShiftMetrics } from "./cockpitShared.tsx";
import {
  OperatorSessionContext,
  type OperatorSessionContextValue,
} from "./OperatorSessionContext.ts";

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
  items: [],
};

function ok(data: unknown, status = 200): Response {
  return new Response(JSON.stringify({ success: true, data }), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function stubFetch(
  handler: (url: string, init?: RequestInit) => Response | Promise<Response>,
) {
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
      <CockpitActivityProvider
        token="tok"
        branch="02"
        workCenter="CT-63"
        runRealtimeEvent={null}
        realtimeConnected
      >
        {ui}
      </CockpitActivityProvider>
    </OperatorSessionContext.Provider>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("MesShiftMetrics — cabeçalho híbrido do posto sensorizado", () => {
  it("shows ERP efficiency/produced and MES stops on the same row", async () => {
    stubFetch(() => ok(TODAY));
    const onOpenPerformance = vi.fn();
    const onOpenActivity = vi.fn();
    renderWithSession(
      <MesShiftMetrics
        shiftLabel="Turno A"
        shiftPct={85}
        shiftProducedQty={0.12}
        onOpenPerformance={onOpenPerformance}
        onOpenActivity={onOpenActivity}
      />,
      sessionCtx("identified"),
    );

    // TOTVS: eficiência e produzido do turno voltam ao cabeçalho.
    expect(screen.getByText("Turno A")).toBeTruthy();
    expect(screen.getByText("85%")).toBeTruthy();
    expect(screen.getByText("Produzido · turno")).toBeTruthy();

    // MES: paradas medidas pelo sensor, com pendência de classificação.
    await waitFor(() => expect(screen.getByText("00:30:00")).toBeTruthy());
    expect(screen.getByText("· 1!")).toBeTruthy();

    fireEvent.click(screen.getByText("Paradas · hoje"));
    expect(onOpenActivity).toHaveBeenCalledTimes(1);
    expect(onOpenPerformance).not.toHaveBeenCalled();

    fireEvent.click(screen.getByText("Turno A"));
    expect(onOpenPerformance).toHaveBeenCalledTimes(1);
  });

  it("keeps ERP tiles but shows — for stops when there is no session", async () => {
    stubFetch(() => ok(TODAY));
    renderWithSession(
      <MesShiftMetrics
        shiftLabel="Turno B"
        shiftPct={95}
        shiftProducedQty={null}
        onOpenPerformance={vi.fn()}
        onOpenActivity={vi.fn()}
      />,
      sessionCtx("anonymous"),
    );

    expect(screen.getByText("95%")).toBeTruthy();
    expect(screen.getByText("Paradas · hoje")).toBeTruthy();
    const stopTile = screen.getByText("Paradas · hoje").closest("button");
    expect(stopTile?.textContent).toContain("—");
  });
});
