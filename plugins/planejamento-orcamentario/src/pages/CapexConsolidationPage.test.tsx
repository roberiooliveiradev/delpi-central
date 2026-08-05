import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";

vi.mock("@delpi/plugin-ui/index", () => ({
  sectionCardPacBemClasses: () => ({}),
  createDashboardSectionCard:
    () =>
    function SectionCard({ title, children }: { title: string; children: ReactNode }) {
      return (
        <section>
          <h2>{title}</h2>
          {children}
        </section>
      );
    },
  createDashboardLoadingActivityCard:
    () =>
    function LoadingActivityCard({ title }: { title: string }) {
      return <div>{title}</div>;
    },
  createDashboardStateBox:
    () =>
    function StateBox({ children }: { children: ReactNode }) {
      return <div role="alert">{children}</div>;
    },
  createSimpleKpiCard:
    () =>
    function KpiCard({ title, value }: { title: string; value: string }) {
      return (
        <article>
          <h3>{title}</h3>
          <p>{value}</p>
        </article>
      );
    },
}));

const permissionsState = {
  profile: {
    permissions: [
      "planejamento-orcamentario.capex.consolidation.view",
      "planejamento-orcamentario.capex.export",
      "planejamento-orcamentario.access",
    ],
  } as { permissions: string[] } | null,
  loading: false,
  error: null as string | null,
};

vi.mock("../hooks/usePermissions", () => ({
  usePermissions: () => permissionsState,
}));

import { CapexConsolidationPage } from "./CapexConsolidationPage";
import * as budgetApi from "../api/budgetPlanningApi";
import { HttpRequestError } from "../api/httpClient";

vi.mock("../api/budgetPlanningApi");

const summary = {
  currency: "BRL",
  total_estimated_amount: "3500.50",
  investment_count: 2,
  cost_center_count: 2,
  plans_draft_count: 0,
  plans_submitted_count: 1,
  plans_changes_requested_count: 0,
  plans_rejected_count: 0,
  plans_approved_count: 1,
  approved_amount: "2500.50",
  in_review_amount: "1000.00",
  incomplete_investment_count: 0,
};

const groupPayload = (code: string, amount: string) => ({
  exercise: { id: "ex-1", year: 2027, name: "PO 2027" },
  filters: {},
  group_by: "unit",
  currency: "BRL",
  total_estimated_amount: amount,
  items: [
    {
      code,
      description: code,
      investment_count: 1,
      total_amount: amount,
      percent_of_total: "100.00",
      unit_id: "01",
      area_id: "PROD",
      cost_center_id: code,
    },
  ],
});

function mockHappyPath() {
  vi.mocked(budgetApi.fetchBudgetContext).mockResolvedValue({
    exercise: { id: "ex-1", year: 2027, name: "PO 2027", status: "open" },
    modules_unlocked: true,
    guidance: { current_version: 1, acknowledged: true },
    scopes: [],
    capabilities: {
      access: true,
      guidance_view: true,
      guidance_manage: false,
      scopes_manage: false,
      admin: false,
    },
  } as never);
  vi.mocked(budgetApi.listActiveCapexCategories).mockResolvedValue({
    items: [{ id: "cat-1", code: "FERR", name: "Ferramentas", is_active: true }],
  } as never);
  vi.mocked(budgetApi.listAdminScopes).mockResolvedValue({
    items: [],
    catalog: {
      units: [{ code: "01", name: "SC" }],
      areas: [{ code: "PROD", name: "Produção", unit_code: "01" }],
      cost_centers: [
        { code: "205", name: "TI", unit_code: "01", area_code: "PROD", active: true },
        { code: "210", name: "Manut", unit_code: "01", area_code: "PROD", active: true },
      ],
    },
  } as never);
  vi.mocked(budgetApi.listAdminExercises).mockResolvedValue([
    { id: "ex-1", year: 2027, name: "PO 2027", status: "open" },
  ] as never);
  vi.mocked(budgetApi.fetchCapexConsolidationSummary).mockResolvedValue({
    exercise: { id: "ex-1", year: 2027, name: "PO 2027" },
    filters: {},
    summary,
  } as never);
  const groupMock = vi.fn().mockResolvedValue(groupPayload("205", "1000.00"));
  vi.mocked(budgetApi.fetchCapexConsolidationByUnit).mockImplementation(groupMock);
  vi.mocked(budgetApi.fetchCapexConsolidationByArea).mockImplementation(groupMock);
  vi.mocked(budgetApi.fetchCapexConsolidationByCostCenter).mockImplementation(groupMock);
  vi.mocked(budgetApi.fetchCapexConsolidationByCategory).mockImplementation(groupMock);
  vi.mocked(budgetApi.fetchCapexConsolidationByPriority).mockImplementation(groupMock);
  vi.mocked(budgetApi.fetchCapexConsolidationByOrigin).mockImplementation(groupMock);
  vi.mocked(budgetApi.fetchCapexConsolidationByMonth).mockImplementation(groupMock);
  vi.mocked(budgetApi.fetchCapexConsolidationByPlanStatus).mockImplementation(groupMock);
  vi.mocked(budgetApi.listCapexConsolidationDetails).mockResolvedValue({
    exercise: { id: "ex-1", year: 2027, name: "PO 2027" },
    filters: {},
    items: [
      {
        id: "inv-1",
        exercise_id: "ex-1",
        unit_id: "01",
        area_id: "PROD",
        cost_center_id: "205",
        description: "Notebooks",
        estimated_amount: "1000.00",
        currency: "BRL",
        is_complete: true,
        plan_status: "submitted",
        plan_id: "plan-1",
        required_date: "2027-06-01",
      },
    ],
    pagination: { page: 1, page_size: 20, total: 1, total_pages: 1 },
  } as never);
}

beforeEach(() => {
  permissionsState.profile = {
    permissions: [
      "planejamento-orcamentario.capex.consolidation.view",
      "planejamento-orcamentario.capex.export",
      "planejamento-orcamentario.access",
      "planejamento-orcamentario.admin",
    ],
  };
  permissionsState.loading = false;
  permissionsState.error = null;
  mockHappyPath();
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("CapexConsolidationPage", () => {
  it("nega acesso sem permissão", async () => {
    permissionsState.profile = { permissions: ["planejamento-orcamentario.access"] };
    render(<CapexConsolidationPage />);
    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toMatch(/Acesso negado/i);
  }, 15000);

  it("carrega resumo, indicadores e agrupamentos", async () => {
    render(<CapexConsolidationPage />);
    await waitFor(() => {
      expect(budgetApi.fetchCapexConsolidationSummary).toHaveBeenCalled();
    });
    expect(await screen.findByText("Valor total previsto")).toBeTruthy();
    expect(screen.getByText("R$ 3.500,50")).toBeTruthy();
    expect(screen.getByText("Valor por unidade")).toBeTruthy();
    expect(screen.getByText("Valor por mês (Data Rcbto)")).toBeTruthy();
    expect(screen.getByText("Distribuição por status do planejamento")).toBeTruthy();
    expect(await screen.findByText("Notebooks")).toBeTruthy();
  }, 15000);

  it("aplica e limpa filtros enviando parâmetros ao backend", async () => {
    render(<CapexConsolidationPage />);
    await waitFor(() => expect(budgetApi.fetchCapexConsolidationSummary).toHaveBeenCalled());

    fireEvent.change(screen.getByLabelText("Filial"), { target: { value: "01" } });
    fireEvent.change(screen.getByLabelText("Prioridade"), { target: { value: "2" } });
    fireEvent.click(screen.getByRole("button", { name: /Aplicar filtros/i }));

    await waitFor(() => {
      expect(budgetApi.fetchCapexConsolidationSummary).toHaveBeenCalledWith(
        expect.objectContaining({ unit_id: "01", priority: "2", exercise_id: "ex-1" }),
        expect.anything(),
      );
    });

    fireEvent.click(screen.getByRole("button", { name: /Limpar filtros/i }));
    await waitFor(() => {
      const last = vi.mocked(budgetApi.fetchCapexConsolidationSummary).mock.calls.at(-1)?.[0];
      expect(last).toEqual(expect.objectContaining({ exercise_id: "ex-1" }));
      expect(last?.unit_id).toBeUndefined();
      expect(last?.priority).toBeUndefined();
    });
  }, 15000);

  it("encadeia filial → área → centro de custo", async () => {
    render(<CapexConsolidationPage />);
    await waitFor(() => expect(budgetApi.fetchCapexConsolidationSummary).toHaveBeenCalled());

    fireEvent.change(screen.getByLabelText("Filial"), { target: { value: "01" } });
    fireEvent.change(screen.getByLabelText("Área"), { target: { value: "PROD" } });
    const cc = screen.getByLabelText("Centro de custo") as HTMLSelectElement;
    expect([...cc.options].some((o) => o.value === "205" || o.text.includes("Filial 01 · 205"))).toBe(
      true,
    );

    fireEvent.change(screen.getByLabelText("Filial"), { target: { value: "" } });
    expect((screen.getByLabelText("Área") as HTMLSelectElement).value).toBe("");
    expect((screen.getByLabelText("Centro de custo") as HTMLSelectElement).value).toBe("");
  }, 15000);

  it("exibe estado sem dados", async () => {
    vi.mocked(budgetApi.fetchCapexConsolidationSummary).mockResolvedValue({
      exercise: { id: "ex-1", year: 2027, name: "PO 2027" },
      filters: {},
      summary: { ...summary, investment_count: 0, total_estimated_amount: "0.00" },
    } as never);
    vi.mocked(budgetApi.listCapexConsolidationDetails).mockResolvedValue({
      exercise: { id: "ex-1" },
      filters: {},
      items: [],
      pagination: { page: 1, page_size: 20, total: 0, total_pages: 0 },
    } as never);
    render(<CapexConsolidationPage />);
    expect(
      await screen.findByText(/Nenhum investimento encontrado/i),
    ).toBeTruthy();
  }, 15000);

  it("mostra botão de exportação só com permissão e baixa arquivo autenticado", async () => {
    const blob = new Blob(["xlsx"], {
      type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    });
    vi.mocked(budgetApi.exportCapexConsolidationXlsx).mockResolvedValue({
      blob,
      filename: "planejamento-capex-2027-2026-08-05.xlsx",
    });

    const clickSpy = vi.fn();
    const originalCreate = document.createElement.bind(document);
    vi.spyOn(document, "createElement").mockImplementation((tag: string) => {
      const el = originalCreate(tag);
      if (tag === "a") {
        Object.defineProperty(el, "click", { value: clickSpy });
      }
      return el;
    });
    Object.defineProperty(URL, "createObjectURL", {
      configurable: true,
      writable: true,
      value: vi.fn(() => "blob:mock"),
    });
    Object.defineProperty(URL, "revokeObjectURL", {
      configurable: true,
      writable: true,
      value: vi.fn(),
    });

    render(<CapexConsolidationPage />);
    await waitFor(() => expect(budgetApi.fetchCapexConsolidationSummary).toHaveBeenCalled());
    const btn = await screen.findByRole("button", { name: /Exportar Excel/i });
    fireEvent.click(btn);

    await waitFor(() => {
      expect(budgetApi.exportCapexConsolidationXlsx).toHaveBeenCalledWith(
        expect.objectContaining({ exercise_id: "ex-1" }),
      );
    });
    expect(clickSpy).toHaveBeenCalled();
    expect(await screen.findByText(/planejamento-capex-2027-2026-08-05\.xlsx/)).toBeTruthy();
  }, 15000);

  it("oculta exportação sem permissão", async () => {
    permissionsState.profile = {
      permissions: ["planejamento-orcamentario.capex.consolidation.view"],
    };
    render(<CapexConsolidationPage />);
    await waitFor(() => expect(budgetApi.fetchCapexConsolidationSummary).toHaveBeenCalled());
    expect(screen.queryByRole("button", { name: /Exportar Excel/i })).toBeNull();
  }, 15000);

  it("trata conflito de moedas na exportação", async () => {
    vi.mocked(budgetApi.exportCapexConsolidationXlsx).mockRejectedValue(
      new HttpRequestError("conflict", 422, {
        code: "budget_capex_consolidation_currency_conflict",
      }),
    );
    render(<CapexConsolidationPage />);
    await waitFor(() => expect(budgetApi.fetchCapexConsolidationSummary).toHaveBeenCalled());
    fireEvent.click(await screen.findByRole("button", { name: /Exportar Excel/i }));
    await waitFor(() => {
      expect(screen.getAllByText(/moedas diferentes/i).length).toBeGreaterThan(0);
    });
  }, 15000);

  it("trata erro 403 de consolidação", async () => {
    vi.mocked(budgetApi.fetchCapexConsolidationSummary).mockRejectedValue(
      new HttpRequestError("forbidden", 403, {
        code: "budget_capex_consolidation_forbidden",
      }),
    );
    render(<CapexConsolidationPage />);
    expect(await screen.findByText(/não tem permissão/i)).toBeTruthy();
  }, 15000);

  it("trata erro 401", async () => {
    vi.mocked(budgetApi.fetchCapexConsolidationSummary).mockRejectedValue(
      new HttpRequestError("expired", 401),
    );
    render(<CapexConsolidationPage />);
    expect(await screen.findByText(/Sessão expirada/i)).toBeTruthy();
  }, 15000);

  it("trata falha de rede", async () => {
    vi.mocked(budgetApi.fetchCapexConsolidationSummary).mockRejectedValue(
      new HttpRequestError("offline", 0),
    );
    render(<CapexConsolidationPage />);
    expect(await screen.findByText(/Falha de rede/i)).toBeTruthy();
  }, 15000);

  it("mantém dados válidos quando um agrupamento falha", async () => {
    vi.mocked(budgetApi.fetchCapexConsolidationByMonth).mockRejectedValue(
      new Error("falha mês"),
    );
    render(<CapexConsolidationPage />);
    await waitFor(() => expect(screen.getByText("R$ 3.500,50")).toBeTruthy());
    expect(screen.getByText("Valor por unidade")).toBeTruthy();
    expect(await screen.findByText(/falha mês|Não foi possível/i)).toBeTruthy();
  }, 15000);

  it("ordena detalhamento via backend", async () => {
    render(<CapexConsolidationPage />);
    await waitFor(() => expect(budgetApi.listCapexConsolidationDetails).toHaveBeenCalled());
    fireEvent.click(screen.getByRole("button", { name: /^Valor$/i }));
    await waitFor(() => {
      expect(budgetApi.listCapexConsolidationDetails).toHaveBeenCalledWith(
        expect.objectContaining({ sort_by: "estimated_amount", sort_dir: "desc" }),
        expect.anything(),
      );
    });
  }, 15000);
});
