import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@delpi/plugin-ui/index", async () => await import("../../test/pluginUiMock"));

const listMock = vi.fn();
const summaryMock = vi.fn();

vi.mock("../../api/financialSettlementsApi", () => ({
  getFinancialSettlements: (...args: unknown[]) => listMock(...args),
  getFinancialSettlementsSummary: (...args: unknown[]) => summaryMock(...args),
}));

import { ApiError } from "../../api/httpClient";
import { FinancialSettlementsPage } from "./FinancialSettlementsPage";

const ITEM = {
  settlementId: "S1",
  settlementDate: "2026-10-05",
  settlementAmount: "1250.75",
  currencyCode: "BRL",
  natureCode: "100",
  natureDescription: "Fornecedores",
  documentNumber: "9001",
  prefix: "NFE",
  installment: "01",
  documentType: "NF",
  partyCode: "F0001",
  partyStore: "01",
  partyName: "Fornecedor Exemplo",
  issueDate: "2026-09-01",
  dueDate: "2026-10-01",
  history: "Baixa",
  movementType: "BA",
  movementDescription: "Baixa de titulo",
  paymentDirection: "P",
  branchCode: null,
  branchResolution: "unresolved",
  linkStatus: "resolved",
};

function listPayload(overrides: Record<string, unknown> = {}) {
  return {
    report: "settlements_payables",
    side: "payable",
    period: { start_date: "2026-10-01", end_date: "2026-10-20" },
    status: "complete",
    officialTotals: false,
    quality: {
      missingDocumentCount: 0,
      missingNatureCount: 0,
      unresolvedBranchCount: 1,
    },
    pagination: {
      page: 1,
      page_size: 50,
      total_items: 1,
      total_pages: 1,
      has_next: false,
      has_previous: false,
    },
    sort: { sort_by: "settlement_date", sort_dir: "desc" },
    items: [ITEM],
    ...overrides,
  };
}

function summaryPayload() {
  return {
    report: "settlements_summary",
    period: { start_date: "2026-10-01", end_date: "2026-10-20" },
    status: "complete",
    officialTotals: false,
    quality: {
      missingDocumentCount: 0,
      missingNatureCount: 0,
      unresolvedBranchCount: 0,
    },
    groups: [
      {
        side: "payable",
        currencyCode: "BRL",
        natureCode: "100",
        natureDescription: "Fornecedores",
        movementType: "BA",
        movementDescription: "Baixa de titulo",
        eventCount: 3,
        totalAmount: "5000.00",
      },
      {
        side: "receivable",
        currencyCode: "USD",
        natureCode: "200",
        natureDescription: null,
        movementType: "VL",
        movementDescription: "Baixa de titulo",
        eventCount: 2,
        totalAmount: "900.00",
      },
    ],
  };
}

async function applyDefaultFilters() {
  fireEvent.change(screen.getByLabelText("Data inicial"), {
    target: { value: "2026-10-01" },
  });
  fireEvent.change(screen.getByLabelText("Data final"), {
    target: { value: "2026-10-20" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Aplicar filtros" }));
  await waitFor(() => expect(listMock).toHaveBeenCalled());
}

afterEach(() => {
  cleanup();
  listMock.mockReset();
  summaryMock.mockReset();
});

describe("FinancialSettlementsPage", () => {
  it("estado inicial pede filtros — não dispara fetch", () => {
    render(<FinancialSettlementsPage />);
    expect(
      screen.getByText(/Informe o período e aplique os filtros/),
    ).toBeTruthy();
    expect(listMock).not.toHaveBeenCalled();
  });

  it("aplica filtros e renderiza linhas + resumo por moeda", async () => {
    listMock.mockResolvedValue(listPayload());
    summaryMock.mockResolvedValue(summaryPayload());
    render(<FinancialSettlementsPage />);
    await applyDefaultFilters();

    expect(listMock).toHaveBeenCalledWith(
      expect.objectContaining({
        side: "payable",
        startDate: "2026-10-01",
        endDate: "2026-10-20",
        page: 1,
        pageSize: 50,
      }),
      expect.anything(),
    );
    expect(await screen.findByText("Fornecedor Exemplo")).toBeTruthy();
    // Valor não repete o código da moeda — moeda tem coluna própria.
    expect(screen.getByText("1.250,75")).toBeTruthy();
    expect(screen.queryByText("BRL 1.250,75")).toBeNull();
    // Filial ausente → «Não identificada» (nunca fallback 01/02).
    expect(screen.getByText("Não identificada")).toBeTruthy();
    // Tipo de movimento exibe código + descrição canônica FKB.
    expect(screen.getByText("BA — Baixa de titulo")).toBeTruthy();
    // Resumo por moeda somente do lado selecionado (BRL, não USD).
    expect(await screen.findByText("Total BRL")).toBeTruthy();
    expect(screen.queryByText("Total USD")).toBeNull();
  });

  it("alterna visão para receber e refaz a consulta", async () => {
    listMock.mockResolvedValue(listPayload({ side: "receivable" }));
    summaryMock.mockResolvedValue(summaryPayload());
    render(<FinancialSettlementsPage />);
    await applyDefaultFilters();

    fireEvent.click(screen.getByRole("button", { name: "Baixas a receber" }));
    await waitFor(() =>
      expect(listMock).toHaveBeenLastCalledWith(
        expect.objectContaining({ side: "receivable", page: 1 }),
        expect.anything(),
      ),
    );
  });

  it("paginação servidor — Próxima pede page 2", async () => {
    listMock.mockResolvedValue(
      listPayload({
        pagination: {
          page: 1,
          page_size: 50,
          total_items: 120,
          total_pages: 3,
          has_next: true,
          has_previous: false,
        },
      }),
    );
    summaryMock.mockResolvedValue(summaryPayload());
    render(<FinancialSettlementsPage />);
    await applyDefaultFilters();
    await screen.findByText("Fornecedor Exemplo");

    fireEvent.click(screen.getByRole("button", { name: "Próxima" }));
    await waitFor(() =>
      expect(listMock).toHaveBeenLastCalledWith(
        expect.objectContaining({ page: 2 }),
        expect.anything(),
      ),
    );
  });

  it("scope_unavailable rende estado próprio — não confunde com vazio nem 403 genérico", async () => {
    listMock.mockRejectedValue(
      new ApiError(403, "Escopo de dados financeiros não autorizado.", "scope_unavailable"),
    );
    summaryMock.mockRejectedValue(new ApiError(403, "x", "scope_unavailable"));
    render(<FinancialSettlementsPage />);
    await applyDefaultFilters();

    expect(await screen.findByText("Escopo de dados indisponível")).toBeTruthy();
    expect(screen.queryByText("Acesso restrito")).toBeNull();
    expect(screen.queryByText(/Nenhuma baixa encontrada/)).toBeNull();
  });

  it("403 genérico rende acesso restrito", async () => {
    listMock.mockRejectedValue(new ApiError(403, "Forbidden"));
    summaryMock.mockRejectedValue(new ApiError(403, "Forbidden"));
    render(<FinancialSettlementsPage />);
    await applyDefaultFilters();

    expect(await screen.findByText("Acesso restrito")).toBeTruthy();
  });

  it("período inválido mostra validação e não chama a API", () => {
    render(<FinancialSettlementsPage />);
    fireEvent.change(screen.getByLabelText("Data inicial"), {
      target: { value: "2026-10-20" },
    });
    fireEvent.change(screen.getByLabelText("Data final"), {
      target: { value: "2026-10-01" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Aplicar filtros" }));

    expect(screen.getByText(/Informe um período válido/)).toBeTruthy();
    expect(listMock).not.toHaveBeenCalled();
  });

  it("resultado vazio mostra mensagem de vazio da tabela", async () => {
    listMock.mockResolvedValue(listPayload({ items: [] }));
    summaryMock.mockResolvedValue(summaryPayload());
    render(<FinancialSettlementsPage />);
    await applyDefaultFilters();

    expect(
      await screen.findByText(/Nenhuma baixa encontrada/),
    ).toBeTruthy();
  });
});
