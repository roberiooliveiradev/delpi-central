// @vitest-environment jsdom

import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type {
  MachineLoadBalancesPayload,
  MachineLoadCockpitStatusPayload,
  PpcBranch,
} from "../types";
import { makeMachineLoadPayload } from "../utils/machineLoadTestPayload";
import { useMachineLoad } from "./useMachineLoad";

const api = vi.hoisted(() => ({
  fetchMachineLoad: vi.fn(),
  fetchMachineLoadCockpitStatus: vi.fn(),
  fetchMachineLoadBalances: vi.fn(),
  publishMachineLoad: vi.fn(),
  refreshMachineLoad: vi.fn(),
}));

vi.mock("../api/ppcApi", () => ({
  fetchMachineLoad: api.fetchMachineLoad,
  fetchMachineLoadCockpitStatus: api.fetchMachineLoadCockpitStatus,
  fetchMachineLoadBalances: api.fetchMachineLoadBalances,
  publishMachineLoad: api.publishMachineLoad,
  refreshMachineLoad: api.refreshMachineLoad,
}));

const EMPTY_COCKPIT_STATUS: MachineLoadCockpitStatusPayload = {
  branch: "01",
  source: "cockpit",
  as_of: "2026-08-20T08:00:00Z",
  summary: { active_runs: 0, producing: 0, stopped: 0, paused: 0, unknown: 0 },
  items: [],
};

const EMPTY_BALANCES: MachineLoadBalancesPayload = {
  branch: "01",
  as_of: "2026-08-20T08:00:00Z",
  summary: { item_count: 0 },
  items: [],
};

/** O cache da fila é do módulo: cada teste usa a sua própria janela de leitura. */
let windowSeq = 0;

function renderMachineLoad(branch: PpcBranch = "01") {
  windowSeq += 1;
  const endDate = `2026-09-${String(windowSeq).padStart(2, "0")}`;
  return renderHook(
    ({ workCenter }: { workCenter: string | null }) =>
      useMachineLoad({ branch, workCenter, startDate: null, endDate }),
    { initialProps: { workCenter: "CT-01A" as string | null } },
  );
}

beforeEach(() => {
  api.fetchMachineLoad.mockReset();
  api.fetchMachineLoadCockpitStatus.mockReset();
  api.fetchMachineLoadBalances.mockReset();
  api.publishMachineLoad.mockReset();
  api.refreshMachineLoad.mockReset();
  api.fetchMachineLoad.mockResolvedValue(makeMachineLoadPayload());
  api.fetchMachineLoadCockpitStatus.mockResolvedValue(EMPTY_COCKPIT_STATUS);
  api.fetchMachineLoadBalances.mockResolvedValue(EMPTY_BALANCES);
});

afterEach(() => {
  cleanup();
});

describe("useMachineLoad", () => {
  it("trocar de centro de trabalho não gera nova leitura da fila", async () => {
    const { result, rerender } = renderMachineLoad();
    await waitFor(() => expect(result.current.data).not.toBeNull());
    expect(api.fetchMachineLoad).toHaveBeenCalledTimes(1);

    rerender({ workCenter: "CT-02" });

    expect(api.fetchMachineLoad).toHaveBeenCalledTimes(1);
    expect(result.current.data?.selected.work_center).toBe("CT-02");
    expect(
      result.current.data?.selected.items.map((item) => item.production_order),
    ).toEqual(["24640401010"]);
  });

  it("a troca de centro nunca passa por fila vazia sem loading", async () => {
    const { result, rerender } = renderMachineLoad();
    await waitFor(() => expect(result.current.data).not.toBeNull());

    rerender({ workCenter: "CT-02" });
    expect(result.current.loading).toBe(false);
    expect(result.current.data?.selected.items.length).toBeGreaterThan(0);

    rerender({ workCenter: "CT-01A" });
    expect(result.current.loading).toBe(false);
    expect(result.current.data?.selected.items.length).toBeGreaterThan(0);
  });

  it("pede a fila e depois cockpit-status e saldos, sem esperar o chão de fábrica", async () => {
    const { result } = renderMachineLoad();
    await waitFor(() => expect(result.current.data).not.toBeNull());

    expect(api.fetchMachineLoad).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(api.fetchMachineLoadCockpitStatus).toHaveBeenCalled());
    await waitFor(() => expect(api.fetchMachineLoadBalances).toHaveBeenCalled());
    expect(api.fetchMachineLoadCockpitStatus).toHaveBeenCalledWith(
      expect.objectContaining({ branch: "01" }),
    );
    expect(api.fetchMachineLoadBalances).toHaveBeenCalledWith(
      expect.objectContaining({ branch: "01" }),
    );
  });

  it("aplica a execução do cockpit sobre a fila sem recarregá-la", async () => {
    api.fetchMachineLoadCockpitStatus.mockResolvedValue({
      ...EMPTY_COCKPIT_STATUS,
      summary: { active_runs: 1, producing: 1, stopped: 0, paused: 0, unknown: 0 },
      items: [
        {
          work_center: "CT-01A",
          production_order: "24640401002",
          operation_code: "03",
          run_status: "running",
          operational_state: "producing",
          display_status: "producing",
          integrity_status: "complete",
          started_at: "2026-08-20T07:45:00Z",
        },
      ],
    } satisfies MachineLoadCockpitStatusPayload);

    const { result } = renderMachineLoad();
    await waitFor(() => expect(result.current.data).not.toBeNull());

    await waitFor(() =>
      expect(result.current.data?.selected.items[0]?.execution_status).toBe("producing"),
    );
    expect(result.current.data?.work_centers[0].in_production_count).toBe(1);
    // A fila não é recarregada pelo polling de execução.
    expect(api.fetchMachineLoad).toHaveBeenCalledTimes(1);
  });

  it("snapshot de execução vazio limpa run anterior — sem ressurreição HZA", async () => {
    let items: MachineLoadCockpitStatusPayload["items"] = [
      {
        work_center: "CT-01A",
        production_order: "24640401002",
        operation_code: "03",
        run_status: "running",
        operational_state: "producing",
        display_status: "producing",
        integrity_status: "complete",
        started_at: "2026-08-20T07:45:00Z",
      },
    ];
    api.fetchMachineLoadCockpitStatus.mockImplementation(() =>
      Promise.resolve({ ...EMPTY_COCKPIT_STATUS, items }),
    );

    const { result } = renderMachineLoad();
    await waitFor(() =>
      expect(result.current.data?.selected.items[0]?.execution_status).toBe("producing"),
    );

    items = [];
    await act(async () => {
      document.dispatchEvent(new Event("visibilitychange"));
    });

    await waitFor(() =>
      expect(result.current.data?.selected.items[0]?.execution_status).toBeNull(),
    );
    // A flag HZA congelada no snapshot não volta a sinalizar produção.
    expect(result.current.data?.selected.items[0]?.is_in_production).toBe(false);
    expect(result.current.data?.summary.in_production_count).toBe(0);
  });

  it("aplica saldo da operação sem tocar o estado de execução", async () => {
    api.fetchMachineLoadBalances.mockResolvedValue({
      ...EMPTY_BALANCES,
      summary: { item_count: 1 },
      items: [
        {
          production_order: "24640401002",
          operation_code: "03",
          operation_produced_qty: 7.1,
          operation_pending_qty: 0,
        },
      ],
    } satisfies MachineLoadBalancesPayload);

    const { result } = renderMachineLoad();
    await waitFor(() =>
      expect(result.current.data?.selected.items[0]?.operation_pending_qty).toBe(0),
    );
    expect(result.current.data?.selected.items[0]?.execution_status).toBeNull();
  });

  it("troca de filial ignora resposta atrasada do cockpit anterior", async () => {
    const deferred: Array<() => void> = [];
    api.fetchMachineLoadCockpitStatus.mockImplementation(
      ({ branch }: { branch: string }) =>
        branch === "01"
          ? new Promise<MachineLoadCockpitStatusPayload>((resolve) =>
              deferred.push(() =>
                resolve({
                  ...EMPTY_COCKPIT_STATUS,
                  summary: {
                    active_runs: 1,
                    producing: 1,
                    stopped: 0,
                    paused: 0,
                    unknown: 0,
                  },
                  items: [
                    {
                      work_center: "CT-01A",
                      production_order: "24640401002",
                      operation_code: "03",
                      run_status: "running",
                      operational_state: "producing",
                      display_status: "producing",
                      integrity_status: "complete",
                      started_at: "2026-08-20T07:45:00Z",
                    },
                  ],
                }),
              ),
            )
          : Promise.resolve(EMPTY_COCKPIT_STATUS),
    );

    windowSeq += 1;
    const endDate = `2026-09-5${windowSeq}`;
    const { result, rerender } = renderHook(
      ({ branch }: { branch: PpcBranch }) =>
        useMachineLoad({ branch, workCenter: "CT-01A", startDate: null, endDate }),
      { initialProps: { branch: "01" as PpcBranch } },
    );
    await waitFor(() => expect(result.current.data).not.toBeNull());
    await waitFor(() =>
      expect(api.fetchMachineLoadCockpitStatus).toHaveBeenCalledTimes(1),
    );

    rerender({ branch: "02" });
    await waitFor(() => expect(result.current.data).not.toBeNull());
    await waitFor(() =>
      expect(api.fetchMachineLoadCockpitStatus).toHaveBeenCalledWith(
        expect.objectContaining({ branch: "02" }),
      ),
    );

    // A resposta da filial 01 chega depois da troca — abortada, nunca aplica.
    await act(async () => {
      deferred.forEach((resolve) => resolve());
    });

    expect(
      result.current.data?.selected.items.every(
        (item) => item.execution_status == null,
      ),
    ).toBe(true);
  });

  it("falha no cockpit-status preserva a fila e sinaliza indisponibilidade", async () => {
    api.fetchMachineLoadCockpitStatus.mockRejectedValue(new Error("cockpit fora"));

    const { result } = renderMachineLoad();
    await waitFor(() => expect(result.current.data).not.toBeNull());
    await waitFor(() => expect(result.current.executionUnavailable).toBe(true));

    expect(result.current.error).toBeNull();
    expect(result.current.data?.selected.items).toHaveLength(2);
  });

  it("recupera a leitura de execução depois de uma falha", async () => {
    api.fetchMachineLoadCockpitStatus
      .mockRejectedValueOnce(new Error("cockpit fora"))
      .mockResolvedValue(EMPTY_COCKPIT_STATUS);

    const { result } = renderMachineLoad();
    await waitFor(() => expect(result.current.data).not.toBeNull());
    await waitFor(() => expect(result.current.executionUnavailable).toBe(true));

    await act(async () => {
      document.dispatchEvent(new Event("visibilitychange"));
    });

    await waitFor(() => expect(result.current.executionUnavailable).toBe(false));
  });

  it("falha nos saldos não apaga a fila nem o estado de execução", async () => {
    api.fetchMachineLoadBalances.mockRejectedValue(new Error("api-delpi fora"));

    const { result } = renderMachineLoad();
    await waitFor(() => expect(result.current.data).not.toBeNull());
    await waitFor(() => expect(result.current.balancesUnavailable).toBe(true));

    expect(result.current.data?.selected.items).toHaveLength(2);
  });

  it("aba oculta suspende o polling de execução e saldos", async () => {
    const visibility = vi.spyOn(document, "visibilityState", "get");
    renderMachineLoad();
    await waitFor(() => expect(api.fetchMachineLoadCockpitStatus).toHaveBeenCalledTimes(1));
    const statusCalls = api.fetchMachineLoadCockpitStatus.mock.calls.length;
    const balanceCalls = api.fetchMachineLoadBalances.mock.calls.length;

    visibility.mockReturnValue("hidden");
    await act(async () => {
      document.dispatchEvent(new Event("visibilitychange"));
    });

    expect(api.fetchMachineLoadCockpitStatus.mock.calls.length).toBe(statusCalls);
    expect(api.fetchMachineLoadBalances.mock.calls.length).toBe(balanceCalls);
    visibility.mockRestore();
  });

  it("erro na fila reporta a mensagem e não inventa linhas", async () => {
    api.fetchMachineLoad.mockRejectedValue(new Error("Snapshot ausente"));

    const { result } = renderMachineLoad();

    await waitFor(() => expect(result.current.error).toBe("Snapshot ausente"));
    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
  });

  it("publish marca a fila como enviada sem rebaixar a carga máquina", async () => {
    api.fetchMachineLoad.mockResolvedValue(
      makeMachineLoadPayload({
        publication: { state: "draft", published_at: "2026-08-19T20:00:00Z", published_by: "pcp" },
      }),
    );
    api.publishMachineLoad.mockResolvedValue({
      state: "live",
      generation_id: "gen-x",
      published_at: "2026-08-20T10:30:00Z",
      published_by: "Maria",
      changed: true,
    });

    const { result } = renderMachineLoad();
    await waitFor(() => expect(result.current.data).not.toBeNull());
    expect(result.current.data?.publication?.state).toBe("draft");
    expect(api.fetchMachineLoad).toHaveBeenCalledTimes(1);

    let publication: Awaited<ReturnType<typeof result.current.publishToMachines>> | undefined;
    await act(async () => {
      publication = await result.current.publishToMachines();
    });

    expect(publication?.state).toBe("live");
    expect(api.publishMachineLoad).toHaveBeenCalledWith({ branch: "01" });
    expect(result.current.data?.publication).toEqual({
      state: "live",
      published_at: "2026-08-20T10:30:00Z",
      published_by: "Maria",
    });
    // Sem GET novo: a fila exibida continua exatamente a mesma.
    expect(api.fetchMachineLoad).toHaveBeenCalledTimes(1);
    expect(result.current.data?.selected.items).toHaveLength(2);
  });

  it("falha no publish mantém o draft e expõe o erro", async () => {
    api.fetchMachineLoad.mockResolvedValue(
      makeMachineLoadPayload({
        publication: { state: "draft", published_at: null, published_by: null },
      }),
    );
    api.publishMachineLoad.mockRejectedValue(
      new Error("Não foi possível enviar a carga máquina para as máquinas."),
    );

    const { result } = renderMachineLoad();
    await waitFor(() => expect(result.current.data).not.toBeNull());

    await act(async () => {
      await expect(result.current.publishToMachines()).rejects.toThrow();
    });

    expect(result.current.data?.publication?.state).toBe("draft");
    expect(result.current.error).toBe(
      "Não foi possível enviar a carga máquina para as máquinas.",
    );
    expect(result.current.publishing).toBe(false);
  });

  it("refresh troca o estado de publicação que veio do backend", async () => {
    api.fetchMachineLoad.mockResolvedValue(
      makeMachineLoadPayload({
        publication: { state: "live", published_at: "2026-08-19T20:00:00Z", published_by: "pcp" },
      }),
    );
    api.refreshMachineLoad.mockResolvedValue(
      makeMachineLoadPayload({
        publication: { state: "draft", published_at: "2026-08-19T20:00:00Z", published_by: "pcp" },
      }),
    );

    const { result } = renderMachineLoad();
    await waitFor(() => expect(result.current.data).not.toBeNull());
    expect(result.current.data?.publication?.state).toBe("live");

    await act(async () => {
      await result.current.refreshFromTotvs();
    });

    expect(result.current.data?.publication?.state).toBe("draft");
  });

  it("payload de mutação mantém o estado que o backend derivou", async () => {
    // LIVE → mutação continua LIVE: o publication vem no próprio payload.
    api.fetchMachineLoad.mockResolvedValue(
      makeMachineLoadPayload({
        publication: { state: "live", published_at: "2026-08-19T20:00:00Z", published_by: "pcp" },
      }),
    );

    const { result } = renderMachineLoad();
    await waitFor(() => expect(result.current.data).not.toBeNull());

    act(() => {
      result.current.applyPayload(
        makeMachineLoadPayload({
          publication: { state: "live", published_at: "2026-08-19T20:00:00Z", published_by: "pcp" },
        }),
      );
    });

    expect(result.current.data?.publication?.state).toBe("live");
  });
});
