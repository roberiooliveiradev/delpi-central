// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { LineFeederUrgentRequest } from "../types";
import { LineFeederUrgentRequestsPanel } from "./LineFeederUrgentRequestsPanel";

const listMock = vi.fn();
const patchMock = vi.fn();

vi.mock("../api/ppcApi", () => ({
  fetchLineFeederUrgentRequests: (...args: unknown[]) => listMock(...args),
  patchLineFeederUrgentRequest: (...args: unknown[]) => patchMock(...args),
}));

function makeRequest(
  partial: Partial<LineFeederUrgentRequest> = {},
): LineFeederUrgentRequest {
  return {
    id: "m-1",
    feedbackId: "fb-1",
    productionOrder: "24640401002",
    operationCode: "03",
    productCode: "10081234",
    description: "TERMINAL FASTON",
    unit: "PC",
    openQty: 120,
    status: "pending",
    feedbackStatus: "acknowledged",
    operatorCode: "001234",
    operatorName: "Maria Silva",
    note: "Falta terminal na bancada",
    reportedAt: "2026-10-01T08:00:00Z",
    reportedWorkCenter: "CT-63",
    currentWorkCenter: "CT-64",
    outOfQueue: false,
    pickedAt: null,
    deliveredAt: null,
    ...partial,
  };
}

function queueOf(items: LineFeederUrgentRequest[]) {
  const pending = items.filter((i) => i.status === "pending").length;
  return {
    items,
    summary: { total: items.length, pending, picked: items.length - pending },
  };
}

afterEach(() => {
  cleanup();
  listMock.mockReset();
  patchMock.mockReset();
});

describe("LineFeederUrgentRequestsPanel (C5)", () => {
  it("mostra contador e itens pending/picked", async () => {
    listMock.mockResolvedValue(
      queueOf([
        makeRequest({ id: "m-1" }),
        makeRequest({
          id: "m-2",
          productCode: "10085678",
          description: "FIO RIGIDO",
          status: "picked",
        }),
      ]),
    );
    render(<LineFeederUrgentRequestsPanel branch="01" />);

    expect(await screen.findByText("Solicitações urgentes (2)")).toBeTruthy();
    expect(screen.getByText("10081234")).toBeTruthy();
    expect(screen.getByText("10085678")).toBeTruthy();
    expect(screen.getByText("Aguardando separação")).toBeTruthy();
    expect(screen.getByText("Em separação")).toBeTruthy();
    // CT atual divergente do reportado (os dois itens compartilham os CTs)
    expect(screen.getAllByText("Destino atual CT-64")).toHaveLength(2);
    expect(screen.getAllByText("Reportado no CT-63")).toHaveLength(2);
  });

  it("lista vazia mostra estado limpo", async () => {
    listMock.mockResolvedValue(queueOf([]));
    render(<LineFeederUrgentRequestsPanel branch="01" />);
    expect(
      await screen.findByText("Nenhuma solicitação urgente nesta filial."),
    ).toBeTruthy();
  });

  it("OP fora da fila continua visível com marcador", async () => {
    listMock.mockResolvedValue(
      queueOf([makeRequest({ outOfQueue: true, currentWorkCenter: null })]),
    );
    render(<LineFeederUrgentRequestsPanel branch="01" />);
    expect(await screen.findByText("OP fora da fila atual")).toBeTruthy();
    expect(screen.getByText("10081234")).toBeTruthy();
  });

  it("Iniciar separação chama PATCH picked e recarrega", async () => {
    listMock
      .mockResolvedValueOnce(queueOf([makeRequest()]))
      .mockResolvedValueOnce(queueOf([makeRequest({ status: "picked" })]));
    patchMock.mockResolvedValue(makeRequest({ status: "picked" }));
    render(<LineFeederUrgentRequestsPanel branch="01" />);

    fireEvent.click(await screen.findByText("Iniciar separação"));
    await waitFor(() => expect(patchMock).toHaveBeenCalledTimes(1));
    expect(patchMock).toHaveBeenCalledWith({
      branch: "01",
      materialId: "m-1",
      status: "picked",
    });
    await waitFor(() => expect(listMock).toHaveBeenCalledTimes(2));
    expect(await screen.findByText("Em separação")).toBeTruthy();
  });

  it("Marcar como entregue chama PATCH delivered e item sai da fila", async () => {
    listMock
      .mockResolvedValueOnce(queueOf([makeRequest({ status: "picked" })]))
      .mockResolvedValueOnce(queueOf([]));
    patchMock.mockResolvedValue(makeRequest({ status: "delivered" }));
    render(<LineFeederUrgentRequestsPanel branch="01" />);

    fireEvent.click(await screen.findByText("Marcar como entregue"));
    await waitFor(() => expect(patchMock).toHaveBeenCalledTimes(1));
    expect(patchMock).toHaveBeenCalledWith({
      branch: "01",
      materialId: "m-1",
      status: "delivered",
    });
    expect(
      await screen.findByText("Nenhuma solicitação urgente nesta filial."),
    ).toBeTruthy();
  });

  it("erro da API mostra mensagem amigável", async () => {
    listMock.mockRejectedValue(new Error("falhou"));
    render(<LineFeederUrgentRequestsPanel branch="01" />);
    expect(await screen.findByRole("alert")).toBeTruthy();
  });
});
