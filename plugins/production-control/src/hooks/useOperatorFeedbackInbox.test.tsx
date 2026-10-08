// @vitest-environment jsdom

import { act, cleanup, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { PcpOperatorFeedback } from "../types";
import { HttpRequestError } from "../api/httpClient";
import { useOperatorFeedbackInbox, INBOX_POLL_MS } from "./useOperatorFeedbackInbox";

(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

const api = vi.hoisted(() => ({
  fetchOperatorFeedbackInbox: vi.fn(),
  acknowledgeOperatorFeedback: vi.fn(),
  resolveOperatorFeedback: vi.fn(),
}));

vi.mock("../api/ppcApi", () => ({
  fetchOperatorFeedbackInbox: api.fetchOperatorFeedbackInbox,
  acknowledgeOperatorFeedback: api.acknowledgeOperatorFeedback,
  resolveOperatorFeedback: api.resolveOperatorFeedback,
}));

function makeFeedback(partial: Partial<PcpOperatorFeedback> = {}): PcpOperatorFeedback {
  return {
    id: "fb-1",
    branch: "01",
    productionOrder: "24640401002",
    operationCode: "03",
    reportedWorkCenter: "CT-63",
    feedbackType: "cannot_produce",
    reasonCode: "missing_material",
    note: null,
    status: "open",
    operatorCode: "001234",
    operatorName: "Maria",
    productCode: null,
    productDescription: null,
    paProductCode: null,
    dueDate: null,
    createdAt: "2026-10-01T08:00:00Z",
    acknowledgedAt: null,
    acknowledgedBy: null,
    ...partial,
  };
}

function inbox(items: PcpOperatorFeedback[]) {
  return {
    items,
    summary: {
      total: items.length,
      open: items.filter((i) => i.status === "open").length,
      acknowledged: items.filter((i) => i.status === "acknowledged").length,
    },
  };
}

beforeEach(() => {
  api.fetchOperatorFeedbackInbox.mockReset();
  api.acknowledgeOperatorFeedback.mockReset();
  api.resolveOperatorFeedback.mockReset();
});

afterEach(() => {
  cleanup();
});

describe("useOperatorFeedbackInbox", () => {
  it("carrega ativos da filial uma unica vez no mount (sem N+1)", async () => {
    api.fetchOperatorFeedbackInbox.mockResolvedValue(inbox([makeFeedback()]));
    const { result } = renderHook(() => useOperatorFeedbackInbox("01"));

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(api.fetchOperatorFeedbackInbox).toHaveBeenCalledTimes(1);
    expect(api.fetchOperatorFeedbackInbox).toHaveBeenCalledWith(
      expect.objectContaining({ branch: "01" }),
    );
    expect(result.current.items).toHaveLength(1);
    expect(result.current.summary.open).toBe(1);
  });

  it("polling leve revalida a inbox sem requests por linha", async () => {
    api.fetchOperatorFeedbackInbox.mockResolvedValue(inbox([]));
    const setSpy = vi.spyOn(window, "setInterval");

    renderHook(() => useOperatorFeedbackInbox("01"));
    await waitFor(() => expect(api.fetchOperatorFeedbackInbox).toHaveBeenCalledTimes(1));
    const timerCalls = setSpy.mock.calls.filter(
      (call) => call[1] === INBOX_POLL_MS,
    );
    expect(timerCalls).toHaveLength(1);
    const poll = timerCalls[0][0] as () => void;

    await act(async () => {
      poll();
    });
    expect(api.fetchOperatorFeedbackInbox).toHaveBeenCalledTimes(2);
    await act(async () => {
      poll();
      poll();
    });
    expect(api.fetchOperatorFeedbackInbox).toHaveBeenCalledTimes(4);
    setSpy.mockRestore();
  });

  it("o intervalo usa o budget leve da inbox", () => {
    expect(INBOX_POLL_MS).toBeGreaterThanOrEqual(15_000);
  });

  it("acknowledge chama a API e revalida", async () => {
    const open = makeFeedback();
    api.fetchOperatorFeedbackInbox
      .mockResolvedValueOnce(inbox([open]))
      .mockResolvedValueOnce(inbox([makeFeedback({ status: "acknowledged" })]));
    api.acknowledgeOperatorFeedback.mockResolvedValue(
      makeFeedback({ status: "acknowledged" }),
    );

    const { result } = renderHook(() => useOperatorFeedbackInbox("01"));
    await waitFor(() => expect(result.current.items).toHaveLength(1));

    let done: boolean | undefined;
    await act(async () => {
      done = await result.current.acknowledge("fb-1");
    });
    expect(done).toBe(true);
    expect(api.acknowledgeOperatorFeedback).toHaveBeenCalledWith(
      expect.objectContaining({ feedbackId: "fb-1" }),
    );
    expect(result.current.items[0].status).toBe("acknowledged");
  });

  it("resolve remove o item dos ativos", async () => {
    api.fetchOperatorFeedbackInbox
      .mockResolvedValueOnce(inbox([makeFeedback()]))
      .mockResolvedValueOnce(inbox([]));
    api.resolveOperatorFeedback.mockResolvedValue(
      makeFeedback({ status: "resolved" }),
    );

    const { result } = renderHook(() => useOperatorFeedbackInbox("01"));
    await waitFor(() => expect(result.current.items).toHaveLength(1));

    await act(async () => {
      await result.current.resolve("fb-1", "Material disponibilizado.");
    });
    expect(api.resolveOperatorFeedback).toHaveBeenCalledWith(
      expect.objectContaining({
        feedbackId: "fb-1",
        resolutionNote: "Material disponibilizado.",
      }),
    );
    expect(result.current.items).toHaveLength(0);
    expect(result.current.summary.total).toBe(0);
  });

  it("409 de concorrencia vira aviso amigavel e revalida a lista", async () => {
    api.fetchOperatorFeedbackInbox
      .mockResolvedValueOnce(inbox([makeFeedback()]))
      .mockResolvedValueOnce(
        inbox([makeFeedback({ status: "acknowledged", acknowledgedBy: "outra.pessoa" })]),
      );
    api.acknowledgeOperatorFeedback.mockRejectedValue(
      new HttpRequestError("Transição inválida", 409),
    );

    const { result } = renderHook(() => useOperatorFeedbackInbox("01"));
    await waitFor(() => expect(result.current.items).toHaveLength(1));

    await act(async () => {
      await result.current.acknowledge("fb-1");
    });
    expect(result.current.notice).toContain("sincronizada");
    expect(result.current.items[0].status).toBe("acknowledged");
  });

  it("erro generico expõe mensagem sem derrubar a lista", async () => {
    api.fetchOperatorFeedbackInbox.mockResolvedValue(inbox([makeFeedback()]));
    api.acknowledgeOperatorFeedback.mockRejectedValue(new Error("falhou"));

    const { result } = renderHook(() => useOperatorFeedbackInbox("01"));
    await waitFor(() => expect(result.current.items).toHaveLength(1));

    let done: boolean | undefined;
    await act(async () => {
      done = await result.current.acknowledge("fb-1");
    });
    expect(done).toBe(false);
    expect(result.current.notice).toBe("falhou");
    expect(result.current.items).toHaveLength(1);
  });
});
