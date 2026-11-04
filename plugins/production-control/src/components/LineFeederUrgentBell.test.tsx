// @vitest-environment jsdom

import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { LineFeederUrgentRequest } from "../types";
import { LineFeederUrgentBell } from "./LineFeederUrgentBell";

const listMock = vi.fn();
const patchMock = vi.fn();

vi.mock("../api/ppcApi", () => ({
  fetchLineFeederUrgentRequests: (...args: unknown[]) => listMock(...args),
  patchLineFeederUrgentRequest: (...args: unknown[]) => patchMock(...args),
}));

vi.mock("@delpi/plugin-ui/index", () => ({
  AnchoredPanelPortal: ({
    open,
    children,
    "aria-label": ariaLabel,
  }: {
    open: boolean;
    children: React.ReactNode;
    "aria-label"?: string;
  }) =>
    open ? (
      <div role="dialog" aria-label={ariaLabel}>
        {children}
      </div>
    ) : null,
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

async function openBell() {
  fireEvent.click(await screen.findByRole("button", { name: /solicita/i }));
}

afterEach(() => {
  cleanup();
  listMock.mockReset();
  patchMock.mockReset();
});

describe("LineFeederUrgentBell (C5)", () => {
  it("mostra badge no sino e lista materiais no popover", async () => {
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
    render(<LineFeederUrgentBell branch="01" />);

    expect(await screen.findByRole("button", { name: /2 solicitações urgentes/i })).toBeTruthy();
    expect(screen.getByText("2")).toBeTruthy();

    await openBell();
    expect(screen.getByRole("dialog", { name: /Urgentes/i })).toBeTruthy();
    expect(screen.getByText("10081234")).toBeTruthy();
    expect(screen.getByText("10085678")).toBeTruthy();
    expect(screen.getByText("Aguardando")).toBeTruthy();
    expect(screen.getByText("Em separação")).toBeTruthy();
    expect(screen.getAllByText("Destino atual CT-64")).toHaveLength(2);
    expect(screen.getAllByText("Reportado no CT-63")).toHaveLength(2);
  });

  it("lista vazia mostra estado limpo no popover", async () => {
    listMock.mockResolvedValue(queueOf([]));
    render(<LineFeederUrgentBell branch="01" />);
    expect(await screen.findByRole("button", { name: /^Solicitações urgentes$/i })).toBeTruthy();
    await openBell();
    expect(
      await screen.findByText("Nenhuma solicitação urgente nesta filial."),
    ).toBeTruthy();
  });

  it("OP fora da fila continua visível com marcador", async () => {
    listMock.mockResolvedValue(
      queueOf([makeRequest({ outOfQueue: true, currentWorkCenter: null })]),
    );
    render(<LineFeederUrgentBell branch="01" />);
    await openBell();
    expect(await screen.findByText("OP fora da fila atual")).toBeTruthy();
    expect(screen.getByText("10081234")).toBeTruthy();
  });

  it("Separar chama PATCH picked e recarrega", async () => {
    listMock
      .mockResolvedValueOnce(queueOf([makeRequest()]))
      .mockResolvedValueOnce(queueOf([makeRequest({ status: "picked" })]));
    patchMock.mockResolvedValue(makeRequest({ status: "picked" }));
    render(<LineFeederUrgentBell branch="01" />);

    await openBell();
    fireEvent.click(await screen.findByText("Separar"));
    await waitFor(() => expect(patchMock).toHaveBeenCalledTimes(1));
    expect(patchMock).toHaveBeenCalledWith({
      branch: "01",
      materialId: "m-1",
      status: "picked",
    });
    await waitFor(() => expect(listMock).toHaveBeenCalledTimes(2));
    expect(await screen.findByText("Em separação")).toBeTruthy();
  });

  it("Entregar chama PATCH delivered e item sai da fila", async () => {
    listMock
      .mockResolvedValueOnce(queueOf([makeRequest({ status: "picked" })]))
      .mockResolvedValueOnce(queueOf([]));
    patchMock.mockResolvedValue(makeRequest({ status: "delivered" }));
    render(<LineFeederUrgentBell branch="01" />);

    await openBell();
    fireEvent.click(await screen.findByText("Entregar"));
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
    render(<LineFeederUrgentBell branch="01" />);
    await openBell();
    expect(await screen.findByRole("alert")).toBeTruthy();
  });
});
