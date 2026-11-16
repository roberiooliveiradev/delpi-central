// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { ApiRequestError } from "../../api/httpClient";
import {
  getSupplierPerformance,
  type SupplierPerformanceResponse,
} from "../../api/supplierPerformance";
import { SupplierPerformancePage } from "./SupplierPerformancePage";

vi.mock("../../api/supplierPerformance", () => ({
  getSupplierPerformance: vi.fn(),
}));
vi.mock("../../app/SuppliesSessionContext", () => {
  const session = { allowedUnits: ["01", "02"] };
  return { useSuppliesSession: () => session };
});

const component = {
  index: 80,
  assessed_count: 10,
  positive_count: 8,
  negative_count: 2,
  unknown_count: 0,
  conditional_count: 1,
  urgent_count: 0,
};
const payload: SupplierPerformanceResponse = {
  items: [
    {
      supplier_code: "000001",
      supplier_store: "01",
      supplier_name: "Fornecedor Exemplo",
      branches: ["01", "02"],
      quality: component,
      delivery: {
        ...component,
        index: 60,
        positive_count: 6,
        negative_count: 4,
      },
      idf: 74,
      quality_contribution: 56,
      delivery_contribution: 18,
      status: "complete",
    },
    {
      supplier_code: "000002",
      supplier_store: "02",
      supplier_name: "Outro fornecedor",
      branches: ["02"],
      quality: {
        ...component,
        index: null,
        assessed_count: 0,
        positive_count: 0,
        negative_count: 0,
        conditional_count: 0,
      },
      delivery: component,
      idf: null,
      quality_contribution: null,
      delivery_contribution: 24,
      status: "missing_quality",
    },
  ],
  summary: {
    suppliers: 2,
    evaluated: 1,
    incomplete: 1,
    average_idf: 74,
    average_quality: 80,
    average_delivery: 60,
    inspection_count: 10,
    receipt_count: 20,
  },
  methodology: {
    quality_weight: 70,
    delivery_weight: 30,
    scale: 100,
    classification_bands: null,
  },
  period: { from: "2026-11-01", to: "2026-11-16" },
  branches: ["01", "02"],
  calculated_at: "2026-11-16T08:00:00-03:00",
};

beforeEach(() => {
  vi.stubGlobal(
    "ResizeObserver",
    class {
      observe() {}
      disconnect() {}
      unobserve() {}
    },
  );
  window.history.replaceState(
    null,
    "",
    "?period=custom&from=2026-11-01&to=2026-11-16&branch=01,02",
  );
  vi.mocked(getSupplierPerformance).mockReset().mockResolvedValue(payload);
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function mount() {
  return render(
    <div className="dashboard-supplies-portal">
      <SupplierPerformancePage basePath="/apps/supplies" />
    </div>,
  );
}

describe("IDF page behavior", () => {
  it("loads the selected scope, searches suppliers and opens exact composition in a contained dialog", async () => {
    mount();
    expect(screen.getByText("Consultando Qualidade e Entrega…")).toBeTruthy();
    await screen.findByText("Fornecedor Exemplo");
    expect(getSupplierPerformance).toHaveBeenCalledWith(
      { branches: ["01", "02"], from: "2026-11-01", to: "2026-11-16" },
      expect.any(AbortSignal),
    );
    fireEvent.click(
      screen.getByRole("button", {
        name: "Ver composição de Fornecedor Exemplo, loja 01",
      }),
    );
    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByText("56,00 pontos na composição")).toBeTruthy();
    expect(within(dialog).getByText("18,00 pontos na composição")).toBeTruthy();
    expect(dialog.closest("[data-modal-contained='true']")).toBeTruthy();
    expect(dialog.closest(".dashboard-supplies-portal")).toBeTruthy();
    fireEvent.click(
      within(dialog).getByRole("button", { name: "Fechar detalhes" }),
    );
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    fireEvent.change(screen.getByLabelText("Buscar fornecedor"), {
      target: { value: "000002" },
    });
    expect(screen.queryByText("Fornecedor Exemplo")).toBeNull();
    expect(screen.getByText("Outro fornecedor")).toBeTruthy();
    fireEvent.click(
      screen.getByRole("button", {
        name: "Ver composição de Outro fornecedor, loja 02",
      }),
    );
    expect(
      within(await screen.findByRole("dialog")).getByText(
        "Aguardando base completa",
      ),
    ).toBeTruthy();
  });

  it("shows upstream error and recovers on retry instead of empty success", async () => {
    vi.mocked(getSupplierPerformance).mockRejectedValueOnce(
      new ApiRequestError("Unavailable", {
        status: 502,
        detail: "Não foi possível consultar o IDF.",
      }),
    );
    mount();
    await screen.findByText("Não foi possível consultar o IDF.");
    expect(screen.queryByText("Fornecedor Exemplo")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Atualizar" }));
    await screen.findByText("Fornecedor Exemplo");
  });

  it.each([403, 422])(
    "shows safe actionable error for HTTP %s",
    async (status) => {
      vi.mocked(getSupplierPerformance).mockRejectedValueOnce(
        new ApiRequestError("Failure", {
          status,
          detail: status === 403 ? "Acesso negado." : "Revise o período.",
        }),
      );
      mount();
      await screen.findByText(
        status === 403 ? "Acesso negado." : "Revise o período.",
      );
      expect(screen.queryByText("Desempenho por fornecedor")).toBeNull();
    },
  );

  it("handles an empty period without displaying a misleading score", async () => {
    vi.mocked(getSupplierPerformance).mockResolvedValueOnce({
      ...payload,
      items: [],
      summary: {
        ...payload.summary,
        suppliers: 0,
        evaluated: 0,
        incomplete: 0,
        average_idf: null,
      },
    });
    mount();
    await screen.findByText("Sem movimento neste período");
    expect(screen.queryByText("74,00")).toBeNull();
  });
});
