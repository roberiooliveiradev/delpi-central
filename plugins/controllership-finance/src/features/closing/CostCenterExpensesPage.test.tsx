import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@delpi/plugin-ui/index", async () => await import("../../test/pluginUiMock"));

const getMock = vi.fn();
const exportMock = vi.fn();
const saveMock = vi.fn();

vi.mock("../../api/costCenterExpensesApi", () => ({
  getCostCenterExpenses: (...args: unknown[]) => getMock(...args),
  exportCostCenterExpenses: (...args: unknown[]) => exportMock(...args),
  costCenterExpensesExportFilename: () => "r10-test.csv",
}));

vi.mock("../../api/documentsApi", () => ({
  saveDocumentBlob: (...args: unknown[]) => saveMock(...args),
}));

import { ApiError } from "../../api/httpClient";
import { CostCenterExpensesPage } from "./CostCenterExpensesPage";

const ITEM = {
  lineId: 1,
  branchCode: "01",
  document: "000123",
  series: "001",
  item: "001",
  sequence: "000001",
  productCode: "P0001",
  productDescription: "Produto Exemplo",
  productType: "PA",
  productGroup: "2000",
  documentType: "N",
  costCenter: "0404",
  costCenterDescription: "MANUTENCAO DE MAQUINAS FABRIL",
  costCenterCatalogStatus: "registered_analytic",
  accountCode: "31101001",
  tes: "101",
  cf: "1102",
  supplierCode: "F001",
  supplierStore: "01",
  supplierName: "Fornecedor X",
  warehouse: "01",
  orderNumber: "",
  entryDate: "20260905",
  issueDate: "20260901",
  quantity: "1.000000",
  unitValue: "100.000000",
  totalValue: "100.00",
  universe: "calculation",
  calculationExclusion: null,
  costClass: "UNCLASSIFIED",
  findings: [],
};

const FINDING = {
  reportId: "R10",
  findingId: "DV-R10-04-99",
  ruleId: "DV-R10-04",
  status: "POSSIBLE_DIVERGENCE",
  lineId: 99,
  sourceRecord: {
    document: "000999",
    series: "001",
    item: "003",
    productCode: "P0009",
    costCenterCode: null,
    tes: "101",
  },
  observedValues: { costCenter: "", productCode: "P0009" },
  findingExplanation:
    "Lançamento de despesa sem centro de custo preenchido.",
  evidenceRefs: ["doc-126#DV-R10-04"],
  erpReviewGuidance:
    "Conferir no Protheus o documento e o item da SD1.",
};

function payload(overrides: Record<string, unknown> = {}) {
  return {
    report: "cost-center-expenses",
    reportId: "R10",
    period: "2026-09",
    branchCode: "all",
    universe: "calculation",
    view: "all",
    status: "available",
    selection: {
      axis: "D1_DTDIGIT",
      grain: "sd1_item",
      excludedTes: ["001"],
      excludeMp: true,
      excludeBenefits: true,
    },
    pagination: {
      page: 1,
      page_size: 50,
      total_items: 1,
      universe_items: 1,
    },
    summary: {
      totalValue: "100.00",
      lineCount: 1,
      documentCount: 1,
      costCenterCount: 1,
      supplierCount: 1,
      findingCount: 0,
      unclassifiedCount: 1,
      byCostCenter: [
        {
          costCenter: "0404",
          costCenterDescription: "MANUTENCAO",
          lineCount: 1,
          totalValue: "100.00",
          findingCount: 0,
        },
      ],
      byProductType: [],
    },
    findings: [],
    findingsTruncated: false,
    rulesCatalog: [],
    parityStatus: "PENDING",
    parityNotes: ["Paridade oficial pendente."],
    items: [ITEM],
    ...overrides,
  };
}

function renderPage(props?: { reportContext?: { period: string } }) {
  return render(<CostCenterExpensesPage {...props} />);
}

afterEach(() => {
  cleanup();
  getMock.mockReset();
  exportMock.mockReset();
  saveMock.mockReset();
});

describe("CostCenterExpensesPage — R10", () => {
  it("renderiza totais, itens e estado de paridade da apuração", async () => {
    getMock.mockResolvedValue(payload());
    renderPage({ reportContext: { period: "2026-09" } });

    await screen.findByText("Disponível", {}, { timeout: 3000 });
    expect(
      screen.getAllByText(/100,00/).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText(/Produto Exemplo/)).toBeTruthy();
    expect(screen.getByText(/Paridade oficial: pendente/)).toBeTruthy();
    expect(getMock).toHaveBeenCalledWith(
      expect.objectContaining({
        period: "2026-09",
        universe: "calculation",
      }),
      expect.anything(),
    );
  });

  it("universo investigação refaz a consulta com universe=investigation e exibe o aviso", async () => {
    getMock.mockResolvedValue(
      payload({ universe: "investigation" }),
    );
    renderPage({ reportContext: { period: "2026-09" } });

    await screen.findByText("Disponível");
    fireEvent.change(
      screen.getByLabelText("Universo"),
      { target: { value: "investigation" } },
    );
    await waitFor(() =>
      expect(getMock).toHaveBeenLastCalledWith(
        expect.objectContaining({ universe: "investigation" }),
        expect.anything(),
      ),
    );
    await screen.findByText(/Universo investigativo/);
  });

  it("visão divergências encaminha view=divergences", async () => {
    getMock.mockResolvedValue(payload());
    renderPage({ reportContext: { period: "2026-09" } });

    await screen.findByText("Disponível");
    fireEvent.change(screen.getByLabelText("Visão"), {
      target: { value: "divergences" },
    });
    await waitFor(() =>
      expect(getMock).toHaveBeenLastCalledWith(
        expect.objectContaining({ view: "divergences" }),
        expect.anything(),
      ),
    );
  });

  it("achados aparecem como possível divergência com orientação ERP", async () => {
    getMock.mockResolvedValue(
      payload({
        findings: [FINDING],
        summary: {
          ...payload().summary,
          findingCount: 1,
        },
        items: [
          {
            ...ITEM,
            lineId: 99,
            costCenter: null,
            costCenterCatalogStatus: "not_applicable",
            findings: ["DV-R10-04"],
          },
        ],
      }),
    );
    renderPage({ reportContext: { period: "2026-09" } });

    await waitFor(() =>
      expect(
        screen.getAllByText(/Possíveis divergências/).length,
      ).toBeGreaterThan(0),
    );
    expect(
      screen.getAllByText(/sem centro de custo preenchido/).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Protheus/).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText("Sem centro de custo").length,
    ).toBeGreaterThan(0);
  });

  it("erro da API exibe banner tipado", async () => {
    getMock.mockRejectedValue(
      new ApiError("falha", { status: 503, code: "unavailable" }),
    );
    renderPage({ reportContext: { period: "2026-09" } });

    await waitFor(() =>
      expect(getMock).toHaveBeenCalled(),
    );
    await waitFor(() =>
      expect(
        screen.getAllByText(/falha|indisponível|erro/i).length,
      ).toBeGreaterThan(0),
    );
  });

  it("sem dados para o filtro mostra estado honesto", async () => {
    getMock.mockResolvedValue(
      payload({
        status: "no_matching_items",
        items: [],
        summary: {
          ...payload().summary,
          lineCount: 0,
          totalValue: "0.00",
          byCostCenter: [],
        },
      }),
    );
    renderPage({ reportContext: { period: "2026-09" } });

    await waitFor(() =>
      expect(
        screen.getAllByText(/Sem dados para o filtro/).length,
      ).toBeGreaterThan(0),
    );
  });
});
