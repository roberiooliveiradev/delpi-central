import { renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { getDowntimeFilterOptions, getDowntimes } from "../api/mesApi";
import type { DowntimesQuery, DowntimesResponse, DowntimeFilterOptionsResponse } from "../types/mes";
import { useDowntimesData } from "./useDowntimesData";
import { useSelectedDowntime } from "./useSelectedDowntime";
import { useDowntimeFilterOptions } from "./useDowntimeFilterOptions";

vi.mock("../api/mesApi", () => ({
  getDowntimes: vi.fn(),
  getDowntimeFilterOptions: vi.fn(),
}));

const itemOf = (id: string) => ({
  id,
  runId: null,
  workCenter: "CT-" + id,
  productionOrder: null,
  operationCode: null,
  startedAt: "2026-02-10T10:00:00.000Z",
  endedAt: "2026-02-10T11:00:00.000Z",
  source: "system",
  reasonCode: null,
  reasonLabel: null,
  category: null,
  confirmed: false,
  note: null,
  updatedAt: null,
  confirmedAt: null,
  confirmedByType: null,
  confirmedByRef: null,
});

const pageOf = (id: string, branch = "01"): DowntimesResponse => ({
  branch,
  referenceAt: "2026-02-10T12:00:00.000Z",
  items: [itemOf(id)],
  total: 1,
  page: 1,
  pageSize: 50,
});

const reasonOf = (code: string) => ({
  code,
  label: "Motivo " + code,
  category: "processo",
  active: true,
});

const query = (branch: "01" | "02"): DowntimesQuery => ({ branch, page: 1, pageSize: 50 });

type Deferred = {
  resolve: (value: DowntimesResponse) => void;
  reject: (reason: unknown) => void;
  signal: AbortSignal;
};

function deferredQueue() {
  const calls: Deferred[] = [];
  vi.mocked(getDowntimes).mockImplementation((_q: unknown, signal?: AbortSignal) => {
    let resolve!: (v: DowntimesResponse) => void;
    let reject!: (r: unknown) => void;
    const promise = new Promise<DowntimesResponse>((res, rej) => {
      resolve = res;
      reject = rej;
    });
    calls.push({ resolve, reject, signal: signal ?? new AbortController().signal });
    return promise;
  });
  return calls;
}

beforeEach(() => vi.clearAllMocks());

describe("useDowntimesData — isolamento por identidade de consulta", () => {
  it("nunca expõe dados da filial anterior, nem por um render", async () => {
    const calls = deferredQueue();
    const { result, rerender } = renderHook(
      ({ q }: { q: DowntimesQuery }) => useDowntimesData(q),
      { initialProps: { q: query("01") } },
    );
    calls[0].resolve(pageOf("A01"));
    await waitFor(() => expect(result.current.data?.items[0]?.id).toBe("A01"));

    // troca de filial: na renderização seguinte a lista anterior já é inacessível
    rerender({ q: query("02") });
    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.loading).toBe(true);

    // a requisição anterior foi cancelada
    expect(calls[0].signal.aborted).toBe(true);

    // resposta atrasada da filial 01 não pode vazar para a filial 02
    calls[0].resolve(pageOf("STALE-01"));
    calls[1].resolve(pageOf("B02"));
    await waitFor(() => expect(result.current.data?.items[0]?.id).toBe("B02"));
    expect(result.current.data?.items[0]?.id).not.toBe("STALE-01");
  });

  it("descarta resposta obsoleta mesmo quando a troca acontece antes da resolução", async () => {
    const calls = deferredQueue();
    const { result, rerender } = renderHook(
      ({ q }: { q: DowntimesQuery }) => useDowntimesData(q),
      { initialProps: { q: query("01") } },
    );
    rerender({ q: query("02") });
    rerender({ q: query("01") });
    // três requisições emitidas; só a última (filial 01, key atual) pode aplicar
    expect(calls.length).toBe(3);
    calls[0].resolve(pageOf("STALE-FIRST-01"));
    calls[1].resolve(pageOf("STALE-02"));
    calls[2].resolve(pageOf("LATEST-01"));
    await waitFor(() => expect(result.current.data?.items[0]?.id).toBe("LATEST-01"));
  });

  it("preserva o último snapshot da mesma consulta quando o refresh falha", async () => {
    const calls = deferredQueue();
    const { result } = renderHook(() => useDowntimesData(query("01")));
    calls[0].resolve(pageOf("A01"));
    await waitFor(() => expect(result.current.data?.items[0]?.id).toBe("A01"));

    void result.current.refresh();
    await waitFor(() => expect(calls.length).toBe(2));
    calls[1].reject(new Error("falha de rede"));
    await waitFor(() => expect(result.current.error).toBe("falha de rede"));
    // snapshot da MESMA chave continua disponível (degradação consciente)
    expect(result.current.data?.items[0]?.id).toBe("A01");
  });
});

describe("useSelectedDowntime — isolamento por filial e id", () => {
  it("não apresenta o detalhe de outra filial ao trocar de branch", async () => {
    const calls = deferredQueue();
    const { result, rerender } = renderHook(
      ({ branch, id }: { branch: "01" | "02"; id: string | null }) =>
        useSelectedDowntime(branch, id),
      { initialProps: { branch: "01" as "01" | "02", id: "dt-1" } },
    );
    calls[0].resolve(pageOf("DETAIL-01"));
    await waitFor(() => expect(result.current.item?.id).toBe("DETAIL-01"));

    rerender({ branch: "02", id: "dt-1" });
    // nenhum render com o detalhe da filial anterior
    expect(result.current.item).toBeNull();
    expect(result.current.loading).toBe(true);
    expect(calls[0].signal.aborted).toBe(true);

    calls[1].resolve(pageOf("DETAIL-02"));
    await waitFor(() => expect(result.current.item?.id).toBe("DETAIL-02"));
  });

  it("não apresenta o detalhe de outro downtimeId ao trocar a seleção", async () => {
    const calls = deferredQueue();
    const { result, rerender } = renderHook(
      ({ id }: { id: string | null }) => useSelectedDowntime("01", id),
      { initialProps: { id: "dt-1" as string | null } },
    );
    calls[0].resolve(pageOf("DETAIL-A"));
    await waitFor(() => expect(result.current.item?.id).toBe("DETAIL-A"));

    rerender({ id: "dt-2" });
    expect(result.current.item).toBeNull();
    calls[1].resolve(pageOf("DETAIL-B"));
    await waitFor(() => expect(result.current.item?.id).toBe("DETAIL-B"));

    // fechar o detalhe limpa o item sem nova consulta
    rerender({ id: null });
    expect(result.current.item).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(calls.length).toBe(2);
  });
});

describe("useDowntimeFilterOptions — isolamento por filial", () => {
  it("não expõe opções de outra filial durante a troca", async () => {
    const calls: Array<{ resolve: (v: DowntimeFilterOptionsResponse) => void }> = [];
    vi.mocked(getDowntimeFilterOptions).mockImplementation(() => {
      let resolve!: (v: DowntimeFilterOptionsResponse) => void;
      const promise = new Promise<DowntimeFilterOptionsResponse>((res) => {
        resolve = res;
      });
      calls.push({ resolve });
      return promise;
    });

    const { result, rerender } = renderHook(
      ({ branch }: { branch: "01" | "02" }) => useDowntimeFilterOptions(branch),
      { initialProps: { branch: "01" as "01" | "02" } },
    );
    calls[0].resolve({ reasons: [reasonOf("M01")], sources: [{ code: "system" }] });
    await waitFor(() => expect(result.current.data?.reasons[0]?.code).toBe("M01"));

    rerender({ branch: "02" });
    expect(result.current.data).toBeNull();
    calls[1].resolve({ reasons: [reasonOf("M02")], sources: [{ code: "system" }] });
    await waitFor(() => expect(result.current.data?.reasons[0]?.code).toBe("M02"));
  });
});
