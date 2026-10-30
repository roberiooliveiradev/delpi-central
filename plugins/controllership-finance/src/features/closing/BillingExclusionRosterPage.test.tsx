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

vi.mock("../../api/billingExclusionRosterApi", () => ({
  getBillingExclusionRoster: (...args: unknown[]) => getMock(...args),
  exportBillingExclusionRoster: (...args: unknown[]) =>
    exportMock(...args),
  billingExclusionExportFilename: () => "r11-test.csv",
}));

vi.mock("../../api/documentsApi", () => ({
  saveDocumentBlob: (...args: unknown[]) => saveMock(...args),
}));

import { ApiError } from "../../api/httpClient";
import { BillingExclusionRosterPage } from "./BillingExclusionRosterPage";

const ITEM = {
  lineId: 1,
  branchCode: "01",
  document: "103033",
  series: "001",
  item: "002",
  productCode: "90350001",
  productDescription: "Servico Industrializacao",
  productType: "SV",
  productGroup: "9035",
  tes: "594",
  tesDescription: "VENDA DE PRODUCAO DO ESTABELECIMENTO",
  cf: "5101",
  customerCode: "C001",
  customerStore: "01",
  customerName: "Cliente X",
  accountCode: "31101001",
  warehouse: "01",
  orderNumber: "",
  issueDate: "20260905",
  quantity: "1.000000",
  unitPrice: "100.000000",
  totalValue: "100.00",
  stockCost: "0.00",
  tesStockMovement: "N",
  tesDuplicateFlag: "S",
  documentItemCount: 1,
  hasStockSiblingItem: false,
  selectionStatus: "matches_historical_criteria",
  costStatus: "structural_zero_expected",
  findings: ["DV-R11-03"],
};

const FINDING = {
  reportId: "R11",
  findingId: "DV-R11-03-1",
  ruleId: "DV-R11-03",
  status: "POSSIBLE_DIVERGENCE",
  lineId: 1,
  sourceRecord: {
    document: "103033",
    series: "001",
    item: "002",
    productCode: "90350001",
    tes: "594",
    cf: "5101",
  },
  observedValues: { document: "103033", documentItemCount: 1 },
  findingExplanation:
    "Documento da seleção histórica sem item-irmão que movimente estoque.",
  evidenceRefs: ["doc-126#DV-R11-03"],
  erpReviewGuidance:
    "Conferir no Protheus o documento e o item da SD2.",
};

function payload(overrides: Record<string, unknown> = {}) {
  return {
    report: "billing-exclusion-roster",
    reportId: "R11",
    period: "2026-09",
    branchCode: "all",
    view: "candidates",
    status: "available",
    selection: {
      axis: "D2_EMISSAO",
      grain: "sd2_item",
      observedCriteria: { productGroup: "9035", tes: "594" },
    },
    pagination: {
      page: 1,
      page_size: 50,
      total_items: 1,
      population_items: 1,
    },
    summary: {
      totalValue: "100.00",
      lineCount: 1,
      documentCount: 1,
      customerCount: 1,
      zeroCostCount: 1,
      missingStockSiblingDocumentCount: 1,
      findingCount: 1,
      candidateLineCount: 1,
      outOfCriteriaLineCount: 0,
      byTes: [{ tes: "594", lineCount: 1, totalValue: "100.00" }],
      byProductGroup: [
        { productGroup: "9035", lineCount: 1, totalValue: "100.00" },
      ],
    },
    findings: [FINDING],
    findingsTruncated: false,
    rulesCatalog: [],
    parityStatus: "PENDING",
    parityNotes: ["Paridade oficial pendente."],
    items: [ITEM],
    ...overrides,
  };
}

function renderPage(props?: { reportContext?: { period: string } }) {
  return render(<BillingExclusionRosterPage {...props} />);
}

afterEach(() => {
  cleanup();
  getMock.mockReset();
  exportMock.mockReset();
  saveMock.mockReset();
});

describe("BillingExclusionRosterPage — R11", () => {
  it("renderiza totais, itens e aviso de lista investigativa", async () => {
    getMock.mockResolvedValue(payload());
    renderPage({ reportContext: { period: "2026-09" } });

    await screen.findByText("Disponível", {}, { timeout: 3000 });
    expect(
      screen.getAllByText(/100,00/).length,
    ).toBeGreaterThan(0);
    expect(screen.getByText(/Servico Industrializacao/)).toBeTruthy();
    expect(
      screen.getByText(/não é exclusão oficial/),
    ).toBeTruthy();
    expect(screen.getByText(/Paridade oficial: pendente/)).toBeTruthy();
    expect(getMock).toHaveBeenCalledWith(
      expect.objectContaining({
        period: "2026-09",
        view: "candidates",
      }),
      expect.anything(),
    );
  });

  it("visão fora do critério refaz a consulta e exibe o aviso investigativo", async () => {
    getMock.mockResolvedValue(
      payload({ view: "out_of_criteria" }),
    );
    renderPage({ reportContext: { period: "2026-09" } });

    await screen.findByText("Disponível");
    fireEvent.change(
      screen.getByLabelText("Visão"),
      { target: { value: "out_of_criteria" } },
    );
    await waitFor(() =>
      expect(getMock).toHaveBeenLastCalledWith(
        expect.objectContaining({ view: "out_of_criteria" }),
        expect.anything(),
      ),
    );
    await screen.findByText(/Visão investigativa/);
  });

  it("finding de item-irmão ausente aparece como possível divergência", async () => {
    getMock.mockResolvedValue(payload());
    renderPage({ reportContext: { period: "2026-09" } });

    await waitFor(() =>
      expect(
        screen.getAllByText(/sem item-irmão/i).length,
      ).toBeGreaterThan(0),
    );
    expect(
      screen.getAllByText(/Protheus/).length,
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText(/Candidata/).length,
    ).toBeGreaterThan(0);
  });

  it("filtros de grupo, documento e TES são encaminhados", async () => {
    getMock.mockResolvedValue(payload());
    renderPage({ reportContext: { period: "2026-09" } });

    await screen.findByText("Disponível");
    fireEvent.change(screen.getByLabelText("Grupo"), {
      target: { value: "9035" },
    });
    fireEvent.change(screen.getByLabelText("Documento"), {
      target: { value: "103033" },
    });
    fireEvent.change(screen.getByLabelText("TES"), {
      target: { value: "594" },
    });
    await waitFor(() =>
      expect(getMock).toHaveBeenLastCalledWith(
        expect.objectContaining({
          productGroup: "9035",
          document: "103033",
          tes: "594",
        }),
        expect.anything(),
      ),
    );
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
        findings: [],
        summary: {
          ...payload().summary,
          lineCount: 0,
          totalValue: "0.00",
          byTes: [],
          byProductGroup: [],
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
