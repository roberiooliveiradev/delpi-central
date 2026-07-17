import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import * as safetyStockApi from "../api/safetyStockApi";
import { configureHttpClient } from "../api/httpClient";
import { ApiClientError } from "../types/api";
import type { SafetyStockFiltersData } from "../types/safetyStock";
import { SafetyStockPage } from "./SafetyStockPage";

const filtersPayload: SafetyStockFiltersData = {
  branch: "01",
  product_groups: ["GRP1"],
  units: ["PC"],
  statuses: ["below_safety_stock", "without_safety_stock"],
  warehouses: ["01", "50", "98", "99"],
  primary_warehouse: "01",
  work_in_process_warehouses: ["50", "98", "99"],
  work_in_process_note: "nota",
  authorized_branches: ["01"],
};

const summaryPayload = {
  total_materials: 100,
  with_safety_stock: 80,
  without_safety_stock: 20,
  below_safety_stock: 12,
  at_safety_stock: 5,
  above_safety_stock: 63,
  with_primary_stock: 70,
  without_primary_stock: 30,
  with_work_in_process_stock: 15,
  deficit_by_unit: [{ unit: "PC", material_count: 2, deficit_quantity: 150 }],
};

const itemsPayload = {
  items: [
    {
      product_code: "10010005",
      product_description: "PARAFUSO TESTE",
      product_type: "MP",
      unit: "PC",
      product_group: "GRP1",
      branch: "01",
      blocked: false,
      safety_stock: 100,
      primary_stock: 50,
      work_in_process_stock: 20,
      warehouse_50_stock: 5,
      warehouse_98_stock: 5,
      warehouse_99_stock: 10,
      work_in_process_committed: 3,
      work_in_process_available: 17,
      deficit_quantity: 50,
      status: "below_safety_stock" as const,
    },
  ],
  page: 1,
  page_size: 50,
  total: 1,
  total_pages: 1,
  sort_by: "product_code" as const,
  sort_direction: "asc" as const,
};

const detailsPayload = {
  product: {
    product_code: "10010005",
    product_description: "PARAFUSO TESTE",
    product_type: "MP",
    unit: "PC",
    secondary_unit: "",
    conversion_factor: null,
    conversion_type: "",
    product_group: "GRP1",
    branch: "01",
    blocked: false,
    status: "below_safety_stock" as const,
  },
  stock: {
    safety_stock: 100,
    available_stock: 65,
    primary_stock: 50,
    warehouse_50_stock: 5,
    warehouse_98_stock: 5,
    warehouse_99_stock: 10,
    work_in_process_stock: 20,
    work_in_process_committed: 3,
    work_in_process_available: 17,
    deficit_quantity: 35,
  },
  purchase_coverage: {
    status: "partial" as const,
    deficit_quantity: 35,
    eligible_open_quantity: 20,
    remaining_to_buy: 15,
    open_order_count: 1,
    eligible_order_count: 1,
    next_expected_delivery_date: "2026-08-10",
    incompatible_unit_order_count: 0,
    warnings: [],
  },
  open_purchase_orders: {
    items: [
      {
        branch: "01",
        order_number: "PC001",
        order_item: "01",
        product_code: "10010005",
        product_description: "PARAFUSO TESTE",
        warehouse: "01",
        unit: "PC",
        ordered_quantity: 20,
        delivered_quantity: 0,
        open_quantity: 20,
        open_quantity_primary_unit: 20,
        pre_invoice_quantity: 0,
        issue_date: "2026-07-01",
        expected_delivery_date: "2026-08-10",
        supplier_code: "F1",
        supplier_store: "01",
        supplier_name: "Fornecedor Teste",
        unit_price: 1,
        open_value: 20,
        unit_compatible: true,
        unit_conversion_reason: null,
        warehouse_eligible: true,
        coverage_eligible: true,
      },
    ],
    total: 1,
  },
  open_commitments: {
    items: [
      {
        branch: "01",
        product_code: "10010005",
        product_description: "PARAFUSO TESTE",
        warehouse: "01",
        production_order: "OP150",
        origin_production_order: "",
        commitment_date: "2026-07-20",
        unit: "PC",
        original_quantity: 150,
        open_quantity: 150,
        open_quantity_primary_unit: 150,
        consumed_quantity: 0,
        lot: "",
        commitment_sequence: "001",
        preserved_balance: 0,
        unit_compatible: true,
        unit_conversion_reason: null,
        warehouse_eligible: true,
        projection_eligible: true,
        date_status: "scheduled" as const,
        date_semantics: "commitment_date",
      },
    ],
    total: 1,
    summary: {
      eligible_open_quantity: 150,
      next_commitment_date: "2026-07-20",
      incompatible_unit_commitment_count: 0,
      eligible_warehouses: ["01", "98", "99"],
      warnings: [],
    },
  },
  stock_projection: {
    items: [
      {
        sequence: 1,
        event_date: "2026-07-16",
        date_status: "today" as const,
        date_semantics: "as_of_today",
        origin: "initial_balance" as const,
        origin_label: "Saldo inicial",
        reference: "Saldo disponível (01+98+99)",
        warehouse: "",
        movement: 100,
        inflow: 0,
        outflow: 0,
        running_balance: 100,
        unit_compatible: true,
        projection_eligible: true,
      },
      {
        sequence: 2,
        event_date: "2026-07-20",
        date_status: "scheduled" as const,
        date_semantics: "commitment_date",
        origin: "commitment" as const,
        origin_label: "Empenho",
        reference: "OP150",
        warehouse: "01",
        movement: -150,
        inflow: 0,
        outflow: 150,
        running_balance: -50,
        unit_compatible: true,
        projection_eligible: true,
      },
      {
        sequence: 3,
        event_date: "2026-07-30",
        date_status: "scheduled" as const,
        date_semantics: "expected_delivery_date",
        origin: "purchase_order" as const,
        origin_label: "Pedido de compra",
        reference: "PC001/01 - TRAMAR",
        warehouse: "01",
        movement: 200,
        inflow: 200,
        outflow: 0,
        running_balance: 150,
        unit_compatible: true,
        projection_eligible: true,
      },
    ],
    total: 3,
    summary: {
      as_of_date: "2026-07-16",
      initial_balance: 100,
      safety_stock: 80,
      eligible_purchase_quantity: 200,
      eligible_commitment_quantity: 150,
      final_projected_balance: 150,
      final_balance_after_safety: 70,
      minimum_projected_balance: -50,
      first_shortage_date: "2026-07-20",
      projected_remaining_to_buy: 0,
      status: "temporary_shortage" as const,
      eligible_warehouses: ["01", "98", "99"],
      warnings: [],
    },
  },
};

const suppliersPayload = {
  items: [
    {
      product_code: "10010005",
      supplier_code: "F001",
      supplier_store: "01",
      supplier_part_number: "PN-ACME-001",
      trade_name: "ACME",
      legal_name: "ACME INDUSTRIA LTDA",
      document: "12345678000199",
      has_last_purchase: true,
      last_purchase_date: "2026-07-10",
      last_unit_price: 12.5,
      last_quantity: 10,
      last_total_value: 125,
      last_invoice_number: "000123",
      last_invoice_series: "1",
    },
    {
      product_code: "10010005",
      supplier_code: "F002",
      supplier_store: "01",
      supplier_part_number: "",
      trade_name: "BETA",
      legal_name: "BETA SA",
      document: "99887766000155",
      has_last_purchase: false,
      last_purchase_date: null,
      last_unit_price: null,
      last_quantity: null,
      last_total_value: null,
      last_invoice_number: null,
      last_invoice_series: null,
    },
  ],
  total: 2,
};

const supplierPriceHistoryPayload = {
  product_code: "10010005",
  branch: "01",
  supplier_code: "F001",
  supplier_store: "01",
  date_start: "20250717",
  date_end_exclusive: "20260718",
  items: [
    {
      branch: "01",
      purchase_date: "2026-01-15",
      issue_date: "2026-01-14",
      supplier_code: "F001",
      supplier_store: "01",
      supplier_name: "ACME",
      unit_price: 10,
      quantity: 5,
      total_value: 50,
      invoice_number: "000100",
      invoice_series: "1",
    },
    {
      branch: "01",
      purchase_date: "2026-07-10",
      issue_date: "2026-07-09",
      supplier_code: "F001",
      supplier_store: "01",
      supplier_name: "ACME",
      unit_price: 12.5,
      quantity: 10,
      total_value: 125,
      invoice_number: "000123",
      invoice_series: "1",
    },
  ],
  total: 2,
  summary: {
    total_purchases: 2,
    min_unit_price: 10,
    max_unit_price: 12.5,
    first_unit_price: 10,
    last_unit_price: 12.5,
    variation_percent: 25,
  },
};

function mockApiSuccess() {
  vi.spyOn(safetyStockApi, "bootstrapSafetyStockFilters").mockResolvedValue(filtersPayload);
  vi.spyOn(safetyStockApi, "fetchSafetyStockFilters").mockResolvedValue(filtersPayload);
  vi.spyOn(safetyStockApi, "fetchSafetyStockSummary").mockResolvedValue(summaryPayload);
  vi.spyOn(safetyStockApi, "fetchSafetyStockItems").mockResolvedValue(itemsPayload);
  vi.spyOn(safetyStockApi, "fetchSafetyStockItemDetails").mockResolvedValue(detailsPayload);
  vi.spyOn(safetyStockApi, "fetchSafetyStockItemSuppliers").mockResolvedValue(suppliersPayload);
  vi.spyOn(safetyStockApi, "fetchSafetyStockSupplierPriceHistory").mockResolvedValue(
    supplierPriceHistoryPayload,
  );
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

beforeEach(() => {
  configureHttpClient(() => "test-token");
});

describe("SafetyStockPage", () => {
  it("renderiza cabeçalho", async () => {
    mockApiSuccess();
    render(<SafetyStockPage />);
    expect(screen.getByRole("heading", { name: "Estoque de Segurança" })).toBeTruthy();
    await waitFor(() => {
      expect(screen.getByText("Total de matérias-primas")).toBeTruthy();
    });
  });

  it("seleciona filial única automaticamente", async () => {
    mockApiSuccess();
    render(<SafetyStockPage />);
    await waitFor(() => {
      expect(safetyStockApi.fetchSafetyStockSummary).toHaveBeenCalled();
      const lastSummary = vi.mocked(safetyStockApi.fetchSafetyStockSummary).mock.calls.at(-1)?.[0];
      expect(lastSummary?.status).toBe("below_safety_stock");
      expect(lastSummary?.includeWithoutSafetyStock).toBe(false);
    });
  });

  it("exibe KPIs e déficit por unidade sem somar UMs", async () => {
    mockApiSuccess();
    render(<SafetyStockPage />);
    await waitFor(() => {
      expect(screen.getByText("Total de matérias-primas")).toBeTruthy();
      expect(screen.getByText(/2 materiais/)).toBeTruthy();
      expect(screen.getByText(/150/)).toBeTruthy();
    });
    expect(screen.queryByText(/total.*déficit/i)).toBeNull();
    expect(screen.queryByText("Sem estoque de segurança")).toBeNull();
    expect(screen.queryByText("Com saldo no armazém principal")).toBeNull();
    expect(screen.queryByText("Com estoque em processo")).toBeNull();
  });

  it("renderiza tabela com badge em português e saldo consolidado", async () => {
    mockApiSuccess();
    render(<SafetyStockPage />);
    await waitFor(() => {
      expect(screen.getByText("10010005")).toBeTruthy();
    });
    expect(screen.getAllByText("Abaixo do estoque de segurança").length).toBeGreaterThan(0);
    expect(screen.getByText("65,00")).toBeTruthy();
    expect(screen.queryByText("Em processo")).toBeNull();
  });

  it("abre modal central com extrato e cobertura ao clicar na linha", async () => {
    mockApiSuccess();
    render(<SafetyStockPage />);
    await waitFor(() => expect(screen.getByText("10010005")).toBeTruthy());

    fireEvent.click(screen.getByText("10010005"));

    await waitFor(() => {
      expect(safetyStockApi.fetchSafetyStockItemDetails).toHaveBeenCalledWith(
        "01",
        "10010005",
        expect.any(Object),
      );
      expect(safetyStockApi.fetchSafetyStockItemSuppliers).toHaveBeenCalledWith(
        "01",
        "10010005",
        expect.any(Object),
      );
      const dialog = screen.getByRole("dialog");
      expect(dialog.className).toContain("ess-modal");
      expect(dialog.className).toContain("delpi-ui-modal");
      expect(document.querySelector(".ess-drawer")).toBeNull();
      expect(screen.getByText("Cobertura por pedidos de compra")).toBeTruthy();
      expect(screen.getByText("Extrato projetado de saldo")).toBeTruthy();
      expect(screen.getByText("Fornecedores vinculados")).toBeTruthy();
      expect(screen.getByText("ACME")).toBeTruthy();
      expect(screen.getByText("10/07/2026")).toBeTruthy();
      expect(screen.getByText("R$ 12,50")).toBeTruthy();
      expect(screen.getAllByText("Sem compras registradas").length).toBeGreaterThan(0);
      expect(screen.getByText("Partnumber")).toBeTruthy();
      expect(screen.getByText("PN-ACME-001")).toBeTruthy();
      expect(screen.queryByText("CNPJ/CPF")).toBeNull();
      expect(screen.queryByText("Razão social")).toBeNull();
      expect(screen.queryByText("Valor total")).toBeNull();
      expect(screen.queryByText("Falta temporária projetada")).toBeNull();
      expect(screen.queryByText("Identificação")).toBeNull();
      expect(screen.queryByText("Armazém 50")).toBeNull();
      expect(screen.queryByText(/Em processo \(50\+98\+99\)/)).toBeNull();
      expect(screen.queryByText("Após estoque de segurança")).toBeNull();
      expect(screen.queryByText("Ainda comprar (projetado)")).toBeNull();
      expect(screen.getByText("Pedido parcial")).toBeTruthy();
      expect(screen.getByText("PC001/01 - TRAMAR")).toBeTruthy();
      expect(screen.getByText("OP150")).toBeTruthy();
      expect(screen.queryByText("Empenhos em aberto (SD4)")).toBeNull();
      expect(screen.queryByText("Pedidos de compra em aberto")).toBeNull();
      expect(screen.queryByLabelText("Filtrar extrato por armazém")).toBeNull();
      expect(screen.queryByText(/Extrato consolidado dos armazéns/)).toBeNull();
      expect(document.querySelector(".ess-detail__flow--positive")).toBeTruthy();
      expect(document.querySelector(".ess-detail__flow--negative")).toBeTruthy();
      expect(document.querySelector(".ess-modal__footer")).toBeTruthy();
      expect(screen.getByRole("button", { name: "Fechar" })).toBeTruthy();
      const balanceSection = screen.getByRole("region", { name: "Saldos" });
      expect(balanceSection.querySelectorAll(".delpi-ui-kpi-card")).toHaveLength(6);
      expect(screen.getByText("Saldo disponível").closest("article")?.className).toContain(
        "delpi-ui-kpi-card--wide",
      );
      const projectionSection = screen.getByRole("region", { name: "Projeção de saldo" });
      expect(projectionSection.textContent).toContain(
        "Partindo de um saldo de 100,00, com 200,00 de entradas previstas e 150,00 de consumo comprometido, o saldo final projetado é 150,00.",
      );
      expect(projectionSection.textContent).toContain(
        "A primeira ruptura está prevista para 20/07/2026.",
      );
      expect(
        Array.from(projectionSection.querySelectorAll("strong.ess-detail__situation-critical")).map(
          (element) => element.textContent,
        ),
      ).toEqual(expect.arrayContaining(["-50,00", "20/07/2026"]));
      expect(
        screen
          .getByText("Déficit físico")
          .closest("article")
          ?.querySelector(".delpi-ui-kpi-value--danger"),
      ).toBeTruthy();
    });

    const ledgerHelp =
      "Linha do tempo consolidada: saldo atual, saídas por empenho (D4_QUANT) e entradas por pedido aberto. A data do empenho é a data do empenho no Protheus, não a garantia de consumo fabril.";
    expect(screen.queryByText(ledgerHelp)).toBeNull();
    fireEvent.focus(screen.getByRole("button", { name: "Como funciona o extrato projetado" }));
    expect(screen.getByRole("tooltip", { hidden: true }).textContent).toBe(ledgerHelp);
  });

  it("mantém detalhe visível quando fornecedores falham e permite retry só da seção", async () => {
    mockApiSuccess();
    vi.mocked(safetyStockApi.fetchSafetyStockItemSuppliers).mockRejectedValue(
      new ApiClientError("Falha ao consultar fornecedores", 500, "unavailable"),
    );

    render(<SafetyStockPage />);
    await waitFor(() => expect(screen.getByText("10010005")).toBeTruthy());
    fireEvent.click(screen.getByText("10010005"));

    await waitFor(() => {
      expect(screen.getByText("Cobertura por pedidos de compra")).toBeTruthy();
      expect(screen.getByText("Fornecedores vinculados")).toBeTruthy();
      expect(screen.getByText("Falha ao consultar fornecedores")).toBeTruthy();
    });

    fireEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));
    await waitFor(() => {
      expect(safetyStockApi.fetchSafetyStockItemSuppliers).toHaveBeenCalledTimes(2);
    });
  });

  it("exibe estado vazio de fornecedores sem ocultar saldos", async () => {
    mockApiSuccess();
    vi.mocked(safetyStockApi.fetchSafetyStockItemSuppliers).mockResolvedValue({
      items: [],
      total: 0,
    });

    render(<SafetyStockPage />);
    await waitFor(() => expect(screen.getByText("10010005")).toBeTruthy());
    fireEvent.click(screen.getByText("10010005"));

    await waitFor(() => {
      expect(screen.getByText("Saldos e estoque de segurança")).toBeTruthy();
      expect(
        screen.getByText("Nenhum fornecedor está vinculado a este produto"),
      ).toBeTruthy();
    });
  });

  it("carrega histórico de preço sob demanda ao clicar no fornecedor", async () => {
    mockApiSuccess();
    render(<SafetyStockPage />);
    await waitFor(() => expect(screen.getByText("10010005")).toBeTruthy());
    fireEvent.click(screen.getByText("10010005"));

    await waitFor(() => expect(screen.getByText("ACME")).toBeTruthy());
    expect(safetyStockApi.fetchSafetyStockSupplierPriceHistory).not.toHaveBeenCalled();

    fireEvent.click(screen.getByText("ACME"));

    await waitFor(() => {
      expect(safetyStockApi.fetchSafetyStockSupplierPriceHistory).toHaveBeenCalledWith(
        "01",
        "10010005",
        "F001",
        "01",
        expect.any(Object),
      );
      expect(screen.getByText(/Oscilação de preço — ACME/)).toBeTruthy();
      expect(screen.getByText("Preço unitário (R$)")).toBeTruthy();
      expect(screen.getByText(/\+25,00%/)).toBeTruthy();
      expect(screen.getByText(/NF 000100\/1/)).toBeTruthy();
      expect(
        document.querySelectorAll(".delpi-ui-series-chart__data-label").length,
      ).toBeGreaterThan(0);
    });
  });

  it("mantém detalhe quando histórico do fornecedor falha e permite retry", async () => {
    mockApiSuccess();
    vi.mocked(safetyStockApi.fetchSafetyStockSupplierPriceHistory).mockRejectedValue(
      new ApiClientError("Falha no histórico", 503, "unavailable"),
    );

    render(<SafetyStockPage />);
    await waitFor(() => expect(screen.getByText("10010005")).toBeTruthy());
    fireEvent.click(screen.getByText("10010005"));
    await waitFor(() => expect(screen.getByText("ACME")).toBeTruthy());
    fireEvent.click(screen.getByText("ACME"));

    await waitFor(() => {
      expect(screen.getByText("Cobertura por pedidos de compra")).toBeTruthy();
      expect(screen.getByText("Falha no histórico")).toBeTruthy();
    });

    fireEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));
    await waitFor(() => {
      expect(safetyStockApi.fetchSafetyStockSupplierPriceHistory).toHaveBeenCalledTimes(2);
    });
  });

  it("exibe vazio do histórico sem ocultar fornecedores", async () => {
    mockApiSuccess();
    vi.mocked(safetyStockApi.fetchSafetyStockSupplierPriceHistory).mockResolvedValue({
      ...supplierPriceHistoryPayload,
      items: [],
      total: 0,
      summary: {
        total_purchases: 0,
        min_unit_price: null,
        max_unit_price: null,
        first_unit_price: null,
        last_unit_price: null,
        variation_percent: null,
      },
    });

    render(<SafetyStockPage />);
    await waitFor(() => expect(screen.getByText("10010005")).toBeTruthy());
    fireEvent.click(screen.getByText("10010005"));
    await waitFor(() => expect(screen.getByText("ACME")).toBeTruthy());
    fireEvent.click(screen.getByText("ACME"));

    await waitFor(() => {
      expect(screen.getByText("Fornecedores vinculados")).toBeTruthy();
      expect(
        screen.getByText(
          "Nenhuma compra registrada com este fornecedor nos últimos 12 meses.",
        ),
      ).toBeTruthy();
    });
  });

  it("permite buscar outro produto no cabeçalho do modal", async () => {
    mockApiSuccess();
    render(<SafetyStockPage />);
    await waitFor(() => expect(screen.getByText("10010005")).toBeTruthy());

    fireEvent.click(screen.getByText("10010005"));
    await waitFor(() => expect(screen.getByRole("dialog")).toBeTruthy());

    const searchInput = screen.getByLabelText("Buscar outro produto");
    fireEvent.change(searchInput, { target: { value: "paraf" } });

    await waitFor(() => {
      expect(safetyStockApi.fetchSafetyStockItems).toHaveBeenCalledWith(
        expect.objectContaining({
          search: "paraf",
          includeWithoutSafetyStock: true,
          includeBlocked: true,
        }),
        1,
        8,
        expect.any(Object),
      );
      expect(screen.getByRole("listbox", { name: "Produtos encontrados" })).toBeTruthy();
    });

    fireEvent.click(screen.getByRole("button", { name: /PARAFUSO TESTE/ }));
    await waitFor(() => {
      expect(screen.queryByRole("listbox", { name: "Produtos encontrados" })).toBeNull();
    });
  });

  it("reinicia página ao alterar busca", async () => {
    mockApiSuccess();
    render(<SafetyStockPage />);
    await waitFor(() => expect(safetyStockApi.fetchSafetyStockItems).toHaveBeenCalled());

    fireEvent.change(screen.getByLabelText("Busca"), {
      target: { value: "parafuso" },
    });

    await waitFor(
      () => {
        const calls = vi.mocked(safetyStockApi.fetchSafetyStockItems).mock.calls;
        const lastParams = calls.at(-1);
        expect(lastParams?.[0]?.search).toBe("parafuso");
        expect(lastParams?.[1]).toBe(1);
      },
      { timeout: 1200 },
    );
  });

  it("limpa filtros mantendo filial", async () => {
    mockApiSuccess();
    render(<SafetyStockPage />);
    await waitFor(() => expect(screen.getByLabelText("Busca")).toBeTruthy());
    fireEvent.change(screen.getByLabelText("Busca"), { target: { value: "abc" } });
    fireEvent.click(screen.getByRole("button", { name: "Limpar filtros" }));
    expect((screen.getByLabelText("Busca") as HTMLInputElement).value).toBe("");
  });

  it("preserva summary quando items falha", async () => {
    mockApiSuccess();
    vi.mocked(safetyStockApi.fetchSafetyStockItems).mockRejectedValue(
      new ApiClientError("Falha na tabela", 503, "unavailable"),
    );
    render(<SafetyStockPage />);
    await waitFor(() => {
      expect(screen.getByText("Total de matérias-primas")).toBeTruthy();
      expect(screen.getByText("Dados temporariamente indisponíveis")).toBeTruthy();
    });
  });

  it("preserva tabela quando summary falha", async () => {
    mockApiSuccess();
    vi.mocked(safetyStockApi.fetchSafetyStockSummary).mockRejectedValue(
      new ApiClientError("Falha no resumo", 503, "unavailable"),
    );
    render(<SafetyStockPage />);
    await waitFor(() => {
      expect(screen.getByText("Dados temporariamente indisponíveis")).toBeTruthy();
      expect(screen.getByText("10010005")).toBeTruthy();
    });
  });

  it("mostra sessão expirada para 401 nos filtros", async () => {
    vi.spyOn(safetyStockApi, "bootstrapSafetyStockFilters").mockRejectedValue(
      new ApiClientError("É necessário autenticar novamente para continuar.", 401, "auth", {
        retryable: false,
      }),
    );
    render(<SafetyStockPage />);
    await waitFor(() => {
      expect(screen.getByText("Sessão expirada")).toBeTruthy();
      expect(screen.getByText("É necessário autenticar novamente para continuar.")).toBeTruthy();
    });
  });

  it("mostra acesso negado para 403 nos filtros", async () => {
    vi.spyOn(safetyStockApi, "bootstrapSafetyStockFilters").mockRejectedValue(
      new ApiClientError(
        "Você não possui permissão para consultar o Estoque de Segurança ou a filial solicitada.",
        403,
        "forbidden",
        { retryable: false },
      ),
    );
    render(<SafetyStockPage />);
    await waitFor(() => {
      expect(screen.getByText("Acesso negado")).toBeTruthy();
    });
  });

  it("mostra filtros inválidos para 400 nos filtros", async () => {
    vi.spyOn(safetyStockApi, "bootstrapSafetyStockFilters").mockRejectedValue(
      new ApiClientError("branch inválida", 400, "validation", { retryable: false }),
    );
    render(<SafetyStockPage />);
    await waitFor(() => {
      expect(screen.getByText("Filtros inválidos")).toBeTruthy();
      expect(screen.getByText("branch inválida")).toBeTruthy();
    });
  });

  it("permite retry da seção de filtros", async () => {
    const bootstrap = vi
      .spyOn(safetyStockApi, "bootstrapSafetyStockFilters")
      .mockRejectedValueOnce(new ApiClientError("indisponível", 503, "unavailable"))
      .mockResolvedValueOnce(filtersPayload);

    render(<SafetyStockPage />);
    await waitFor(() => expect(screen.getByText("Dados temporariamente indisponíveis")).toBeTruthy());

    fireEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));

    await waitFor(() => {
      expect(bootstrap).toHaveBeenCalledTimes(2);
      expect(screen.getByText("Total de matérias-primas")).toBeTruthy();
    });
  });

  it("permite retry do summary", async () => {
    mockApiSuccess();
    const summary = vi
      .mocked(safetyStockApi.fetchSafetyStockSummary)
      .mockRejectedValueOnce(new ApiClientError("falha", 503, "unavailable"))
      .mockResolvedValue(summaryPayload);

    render(<SafetyStockPage />);
    await waitFor(() => expect(screen.getByText("Dados temporariamente indisponíveis")).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));

    await waitFor(() => {
      expect(summary.mock.calls.length).toBeGreaterThanOrEqual(2);
      expect(screen.getByText("Total de matérias-primas")).toBeTruthy();
    });
  });

  it("permite retry da tabela", async () => {
    mockApiSuccess();
    const items = vi.mocked(safetyStockApi.fetchSafetyStockItems);
    items.mockRejectedValueOnce(new ApiClientError("falha", 503, "unavailable"));

    render(<SafetyStockPage />);
    await waitFor(() =>
      expect(screen.getByText("Dados temporariamente indisponíveis")).toBeTruthy(),
    );

    items.mockResolvedValue(itemsPayload);
    fireEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));

    await waitFor(() => {
      expect(items.mock.calls.length).toBeGreaterThanOrEqual(2);
      expect(screen.getByText("10010005")).toBeTruthy();
    });
  });
});
