import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { useState } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { DowntimesRouteParams } from "../hooks/useDelpiMesRoute";
import type { DowntimeItem } from "../types/mes";
import { DowntimesPage } from "./DowntimesPage";

function analyticsSection(): HTMLElement {
  const section = document.querySelector("section.delpi-mes-analytics");
  if (!section) {
    throw new Error("analytics section not rendered");
  }
  return section as HTMLElement;
}

const DEFAULT_PARAMS: DowntimesRouteParams = {
  period: "7d",
  from: null,
  to: null,
  workCenter: null,
  reasonCode: null,
  source: null,
  classification: null,
  sort: "recent",
  downtimeId: null,
  page: 1,
  pageSize: 50,
};

const downtime = (overrides: Partial<DowntimeItem> = {}): DowntimeItem => ({
  id: "1",
  runId: "run-1",
  workCenter: "CT-35",
  productionOrder: "OP-100",
  operationCode: "010",
  startedAt: "2026-02-10T10:00:00.000Z",
  endedAt: "2026-02-10T11:00:00.000Z",
  source: "operator_pause",
  reasonCode: "SETUP",
  reasonLabel: "Preparação de máquina",
  category: "setup",
  confirmed: true,
  note: null,
  ...overrides,
});

const LIST = {
  branch: "01",
  referenceAt: "2026-02-10T12:00:00.000Z",
  page: 1,
  pageSize: 50,
  total: 120,
  items: [
    downtime(),
    downtime({
      id: "2",
      runId: null,
      workCenter: "CT-41",
      productionOrder: null,
      operationCode: null,
      startedAt: "2026-02-10T08:00:00.000Z",
      endedAt: null,
      source: "system",
      reasonCode: null,
      reasonLabel: null,
      confirmed: false,
    }),
  ],
};

const ANALYTICS = {
  branch: "01",
  from: "2026-02-04T03:00:00.000Z",
  to: "2026-02-10T12:00:00.000Z",
  referenceAt: "2026-02-10T12:00:00.000Z",
  timezone: "America/Sao_Paulo",
  appliedFilters: {
    workCenter: null, reasonCode: null, source: null, classification: null,
  },
  summary: {
    totalStoppedSeconds: 10800,
    attributedSeconds: 10800,
    occurrencesCount: 3,
    averageOccurrenceSeconds: 3600,
    pendingCount: 1,
    openCount: 1,
  },
  byReason: [
    {
      key: "SETUP", reasonCode: "SETUP", label: "Preparação de máquina",
      seconds: 7200, occurrencesCount: 2, pendingCount: 0,
      percentOfAttributed: 66.67, cumulativePercent: 66.67,
    },
    {
      key: "pending", reasonCode: null, label: "Pendente de classificação",
      seconds: 3600, occurrencesCount: 1, pendingCount: 1,
      percentOfAttributed: 33.33, cumulativePercent: 100,
    },
  ],
  byWorkCenter: [
    { workCenter: "CT-35", seconds: 7200, occurrencesCount: 2, averageSeconds: 3600, percentOfTotal: 66.67 },
    { workCenter: "CT-41", seconds: 3600, occurrencesCount: 1, averageSeconds: 3600, percentOfTotal: 33.33 },
  ],
  byDay: [
    { date: "2026-02-09", weekday: 0, seconds: 3600, occurrencesCount: 1 },
    { date: "2026-02-10", weekday: 1, seconds: 7200, occurrencesCount: 2 },
  ],
  byWeekdayHour: [
    { weekday: 0, weekdayLabel: "seg", hour: 10, seconds: 3600, occurrencesCount: 1 },
  ],
  quality: { overlapDetected: false, overlapSeconds: 0, partial: false, factsCapped: false },
};

const OPTIONS = {
  reasons: [
    { code: "SETUP", label: "Preparação de máquina", category: "setup", active: true },
    { code: "OLD_REASON", label: "Motivo legado", category: "other", active: false },
  ],
  sources: [{ code: "operator_pause" }, { code: "system" }],
};

const envelope = (data: unknown, status = 200) =>
  new Response(JSON.stringify({ success: status < 400, message: "OK", data }), {
    status,
    headers: { "content-type": "application/json" },
  });

function fetchRouter() {
  return vi.fn().mockImplementation((url: string) => {
    if (url.includes("/downtimes/analytics")) {
      return Promise.resolve(envelope(ANALYTICS));
    }
    if (url.includes("/downtimes/filter-options")) {
      return Promise.resolve(envelope(OPTIONS));
    }
    if (url.includes("downtimeId=")) {
      return Promise.resolve(
        envelope({ ...LIST, total: 1, items: [LIST.items[1]], pageSize: 1 }),
      );
    }
    if (url.includes("/downtimes?")) {
      return Promise.resolve(envelope(LIST));
    }
    if (url.includes("/timeline")) {
      return Promise.resolve(envelope({ workCenter: "CT-41", items: [] }));
    }
    return Promise.reject(new Error("unexpected url " + url));
  });
}

function renderPage(initial: Partial<DowntimesRouteParams> = {}, permissions = { history: true, monitoring: true }) {
  const onOpenMonitoring = vi.fn();
  function Wrapper() {
    const [params, setParams] = useState<DowntimesRouteParams>({ ...DEFAULT_PARAMS, ...initial });
    return (
      <DowntimesPage
        branch="01"
        params={params}
        onParamsChange={setParams}
        canViewHistory={permissions.history}
        canViewMonitoring={permissions.monitoring}
        onOpenMonitoring={onOpenMonitoring}
      />
    );
  }
  render(<Wrapper />);
  return { onOpenMonitoring };
}

describe("DowntimesPage", () => {
  let fetchMock: ReturnType<typeof fetchRouter>;
  beforeEach(() => {
    fetchMock = fetchRouter();
    vi.stubGlobal("fetch", fetchMock);
  });
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("renders real downtime events including autonomous stops without a production order", async () => {
    renderPage();
    await screen.findByText("OP-100 / 010");
    expect(screen.getByText("Sem OP vinculada")).toBeTruthy();
    expect(screen.getAllByText("CT-41").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Encerrada")).toBeTruthy();
    expect(screen.getAllByText("Confirmada").length).toBeGreaterThan(0);
    expect(screen.getByText("Aberta")).toBeTruthy();
    expect(screen.getByText("Pendente")).toBeTruthy();
    expect(screen.getByText("Em aberto")).toBeTruthy();
    expect(screen.getAllByText("Preparação de máquina").length).toBeGreaterThan(0);
  });

  it("sends branch, period and pagination to the backend on first load", async () => {
    renderPage();
    await screen.findByText("OP-100 / 010");
    const listCall = fetchMock.mock.calls.find(([url]) => (url as string).includes("/downtimes?"));
    const url = listCall?.[0] as string;
    expect(url).toContain("branch=01");
    expect(url).toContain("page=1");
    expect(url).toContain("pageSize=50");
    expect(url).toContain("from=");
    expect(url).not.toContain("downtimeId=");
  });

  it("applies a filter by resetting to the first page and re-querying the backend", async () => {
    renderPage({ page: 3 });
    await screen.findByText("OP-100 / 010");
    const selects = screen.getAllByRole("combobox");
    const classification = selects.find((el) =>
      Array.from((el as HTMLSelectElement).options).some((o) => o.value === "pending"),
    );
    expect(classification).toBeTruthy();
    fireEvent.change(classification!, { target: { value: "pending" } });
    await waitFor(() => {
      const calls = fetchMock.mock.calls.map(([url]) => url as string);
      expect(
        calls.some((url) => url.includes("classification=pending") && url.includes("page=1")),
      ).toBe(true);
    });
  });

  it("clears filters through the canonical clear-filters control", async () => {
    renderPage({ reasonCode: "SETUP", sort: "oldest" });
    await screen.findByText("OP-100 / 010");
    const clear = screen.getAllByRole("button", { name: "Limpar filtros" })[0];
    fireEvent.click(clear);
    await waitFor(() => {
      const last = fetchMock.mock.calls.map(([url]) => url as string).filter(
        (url) => url.includes("/downtimes?") && !url.includes("downtimeId="),
      );
      const url = last[last.length - 1];
      expect(url).not.toContain("reasonCode=");
      expect(url).not.toContain("sort=oldest");
      expect(url).toContain("page=1");
    });
  });

  it("navigates pages through backend pagination", async () => {
    renderPage();
    await screen.findByText("OP-100 / 010");
    fireEvent.click(screen.getByRole("button", { name: "Próxima" }));
    await waitFor(() => {
      const calls = fetchMock.mock.calls.map(([url]) => url as string);
      expect(calls.some((url) => url.includes("page=2"))).toBe(true);
    });
  });

  it("opens the read-only detail via a scoped downtimeId query, not by filtering the list", async () => {
    renderPage({ downtimeId: "2" });
    await screen.findByText("Detalhe da parada");
    const detailCall = fetchMock.mock.calls.find(([url]) =>
      (url as string).includes("downtimeId=2"),
    );
    expect(detailCall?.[0]).toContain("branch=01");
    await screen.findByText("Identificador");
    expect(screen.getAllByText("2").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Sistema").length).toBeGreaterThan(0);
    const statusTerm = screen.getAllByText("Situação").find((el) => el.tagName === "DT");
    expect(statusTerm?.parentElement?.textContent).toContain("Aberta · Pendente");
    expect(screen.queryByText("Editar")).toBeNull();
  });

  it("offers the day timeline only to users with the history permission", async () => {
    const { onOpenMonitoring } = renderPage({ downtimeId: "2" }, { history: false, monitoring: true });
    await screen.findByText("Detalhe da parada");
    expect(screen.getByText("A linha do tempo do dia exige a permissão de Histórico.")).toBeTruthy();
    expect(screen.queryByText("Ver linha do tempo do dia")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Abrir no monitoramento" }));
    expect(onOpenMonitoring).toHaveBeenCalledWith("CT-41");
  });

  it("loads the day timeline on demand for authorized users", async () => {
    renderPage({ downtimeId: "2" });
    await screen.findByText("Detalhe da parada");
    fireEvent.click(screen.getByRole("button", { name: "Ver linha do tempo do dia" }));
    await waitFor(() => {
      expect(
        fetchMock.mock.calls.some(([url]) => (url as string).includes("/timeline")),
      ).toBe(true);
    });
    const timelineCall = fetchMock.mock.calls.find(([url]) =>
      (url as string).includes("/timeline"),
    );
    expect(timelineCall?.[0]).toContain("/work-centers/CT-41/timeline");
    expect(timelineCall?.[0]).toContain("branch=01");
    await screen.findByText("Nenhum estado registrado neste dia.");
  });

  it("shows the empty state for a period without downtime", async () => {
    fetchMock.mockImplementation((url: string) => {
      if ((url as string).includes("/downtimes/filter-options")) {
        return Promise.resolve(envelope(OPTIONS));
      }
      if ((url as string).includes("/downtimes/analytics")) {
        return Promise.resolve(envelope(ANALYTICS));
      }
      return Promise.resolve(envelope({ ...LIST, items: [], total: 0 }));
    });
    renderPage();
    await screen.findByText("Nenhuma parada registrada no período");
  });

  it("shows the filtered-empty state and keeps the list query untouched by downtimeId", async () => {
    fetchMock.mockImplementation((url: string) => {
      if ((url as string).includes("/downtimes/filter-options")) {
        return Promise.resolve(envelope(OPTIONS));
      }
      if ((url as string).includes("/downtimes/analytics")) {
        return Promise.resolve(envelope(ANALYTICS));
      }
      return Promise.resolve(envelope({ ...LIST, items: [], total: 0 }));
    });
    renderPage({ reasonCode: "SETUP" });
    await screen.findByText("Nenhuma parada corresponde aos filtros");
  });

  it("shows a recoverable error state when the API is unavailable", async () => {
    fetchMock.mockImplementation((url: string) => {
      if ((url as string).includes("/downtimes/filter-options")) {
        return Promise.resolve(envelope(OPTIONS));
      }
      return Promise.resolve(new Response(JSON.stringify({ success: false, message: "Serviço indisponível", data: null }), { status: 503, headers: { "content-type": "application/json" } }));
    });
    renderPage();
    await screen.findByText("Não foi possível carregar as paradas");
    expect(screen.getByRole("button", { name: "Tentar novamente" })).toBeTruthy();
  });

  it("renders backend-computed indicators and analytics groups above the list", async () => {
    renderPage();
    await screen.findByText("OP-100 / 010");
    await screen.findByText("Indicadores do período");
    const scope = within(analyticsSection());
    // KPIs calculados pelo backend (nunca apenas pela página atual)
    expect(scope.getByText("Tempo total parado")).toBeTruthy();
    expect(scope.getByText("3h 00min")).toBeTruthy();
    expect(scope.getByText("Duração média")).toBeTruthy();
    expect(scope.getByText("Pendentes de classificação")).toBeTruthy();
    expect(scope.getByText("Em aberto agora")).toBeTruthy();
    // grupos: Pareto com código + descrição e pendências identificáveis
    expect(scope.getByText("SETUP — Preparação de máquina")).toBeTruthy();
    expect(scope.getByText("Pendente de classificação")).toBeTruthy();
    // a consulta analítica não carrega paginação/ordenação/detalhe
    const analyticsCall = fetchMock.mock.calls.find(([url]) =>
      (url as string).includes("/downtimes/analytics"),
    );
    const url = analyticsCall?.[0] as string;
    expect(url).toContain("branch=01");
    expect(url).toContain("from=");
    expect(url).not.toContain("page=");
    expect(url).not.toContain("sort=");
    expect(url).not.toContain("downtimeId=");
  });

  it("drills down from the reason Pareto into the existing list filters", async () => {
    renderPage();
    await screen.findByText("SETUP — Preparação de máquina");
    fireEvent.click(
      within(analyticsSection()).getByText("SETUP — Preparação de máquina"),
    );
    await waitFor(() => {
      const calls = fetchMock.mock.calls.map(([url]) => url as string);
      expect(
        calls.some(
          (url) => url.includes("/downtimes?") && url.includes("reasonCode=SETUP"),
        ),
      ).toBe(true);
      // analytics da nova consulta reflete o mesmo universo filtrado
      expect(
        calls.some(
          (url) =>
            url.includes("/downtimes/analytics") && url.includes("reasonCode=SETUP"),
        ),
      ).toBe(true);
    });
  });

  it("drills the pending group via classification=pending, not a fake reason code", async () => {
    renderPage();
    // a página inteira entra em loading até a primeira resposta da lista
    await screen.findByText("Indicadores do período");
    await within(analyticsSection()).findByText("Pendente de classificação");
    fireEvent.click(
      within(analyticsSection()).getByText("Pendente de classificação"),
    );
    await waitFor(() => {
      const calls = fetchMock.mock.calls.map(([url]) => url as string);
      expect(
        calls.some(
          (url) =>
            url.includes("/downtimes?") &&
            url.includes("classification=pending") &&
            !url.includes("reasonCode="),
        ),
      ).toBe(true);
    });
  });

  it("drills down from the work-center ranking into the CT filter", async () => {
    renderPage();
    await screen.findByText("Indicadores do período");
    const scope = within(analyticsSection());
    await scope.findByText("Pendente de classificação");
    const ctLabel = scope.getByText("CT-41");
    const clickable = ctLabel.closest("button") ?? ctLabel;
    fireEvent.click(clickable);
    await waitFor(() => {
      const calls = fetchMock.mock.calls.map(([url]) => url as string);
      expect(
        calls.some(
          (url) => url.includes("/downtimes?") && url.includes("workCenter=CT-41"),
        ),
      ).toBe(true);
    });
  });

  it("drills a day chip into a custom single-day period filter", async () => {
    renderPage();
    await screen.findByText("Indicadores do período");
    const chip = await within(analyticsSection()).findByTitle(/de 10\/02/);
    fireEvent.click(chip);
    await waitFor(() => {
      const calls = fetchMock.mock.calls.map(([url]) => url as string);
      expect(
        calls.some(
          (url) =>
            url.includes("/downtimes?") &&
            url.includes("from=2026-02-10") &&
            url.includes("to=2026-02-11"),
        ),
      ).toBe(true);
    });
  });

  it("keeps the list working when the analytics request fails", async () => {
    fetchMock.mockImplementation((url: string) => {
      if ((url as string).includes("/downtimes/analytics")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({ success: false, message: "agregação indisponível", data: null }),
            { status: 503, headers: { "content-type": "application/json" } },
          ),
        );
      }
      if ((url as string).includes("/downtimes/filter-options")) {
        return Promise.resolve(envelope(OPTIONS));
      }
      if ((url as string).includes("/downtimes?")) {
        return Promise.resolve(envelope(LIST));
      }
      return Promise.reject(new Error("unexpected url " + url));
    });
    renderPage();
    // a listagem da Etapa 1 segue funcionando normalmente
    await screen.findByText("OP-100 / 010");
    await screen.findByText(/Não foi possível calcular os indicadores/);
  });
});

