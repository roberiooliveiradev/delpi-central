import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@delpi/plugin-ui/index", () => ({
  exportPayloadToXlsx: vi.fn(),
}));

vi.mock("../api/safetyStockApi", () => ({
  fetchSafetyStockItems: vi.fn(),
}));

import { fetchSafetyStockItems } from "../api/safetyStockApi";
import type { SafetyStockItem, SafetyStockQueryParams } from "../types/safetyStock";
import {
  buildSafetyStockExportPayload,
  fetchAllSafetyStockItemsForExport,
  safetyStockItemToExportRow,
} from "./exportSafetyStockExcel";

const fetchItemsMock = vi.mocked(fetchSafetyStockItems);

function sampleItem(overrides: Partial<SafetyStockItem> = {}): SafetyStockItem {
  return {
    product_code: "10010005",
    product_description: "CABO",
    product_type: "MP",
    unit: "MT",
    product_group: "10",
    branch: "01",
    blocked: false,
    safety_stock: 100,
    primary_stock: 40,
    work_in_process_stock: 0,
    warehouse_50_stock: 0,
    warehouse_98_stock: 10,
    warehouse_99_stock: 5,
    work_in_process_committed: 0,
    work_in_process_available: 0,
    deficit_quantity: 45,
    status: "below_safety_stock",
    ...overrides,
  };
}

const baseParams: SafetyStockQueryParams = {
  branch: "01",
  includeBlocked: false,
  productGroup: "",
  unit: "",
  search: "",
  status: "",
  includeWithoutSafetyStock: true,
  sortBy: "product_code",
  sortDirection: "asc",
};

describe("exportSafetyStockExcel", () => {
  beforeEach(() => {
    fetchItemsMock.mockReset();
  });

  it("monta linha com saldo consolidado e situação em português", () => {
    const row = safetyStockItemToExportRow(sampleItem());
    expect(row.display_balance).toBe(55);
    expect(row.status).toContain("Abaixo");
    expect(row.blocked).toBe("Não");
  });

  it("monta payload com colunas esperadas", () => {
    const payload = buildSafetyStockExportPayload([sampleItem()]);
    expect(payload.columns.map((column) => column.key)).toContain("display_balance");
    expect(payload.rows).toHaveLength(1);
  });

  it("P0: pagina até o total mesmo quando a API responde page_size menor que o pedido", async () => {
    fetchItemsMock
      .mockResolvedValueOnce({
        items: Array.from({ length: 50 }, (_, index) =>
          sampleItem({ product_code: `A${index}` }),
        ),
        page: 1,
        page_size: 50,
        total: 120,
        total_pages: 3,
        sort_by: "product_code",
        sort_direction: "asc",
      })
      .mockResolvedValueOnce({
        items: Array.from({ length: 50 }, (_, index) =>
          sampleItem({ product_code: `B${index}` }),
        ),
        page: 2,
        page_size: 50,
        total: 120,
        total_pages: 3,
        sort_by: "product_code",
        sort_direction: "asc",
      })
      .mockResolvedValueOnce({
        items: Array.from({ length: 20 }, (_, index) =>
          sampleItem({ product_code: `C${index}` }),
        ),
        page: 3,
        page_size: 50,
        total: 120,
        total_pages: 3,
        sort_by: "product_code",
        sort_direction: "asc",
      });

    const items = await fetchAllSafetyStockItemsForExport(baseParams);

    expect(items).toHaveLength(120);
    expect(fetchItemsMock).toHaveBeenCalledTimes(3);
    expect(fetchItemsMock.mock.calls[0]?.[2]).toBe(200);
  });

  it("irmão: uma única página completa encerra sem segunda chamada", async () => {
    fetchItemsMock.mockResolvedValueOnce({
      items: Array.from({ length: 30 }, (_, index) =>
        sampleItem({ product_code: `S${index}` }),
      ),
      page: 1,
      page_size: 200,
      total: 30,
      total_pages: 1,
      sort_by: "product_code",
      sort_direction: "asc",
    });

    const items = await fetchAllSafetyStockItemsForExport(baseParams);
    expect(items).toHaveLength(30);
    expect(fetchItemsMock).toHaveBeenCalledTimes(1);
  });

  it("negativo: consulta vazia devolve lista vazia", async () => {
    fetchItemsMock.mockResolvedValueOnce({
      items: [],
      page: 1,
      page_size: 200,
      total: 0,
      total_pages: 0,
      sort_by: "product_code",
      sort_direction: "asc",
    });

    const items = await fetchAllSafetyStockItemsForExport(baseParams);
    expect(items).toEqual([]);
    expect(fetchItemsMock).toHaveBeenCalledTimes(1);
  });
});
