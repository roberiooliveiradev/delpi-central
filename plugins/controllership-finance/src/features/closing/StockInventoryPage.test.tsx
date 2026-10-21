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

const getMock = vi.fn();

vi.mock("../../api/stockInventoryApi", () => ({
  getStockInventory: (...args: unknown[]) => getMock(...args),
}));

import { ApiError } from "../../api/httpClient";
import { StockInventoryPage } from "./StockInventoryPage";

const ITEM = {
  productCode: "P0001",
  description: "Produto Exemplo",
  productType: "MP",
  productGroup: "1000",
  unit: "KG",
  warehouse: "01",
  branchCode: "02",
  historicalQuantity: "10.0000",
  historicalStockValue: "100.5000",
};

function payload(overrides: Record<string, unknown> = {}) {
  return {
    report: "stock-inventory",
    period: "2026-09",
    referenceDate: "2026-09-30",
    dataAsOf: "2026-09-30",
    branchCode: "all",
    reportScope: "all_products",
    source: "protheus_sb9_sb1",
    officialP7: false,
    parityStatus: "TEST_NOT_RUN",
    status: "available",
    branchesAvailable: ["02"],
    branchesMissing: [],
    historicalTotal: "10576487.8400",
    pagination: {
      page: 1,
      page_size: 50,
      total_items: 1,
      total_pages: 1,
      has_next: false,
      has_previous: false,
    },
    items: [ITEM],
    summariesByType: [
      {
        productType: "MP",
        itemCount: 1,
        totalQuantity: "10.0000",
        totalStockValue: "100.5000",
      },
    ],
    summariesByWarehouse: [
      {
        branchCode: "02",
        warehouse: "01",
        itemCount: 1,
        totalQuantity: "10.0000",
        totalStockValue: "100.5000",
      },
    ],
    ...overrides,
  };
}

async function waitInitialFetch() {
  await waitFor(() => expect(getMock).toHaveBeenCalledTimes(1));
}

afterEach(() => {
  cleanup();
  getMock.mockReset();
  vi.useRealTimers();
});

describe("StockInventoryPage — consulta automática", () => {
  it("consulta inicial automática com a competência atual", async () => {
    getMock.mockResolvedValue(payload());
    render(<StockInventoryPage />);

    await waitInitialFetch();
    const query = getMock.mock.calls[0][0];
    expect(query.period).toMatch(/^\d{4}-\d{2}$/);
    expect(query.branch).toBe("all");
    expect(query.reportScope).toBe("all_products");
    expect(query.page).toBe(1);
    expect(query.pageSize).toBe(50);
    expect(
      screen.queryByRole("button", { name: "Consultar" }),
    ).toBeNull();
    expect(
      screen.getByText("Estoque histórico — P7"),
    ).toBeTruthy();
    expect(
      screen.getByText(/não equivalem ao relatório oficial MATR460/i),
    ).toBeTruthy();
  });

  it("mudança de competência atualiza a consulta sem botão", async () => {
    getMock.mockResolvedValue(payload());
    render(<StockInventoryPage />);
    await waitInitialFetch();

    fireEvent.change(screen.getByLabelText("Competência"), {
      target: { value: "2026-09" },
    });
    await waitFor(() => expect(getMock).toHaveBeenCalledTimes(2));
    expect(getMock.mock.calls[1][0].period).toBe("2026-09");
    expect(await screen.findByText("Produto Exemplo")).toBeTruthy();
    // data-base civil exibida sem deslocamento: último dia do mês
    expect(screen.getByText("30/09/2026")).toBeTruthy();
  });

  it("filial é filtro de dados — encaminha o código ao confirmar seleção", async () => {
    getMock.mockResolvedValue(payload());
    render(<StockInventoryPage />);
    await waitInitialFetch();

    fireEvent.change(screen.getByLabelText("Filial"), {
      target: { value: "02" },
    });
    await waitFor(() => expect(getMock).toHaveBeenCalledTimes(2));
    expect(getMock.mock.calls[1][0].branch).toBe("02");
  });

  it("alternar visão MP/PI/PA atualiza imediatamente", async () => {
    getMock.mockResolvedValue(payload());
    render(<StockInventoryPage />);
    await waitInitialFetch();

    fireEvent.click(screen.getByRole("button", { name: "MP / PI / PA" }));
    await waitFor(() => expect(getMock).toHaveBeenCalledTimes(2));
    expect(getMock.mock.calls[1][0].reportScope).toBe("mp_pi_pa");
  });

  it("armazém (digitável) usa debounce — uma consulta por pausa", async () => {
    vi.useFakeTimers();
    getMock.mockResolvedValue(payload());
    render(<StockInventoryPage />);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(getMock).toHaveBeenCalledTimes(1);

    fireEvent.change(screen.getByLabelText("Armazém"), {
      target: { value: "0" },
    });
    fireEvent.change(screen.getByLabelText("Armazém"), {
      target: { value: "01" },
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(399);
    });
    expect(getMock).toHaveBeenCalledTimes(1);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1);
    });
    expect(getMock).toHaveBeenCalledTimes(2);
    expect(getMock.mock.calls[1][0].warehouse).toBe("01");
  });

  it("competência incompleta/inválida não dispara consulta", async () => {
    getMock.mockResolvedValue(payload());
    render(<StockInventoryPage />);
    await waitInitialFetch();

    fireEvent.change(screen.getByLabelText("Competência"), {
      target: { value: "" },
    });
    expect(
      screen.getByText(/no formato AAAA-MM/),
    ).toBeTruthy();
    await act(async () => {});
    expect(getMock).toHaveBeenCalledTimes(1);
  });

  it("mudança de filtro volta para página 1 — sem consulta duplicada", async () => {
    getMock.mockResolvedValue(
      payload({
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
    render(<StockInventoryPage />);
    await waitInitialFetch();
    await screen.findByText("Produto Exemplo");

    fireEvent.click(screen.getByRole("button", { name: "Próxima" }));
    await waitFor(() =>
      expect(getMock).toHaveBeenLastCalledWith(
        expect.objectContaining({ page: 2 }),
        expect.anything(),
      ),
    );

    fireEvent.change(screen.getByLabelText("Filial"), {
      target: { value: "01" },
    });
    await waitFor(() =>
      expect(getMock).toHaveBeenLastCalledWith(
        expect.objectContaining({ page: 1, branch: "01" }),
        expect.anything(),
      ),
    );
    // inicial + page 2 + filtro = exatamente 3 chamadas
    expect(getMock).toHaveBeenCalledTimes(3);
  });

  it("resposta antiga não sobrescreve o resultado mais recente", async () => {
    let resolveFirst: ((v: unknown) => void) | null = null;
    getMock
      .mockImplementationOnce(
        () => new Promise((resolve) => (resolveFirst = resolve)),
      )
      .mockResolvedValue(
        payload({
          items: [
            { ...ITEM, productCode: "P9999", description: "Produto Novo" },
          ],
        }),
      );
    render(<StockInventoryPage />);
    await waitInitialFetch();

    fireEvent.change(screen.getByLabelText("Filial"), {
      target: { value: "02" },
    });
    expect(await screen.findByText("Produto Novo")).toBeTruthy();

    resolveFirst?.(payload());
    await act(async () => {});
    expect(screen.queryByText("Produto Exemplo")).toBeNull();
    expect(screen.getByText("Produto Novo")).toBeTruthy();
  });

  it("limpar repõe os filtros padrão e consulta automaticamente", async () => {
    getMock.mockResolvedValue(payload());
    render(<StockInventoryPage />);
    await waitInitialFetch();

    fireEvent.change(screen.getByLabelText("Filial"), {
      target: { value: "01" },
    });
    await waitFor(() => expect(getMock).toHaveBeenCalledTimes(2));

    fireEvent.click(
      screen.getByRole("button", { name: "Limpar filtros" }),
    );
    await waitFor(() =>
      expect(getMock).toHaveBeenLastCalledWith(
        expect.objectContaining({ branch: "all", page: 1 }),
        expect.anything(),
      ),
    );
    expect(getMock).toHaveBeenCalledTimes(3);
  });
});

describe("StockInventoryPage — estados", () => {
  it("mostra indicadores, resumos e tabela quando disponível", async () => {
    getMock.mockResolvedValue(payload());
    render(<StockInventoryPage />);

    await screen.findByText("Produto Exemplo");
    expect(screen.getByText("Resumo por tipo de produto")).toBeTruthy();
    expect(screen.getByText("Resumo por armazém")).toBeTruthy();
    expect(screen.getByText("10.576.487,84")).toBeTruthy();
  });

  it("grid de indicadores e resumos usa o card-strip centralizado", async () => {
    getMock.mockResolvedValue(
      payload({
        summariesByType: [
          {
            productType: "MP",
            itemCount: 3867,
            totalQuantity: "1.0000",
            totalStockValue: "12896290.8900",
          },
        ],
        summariesByWarehouse: [
          {
            branchCode: "02",
            warehouse: "01",
            itemCount: 42,
            totalQuantity: "1.0000",
            totalStockValue: "10113731.7800",
          },
        ],
      }),
    );
    render(<StockInventoryPage />);

    await screen.findByText("Produto Exemplo");
    // hero integra identidade e KPIs reais (doc 50)
    expect(screen.getByText("Central de Fechamento")).toBeTruthy();
    expect(
      screen.getByRole("heading", { name: "Estoque histórico — P7" }),
    ).toBeTruthy();
    expect(screen.getByText("Disponibilidade")).toBeTruthy();
    expect(screen.getByText("Data-base")).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Atualizar consulta" }),
    ).toBeTruthy();
    // grupos acessíveis do grid centralizado
    expect(
      screen.getByRole("group", { name: "Resumo por tipo de produto" }),
    ).toBeTruthy();
    expect(
      screen.getByRole("group", { name: "Resumo por armazém" }),
    ).toBeTruthy();
    // valor financeiro longo exibido por inteiro — sem truncamento
    expect(screen.getByText("12.896.290,89")).toBeTruthy();
    expect(screen.getByText("10.113.731,78")).toBeTruthy();
    // associação armazém·filial preservada no rótulo do card
    expect(screen.getByText("Armazém 01 · Filial 02")).toBeTruthy();
    expect(screen.getAllByText(/itens$/).length).toBeGreaterThan(0);
    // tipo de produto renderiza como badge neutro do kit (sem semântica inventada)
    expect(screen.getAllByText("MP").length).toBeGreaterThan(0);
  });

  it("seções de resultado ficam dentro do stack com gap (regressão)", async () => {
    getMock.mockResolvedValue(payload());
    const { container } = render(<StockInventoryPage />);
    await screen.findByText("Produto Exemplo");

    const resultsRegion = container.querySelector(
      "[aria-busy]",
    ) as HTMLElement | null;
    expect(resultsRegion).not.toBeNull();
    // a região de resultados deve ser um cf-page-stack para que as
    // CfSectionCard internas herdem o gap do token --cf-section-gap
    expect(resultsRegion?.classList.contains("cf-page-stack")).toBe(true);
    expect(resultsRegion?.children.length ?? 0).toBeGreaterThan(0);
  });

  it("source_missing não exibe total nem zero", async () => {
    getMock.mockResolvedValue(
      payload({
        status: "source_missing",
        dataAsOf: null,
        branchesAvailable: [],
        branchesMissing: ["01"],
        historicalTotal: null,
        items: [],
        summariesByType: [],
        summariesByWarehouse: [],
        pagination: {
          page: 1,
          page_size: 50,
          total_items: 0,
          total_pages: 1,
          has_next: false,
          has_previous: false,
        },
      }),
    );
    render(<StockInventoryPage />);
    await waitFor(() => screen.getByText("Snapshot não encontrado"));
    expect(screen.queryByText("Valor histórico total")).toBeNull();
  });

  it("incomplete sinaliza filial ausente", async () => {
    getMock.mockResolvedValue(
      payload({ status: "incomplete", branchesMissing: ["01"] }),
    );
    render(<StockInventoryPage />);
    await waitFor(() =>
      screen.getByText("Dados parcialmente disponíveis"),
    );
  });

  it("erro 403 mostra estado de acesso restrito", async () => {
    getMock.mockRejectedValue(new ApiError(403, "Acesso negado."));
    render(<StockInventoryPage />);
    await waitFor(() => screen.getByText("Acesso restrito"));
  });

  it("scope_unavailable mostra estado próprio", async () => {
    getMock.mockRejectedValue(
      new ApiError(403, "Escopo.", "scope_unavailable"),
    );
    render(<StockInventoryPage />);
    await waitFor(() => screen.getByText("Consulta ainda não habilitada"));
  });

  it("S2S_SCOPE_DENIED mostra estado de integração pendente", async () => {
    getMock.mockRejectedValue(
      new ApiError(403, "Acesso negado.", "S2S_SCOPE_DENIED"),
    );
    render(<StockInventoryPage />);
    await waitFor(() => screen.getByText("Integração de dados pendente"));
  });

  it("503 oferece Tentar novamente e recupera", async () => {
    getMock
      .mockRejectedValueOnce(
        new ApiError(503, "Origem de dados financeiros indisponível."),
      )
      .mockResolvedValue(payload());
    render(<StockInventoryPage />);
    await waitFor(() => screen.getByText("Origem indisponível"));

    fireEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));
    expect(await screen.findByText("Produto Exemplo")).toBeTruthy();
    expect(getMock).toHaveBeenCalledTimes(2);
  });

  it("carregamento usa o componente centralizado com role=status", async () => {
    let resolveGet: ((v: unknown) => void) | null = null;
    getMock.mockImplementation(
      () => new Promise((resolve) => (resolveGet = resolve)),
    );
    render(<StockInventoryPage />);

    // hero mostra highlights em "…" e a tabela mantém role=status
    await waitFor(() =>
      expect(screen.getAllByText("…").length).toBeGreaterThan(0),
    );
    expect(screen.getAllByRole("status").length).toBeGreaterThan(0);

    resolveGet?.(payload());
    expect(await screen.findByText("Produto Exemplo")).toBeTruthy();
  });
});
