import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
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

function mockOk() {
  listMock.mockResolvedValue(listPayload());
  summaryMock.mockResolvedValue(summaryPayload());
}

async function waitInitialFetch() {
  await waitFor(() => expect(listMock).toHaveBeenCalledTimes(1));
}

afterEach(() => {
  cleanup();
  listMock.mockReset();
  summaryMock.mockReset();
  vi.useRealTimers();
});

describe("FinancialSettlementsPage — consulta automática", () => {
  it("consulta inicial automática com os filtros padrão válidos", async () => {
    mockOk();
    render(<FinancialSettlementsPage />);

    await waitInitialFetch();
    expect(listMock).toHaveBeenCalledWith(
      expect.objectContaining({ side: "payable", page: 1, pageSize: 50 }),
      expect.anything(),
    );
    expect(
      screen.queryByRole("button", { name: "Aplicar filtros" }),
    ).toBeNull();
    expect(screen.queryByRole("button", { name: "Consultar" })).toBeNull();
  });

  it("alterar período atualiza a consulta sem clicar em botão", async () => {
    mockOk();
    render(<FinancialSettlementsPage />);
    await waitInitialFetch();

    fireEvent.change(screen.getByLabelText("Data inicial"), {
      target: { value: "2026-08-01" },
    });
    fireEvent.change(screen.getByLabelText("Data final"), {
      target: { value: "2026-08-31" },
    });

    await waitFor(() =>
      expect(listMock).toHaveBeenLastCalledWith(
        expect.objectContaining({
          startDate: "2026-08-01",
          endDate: "2026-08-31",
          page: 1,
        }),
        expect.anything(),
      ),
    );

    expect(await screen.findByText("Fornecedor Exemplo")).toBeTruthy();
    expect(screen.getByText("1.250,75")).toBeTruthy();
    expect(screen.queryByText("BRL 1.250,75")).toBeNull();
    expect(screen.getByText("Não identificada")).toBeTruthy();
    // natureza: código em primária + descrição em linha secundária
    expect(screen.getByText("BA")).toBeTruthy();
    expect(screen.getByText("Baixa de titulo")).toBeTruthy();
    // direção: badge com lado real da consulta; código cru só em
    // tooltip/AT — nunca como caractere solto em segunda linha (AC01)
    expect(screen.getByText("A pagar")).toBeTruthy();
    expect(screen.queryByText("P")).toBeNull();
    const directionCell = screen.getByTitle(
      "Código de direção na origem: P",
    );
    expect(directionCell.className).toContain("cf-cell-direction");
    expect(
      screen.getByText("código de direção na origem: P").className,
    ).toContain("cf-visually-hidden");
    // vínculo resolvido renderiza como badge de qualidade
    expect(screen.getByText("Vínculo completo")).toBeTruthy();
    expect(
      await screen.findByText("Movimentações registradas"),
    ).toBeTruthy();
    expect(screen.getByText("moeda BRL")).toBeTruthy();
    expect(screen.queryByText("moeda USD")).toBeNull();
  });

  it("alternar pagar/receber atualiza imediatamente", async () => {
    listMock.mockResolvedValue(listPayload({ side: "receivable" }));
    summaryMock.mockResolvedValue(summaryPayload());
    render(<FinancialSettlementsPage />);
    await waitInitialFetch();

    fireEvent.click(screen.getByRole("button", { name: "Baixas a receber" }));
    await waitFor(() =>
      expect(listMock).toHaveBeenLastCalledWith(
        expect.objectContaining({ side: "receivable", page: 1 }),
        expect.anything(),
      ),
    );
    expect(listMock).toHaveBeenCalledTimes(2);
  });

  it("campo digitável (natureza) usa debounce — uma consulta por pausa", async () => {
    vi.useFakeTimers();
    mockOk();
    render(<FinancialSettlementsPage />);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(listMock).toHaveBeenCalledTimes(1);

    fireEvent.change(screen.getByLabelText("Natureza financeira"), {
      target: { value: "1" },
    });
    fireEvent.change(screen.getByLabelText("Natureza financeira"), {
      target: { value: "12" },
    });
    fireEvent.change(screen.getByLabelText("Natureza financeira"), {
      target: { value: "123" },
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(399);
    });
    expect(listMock).toHaveBeenCalledTimes(1);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1);
    });
    expect(listMock).toHaveBeenCalledTimes(2);
    expect(listMock).toHaveBeenLastCalledWith(
      expect.objectContaining({ natureCode: "123" }),
      expect.anything(),
    );
  });

  it("período inválido não dispara consulta", async () => {
    mockOk();
    render(<FinancialSettlementsPage />);
    await waitInitialFetch();

    // data inicial posterior à data final default (hoje) → inválido
    fireEvent.change(screen.getByLabelText("Data inicial"), {
      target: { value: "2099-12-31" },
    });

    expect(
      screen.getByText(/a data inicial deve ser anterior ou igual à data final/),
    ).toBeTruthy();
    await act(async () => {});
    expect(listMock).toHaveBeenCalledTimes(1);
  });

  it("mudança de filtro volta para página 1 — sem consulta duplicada", async () => {
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
    await waitInitialFetch();
    await screen.findByText("Fornecedor Exemplo");
    // T02: contagem do universo filtrado junto ao título, não só da página
    expect(screen.getByText("120 registros")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Próxima" }));
    await waitFor(() =>
      expect(listMock).toHaveBeenLastCalledWith(
        expect.objectContaining({ page: 2 }),
        expect.anything(),
      ),
    );

    fireEvent.change(screen.getByLabelText("Direção da ordenação"), {
      target: { value: "asc" },
    });
    await waitFor(() =>
      expect(listMock).toHaveBeenLastCalledWith(
        expect.objectContaining({ page: 1, sortDir: "asc" }),
        expect.anything(),
      ),
    );
    // inicial + page 2 + filtro = exatamente 3 chamadas (reset não duplica)
    expect(listMock).toHaveBeenCalledTimes(3);
  });

  it("resposta antiga não sobrescreve o resultado da consulta mais recente", async () => {
    let resolveFirst: ((v: unknown) => void) | null = null;
    listMock
      .mockImplementationOnce(
        () => new Promise((resolve) => (resolveFirst = resolve)),
      )
      .mockResolvedValue(
        listPayload({
          items: [{ ...ITEM, settlementId: "S2", partyName: "Fornecedor Novo" }],
        }),
      );
    summaryMock.mockResolvedValue(summaryPayload());
    render(<FinancialSettlementsPage />);
    await waitInitialFetch();

    fireEvent.change(screen.getByLabelText("Data inicial"), {
      target: { value: "2026-10-02" },
    });
    expect(await screen.findByText("Fornecedor Novo")).toBeTruthy();

    // resposta tardia da consulta antiga é descartada
    resolveFirst?.(listPayload());
    await act(async () => {});
    expect(screen.queryByText("Fornecedor Exemplo")).toBeNull();
    expect(screen.getByText("Fornecedor Novo")).toBeTruthy();
  });

  it("limpar repõe filtros padrão e consulta automaticamente", async () => {
    mockOk();
    render(<FinancialSettlementsPage />);
    await waitInitialFetch();

    fireEvent.change(screen.getByLabelText("Data inicial"), {
      target: { value: "2026-08-01" },
    });
    await waitFor(() => expect(listMock).toHaveBeenCalledTimes(2));

    fireEvent.click(
      screen.getByRole("button", { name: "Limpar filtros" }),
    );
    await waitFor(() => expect(listMock).toHaveBeenCalledTimes(3));
    expect(listMock).toHaveBeenLastCalledWith(
      expect.objectContaining({ page: 1, sortDir: "desc" }),
      expect.anything(),
    );
  });
});

describe("FinancialSettlementsPage — estados", () => {
  it("scope_unavailable rende estado próprio — não confunde com vazio nem 403 genérico", async () => {
    listMock.mockRejectedValue(
      new ApiError(403, "Escopo de dados financeiros não autorizado.", "scope_unavailable"),
    );
    summaryMock.mockRejectedValue(new ApiError(403, "x", "scope_unavailable"));
    render(<FinancialSettlementsPage />);

    expect(await screen.findByText("Consulta ainda não habilitada")).toBeTruthy();
    expect(screen.queryByText("Acesso restrito")).toBeNull();
    expect(screen.queryByText(/Nenhuma baixa encontrada/)).toBeNull();
  });

  it("403 genérico rende acesso restrito", async () => {
    listMock.mockRejectedValue(new ApiError(403, "Forbidden"));
    summaryMock.mockRejectedValue(new ApiError(403, "Forbidden"));
    render(<FinancialSettlementsPage />);

    expect(await screen.findByText("Acesso restrito")).toBeTruthy();
  });

  it("falha de comunicação oferece Tentar novamente e recupera", async () => {
    listMock
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValue(listPayload());
    summaryMock.mockResolvedValue(summaryPayload());
    render(<FinancialSettlementsPage />);

    expect(await screen.findByText("Falha de comunicação")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));
    expect(await screen.findByText("Fornecedor Exemplo")).toBeTruthy();
    expect(listMock).toHaveBeenCalledTimes(2);
  });

  it("hero integra KPIs reais e qualidade é mensagem informativa", async () => {
    mockOk();
    render(<FinancialSettlementsPage />);
    await screen.findByText("Fornecedor Exemplo");

    // hero: identidade + KPIs do resumo vigente (doc 50)
    expect(screen.getByText("Central de Fechamento")).toBeTruthy();
    expect(
      screen.getByRole("heading", { name: "Baixas financeiras" }),
    ).toBeTruthy();
    expect(screen.getByText("Eventos")).toBeTruthy();
    expect(screen.getByText("Naturezas")).toBeTruthy();
    expect(screen.getByText("Tipos de movimento")).toBeTruthy();
    expect(
      screen.getByText(/Movimentações registradas/),
    ).toBeTruthy();
    expect(screen.getByText(/Atualizado em/)).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Atualizar consulta" }),
    ).toBeTruthy();
    expect(screen.getByText("Qualidade dos vínculos")).toBeTruthy();
    expect(
      screen.getByText(/1 sem filial identificada/),
    ).toBeTruthy();
  });

  it("Atualizar repete a consulta vigente sem alterar filtros", async () => {
    mockOk();
    render(<FinancialSettlementsPage />);
    await screen.findByText("Fornecedor Exemplo");
    expect(listMock).toHaveBeenCalledTimes(1);

    fireEvent.click(
      screen.getByRole("button", { name: "Atualizar consulta" }),
    );
    await waitFor(() => expect(listMock).toHaveBeenCalledTimes(2));
    expect(listMock).toHaveBeenLastCalledWith(
      expect.objectContaining({ page: 1, sortDir: "desc" }),
      expect.anything(),
    );
  });

  it("resultado vazio mostra mensagem de vazio da tabela", async () => {
    listMock.mockResolvedValue(listPayload({ items: [] }));
    summaryMock.mockResolvedValue(summaryPayload());
    render(<FinancialSettlementsPage />);

    expect(
      await screen.findByText(/Nenhuma baixa encontrada/),
    ).toBeTruthy();
  });

  it("carregamento usa o componente centralizado com role=status", async () => {
    let resolveList: ((v: unknown) => void) | null = null;
    listMock.mockImplementation(
      () => new Promise((resolve) => (resolveList = resolve)),
    );
    summaryMock.mockResolvedValue(summaryPayload());
    render(<FinancialSettlementsPage />);

    // hero mostra highlights em "…" e a tabela mantém role=status
    await waitFor(() =>
      expect(screen.getAllByText("…").length).toBeGreaterThan(0),
    );
    expect(screen.getAllByRole("status").length).toBeGreaterThan(0);

    resolveList?.(listPayload());
    expect(await screen.findByText("Fornecedor Exemplo")).toBeTruthy();
  });

  it("desmontagem durante a requisição não produz atualizações tardias", async () => {
    let resolveList: ((v: unknown) => void) | null = null;
    listMock.mockImplementation(
      () => new Promise((resolve) => (resolveList = resolve)),
    );
    summaryMock.mockResolvedValue(summaryPayload());
    const { unmount } = render(<FinancialSettlementsPage />);
    await waitInitialFetch();

    unmount();
    resolveList?.(listPayload());
    await act(async () => {});
  });
});


describe("FinancialSettlementsPage — modo contextual do relatório (UX-011)", () => {
  it("competência da rota inicia os filtros e exibe agrupamentos em colunas", async () => {
    mockOk();
    render(<FinancialSettlementsPage reportContext={{ period: "2026-10" }} />);

    await waitInitialFetch();
    expect(listMock).toHaveBeenCalledWith(
      expect.objectContaining({
        startDate: "2026-10-01",
        endDate: "2026-10-31",
      }),
      expect.anything(),
    );

    // Tabela de agrupamentos: natureza e tipo de movimento em colunas
    // separadas — nunca concatenados (doc 112 §46).
    await screen.findByText("Agrupamentos — Pagamentos");
    expect(
      screen.getAllByText("Fornecedores").length,
    ).toBeGreaterThan(0);
    expect(screen.getAllByText("Baixa de titulo").length).toBeGreaterThan(0);
    expect(screen.getAllByText(/5\.000,00/).length).toBeGreaterThan(0);

    // Slot de PDF honesto — sem produtor homologado.
    expect(
      screen.getByText(
        "A prévia do PDF ainda não está disponível para este relatório.",
      ),
    ).toBeTruthy();
  });

  it("«Ver registros» aplica natureza/movimento do grupo à tabela", async () => {
    mockOk();
    render(<FinancialSettlementsPage reportContext={{ period: "2026-10" }} />);

    await screen.findByText("Agrupamentos — Pagamentos");
    fireEvent.click(
      screen.getByRole("button", { name: "Ver registros" }),
    );

    await waitFor(() =>
      expect(listMock).toHaveBeenCalledWith(
        expect.objectContaining({
          natureCode: "100",
          movementType: "BA",
        }),
        expect.anything(),
      ),
    );
  });
});
