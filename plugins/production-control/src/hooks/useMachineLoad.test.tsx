// @vitest-environment jsdom

import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { MachineLoadLiveStatusPayload, PpcBranch } from "../types";
import { makeMachineLoadPayload } from "../utils/machineLoadTestPayload";
import { useMachineLoad } from "./useMachineLoad";

const api = vi.hoisted(() => ({
  fetchMachineLoad: vi.fn(),
  fetchMachineLoadLiveStatus: vi.fn(),
  publishMachineLoad: vi.fn(),
  refreshMachineLoad: vi.fn(),
}));

vi.mock("../api/ppcApi", () => ({
  fetchMachineLoad: api.fetchMachineLoad,
  fetchMachineLoadLiveStatus: api.fetchMachineLoadLiveStatus,
  publishMachineLoad: api.publishMachineLoad,
  refreshMachineLoad: api.refreshMachineLoad,
}));

const EMPTY_LIVE_STATUS: MachineLoadLiveStatusPayload = {
  branch: "01",
  as_of: "2026-08-20T08:00:00Z",
  summary: { operation_count: 3, in_production_count: 0 },
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
  api.fetchMachineLoadLiveStatus.mockReset();
  api.publishMachineLoad.mockReset();
  api.refreshMachineLoad.mockReset();
  api.fetchMachineLoad.mockResolvedValue(makeMachineLoadPayload());
  api.fetchMachineLoadLiveStatus.mockResolvedValue(EMPTY_LIVE_STATUS);
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

  it("pede a fila com todos os centros e sem esperar o chão de fábrica", async () => {
    const { result } = renderMachineLoad();
    await waitFor(() => expect(result.current.data).not.toBeNull());

    // A fila chega primeiro; o status vivo vem de uma rota própria.
    expect(api.fetchMachineLoad).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(api.fetchMachineLoadLiveStatus).toHaveBeenCalled());
    expect(api.fetchMachineLoadLiveStatus).toHaveBeenCalledWith(
      expect.objectContaining({ branch: "01" }),
    );
  });

  it("aplica o status vivo sobre a fila sem recarregá-la", async () => {
    api.fetchMachineLoadLiveStatus.mockResolvedValue({
      ...EMPTY_LIVE_STATUS,
      summary: { operation_count: 3, in_production_count: 1 },
      items: [
        {
          production_order: "24640401002",
          operation_code: "03",
          production_status: "in_progress",
          is_in_production: true,
          active_operator_name: "SILVANA ANDRADE DOS SANTOS",
        },
      ],
    } satisfies MachineLoadLiveStatusPayload);

    const { result } = renderMachineLoad();
    await waitFor(() => expect(result.current.data).not.toBeNull());

    await waitFor(() =>
      expect(result.current.data?.selected.items[0]?.is_in_production).toBe(true),
    );
    expect(result.current.data?.selected.items[0]?.active_operator_name).toBe(
      "SILVANA ANDRADE DOS SANTOS",
    );
    expect(result.current.data?.work_centers[0].in_production_count).toBe(1);
    expect(api.fetchMachineLoad).toHaveBeenCalledTimes(1);
  });

  it("falha no status vivo não derruba a fila que já está na tela", async () => {
    api.fetchMachineLoadLiveStatus.mockRejectedValue(new Error("TOTVS indisponível"));

    const { result } = renderMachineLoad();
    await waitFor(() => expect(result.current.data).not.toBeNull());
    await waitFor(() => expect(api.fetchMachineLoadLiveStatus).toHaveBeenCalled());

    expect(result.current.error).toBeNull();
    expect(result.current.data?.selected.items).toHaveLength(2);
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
