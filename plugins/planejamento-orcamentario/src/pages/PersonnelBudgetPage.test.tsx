import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";

vi.mock("@delpi/plugin-ui/index", () => ({
  sectionCardPacBemClasses: () => ({}),
  createDashboardSectionCard:
    () =>
    function SectionCard({ title, children }: { title: string; children: ReactNode }) {
      return (
        <section data-testid={`section-${title}`}>
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
}));

const permissionsMock = vi.hoisted(() => ({
  profile: {
    permissions: [
      "planejamento-orcamentario.access",
      "planejamento-orcamentario.personnel.view",
      "planejamento-orcamentario.personnel.edit",
    ],
  },
}));

vi.mock("../hooks/usePermissions", () => ({
  usePermissions: () => ({
    profile: permissionsMock.profile,
    loading: false,
    error: null,
  }),
}));

import { PersonnelBudgetPage } from "./PersonnelBudgetPage";
import * as budgetApi from "../api/budgetPlanningApi";
import { HttpRequestError } from "../api/httpClient";

vi.mock("../api/budgetPlanningApi");

const exercise = {
  id: "ex-2027",
  year: 2027,
  name: "PO 2027",
  status: "open" as const,
  is_active: true,
};

const resp01 = {
  id: "r1",
  exercise_id: "ex-2027",
  module: "personnel",
  user_sub: "user-1",
  unit_id: "01",
  branch: "01",
  area_id: "PROD",
  cost_center_id: "205",
  responsibility_type: "owner" as const,
  is_active: true,
};

const resp02 = {
  ...resp01,
  id: "r2",
  unit_id: "02",
  branch: "02",
};

const emptyPlan = {
  id: "plan-1",
  exercise_id: "ex-2027",
  unit_id: "01",
  cost_center_id: "205",
  status: "draft",
  version: 1,
  lines: [] as never[],
  position_count: 0,
  totals: {
    headcount_dec_2025: 0,
    headcount_oct_2026: 0,
    headcount_forecast: 0,
    headcount_dec_2027: 0,
  },
  incomplete_line_count: 0,
  is_complete: false,
};

function mockContext(overrides: Record<string, unknown> = {}) {
  vi.mocked(budgetApi.fetchBudgetContext).mockResolvedValue({
    exercise,
    guidance: { current_version: 1, acknowledged: true },
    scopes: [],
    capabilities: {
      access: true,
      guidance_view: true,
      guidance_manage: false,
      scopes_manage: false,
      admin: false,
    },
    modules_unlocked: true,
    ...overrides,
  } as never);
}

function openCc(unitId = "01") {
  window.history.pushState(
    {},
    "",
    `/apps/planejamento-orcamentario/pessoal?cost_center_id=205&unit_id=${unitId}`,
  );
}

beforeEach(() => {
  permissionsMock.profile = {
    permissions: [
      "planejamento-orcamentario.access",
      "planejamento-orcamentario.personnel.view",
      "planejamento-orcamentario.personnel.edit",
    ],
  };
  mockContext();
  vi.mocked(budgetApi.fetchMyPersonnelResponsibilities).mockResolvedValue({
    user_sub: "user-1",
    module: "personnel",
    items: [resp01, resp02],
  });
  vi.mocked(budgetApi.listErpCostCenters).mockImplementation(async (branch) => ({
    branch,
    items: [
      { branch, code: "205", description: branch === "01" ? "TI SC" : "TI ES" },
    ],
  }));
  vi.mocked(budgetApi.resolvePersonnelPlan).mockResolvedValue(emptyPlan as never);
  vi.mocked(budgetApi.getPersonnelPlan).mockResolvedValue(emptyPlan as never);
  vi.mocked(budgetApi.listPersonnelPlans).mockResolvedValue({
    items: [emptyPlan as never],
    pagination: { page: 1, page_size: 5, total: 1, has_more: false },
  });
  vi.mocked(budgetApi.listPersonnelPlanHistory).mockResolvedValue({ items: [] });
  window.history.pushState({}, "", "/apps/planejamento-orcamentario/pessoal");
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  vi.useRealTimers();
});

describe("PersonnelBudgetPage", () => {
  it("lista centros personnel separados por filial 01 e 02", async () => {
    render(<PersonnelBudgetPage />);
    await screen.findByText(/Filial 01 · 205 — TI SC/);
    expect(screen.getByText(/Filial 02 · 205 — TI ES/)).toBeTruthy();
    expect(budgetApi.fetchMyPersonnelResponsibilities).toHaveBeenCalledWith(
      "ex-2027",
      expect.anything(),
    );
  });

  it("estado vazio sem responsabilidades", async () => {
    vi.mocked(budgetApi.fetchMyPersonnelResponsibilities).mockResolvedValue({
      user_sub: "user-1",
      module: "personnel",
      items: [],
    });
    render(<PersonnelBudgetPage />);
    expect(await screen.findByText(/Nenhum centro atribuído/i)).toBeTruthy();
  });

  it("resolve plano ao selecionar centro (idempotente)", async () => {
    openCc("01");
    render(<PersonnelBudgetPage />);
    await waitFor(() => {
      expect(budgetApi.resolvePersonnelPlan).toHaveBeenCalledWith(
        {
          exercise_id: "ex-2027",
          unit_id: "01",
          cost_center_id: "205",
        },
        expect.anything(),
      );
    });
    expect(await screen.findByTestId("personnel-empty-lines")).toBeTruthy();
    expect(screen.getByTestId("personnel-totals")).toBeTruthy();
  });

  it("não mistura filiais no resolve", async () => {
    openCc("02");
    render(<PersonnelBudgetPage />);
    await waitFor(() => {
      expect(budgetApi.resolvePersonnelPlan).toHaveBeenCalledWith(
        expect.objectContaining({ unit_id: "02", cost_center_id: "205" }),
        expect.anything(),
      );
    });
  });

  it("cria linha com cargo livre, trim e acento; atualiza versão e totais", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    openCc("01");
    vi.mocked(budgetApi.createPersonnelPlanLine).mockResolvedValue({
      id: "line-1",
      plan_id: "plan-1",
      position_name: "Analista de Qualidade",
      headcount_dec_2025: 0,
      headcount_oct_2026: null,
      headcount_forecast: null,
      headcount_dec_2027: null,
      observations: null,
      version: 1,
      is_active: true,
      is_complete: false,
    });
    vi.mocked(budgetApi.getPersonnelPlan).mockResolvedValue({
      ...emptyPlan,
      position_count: 1,
      totals: { ...emptyPlan.totals, headcount_dec_2025: 0 },
      incomplete_line_count: 1,
      lines: [
        {
          id: "line-1",
          plan_id: "plan-1",
          position_name: "Analista de Qualidade",
          headcount_dec_2025: 0,
          version: 1,
          is_active: true,
        },
      ],
    } as never);

    render(<PersonnelBudgetPage />);
    await screen.findByTestId("personnel-add-line");
    fireEvent.click(screen.getByTestId("personnel-add-line"));
    const cargo = await screen.findByLabelText("Cargo");
    fireEvent.change(cargo, { target: { value: "  Analista de Qualidade  " } });
    fireEvent.change(screen.getByLabelText("Dez/2025"), { target: { value: "0" } });

    await vi.advanceTimersByTimeAsync(1100);

    await waitFor(() => {
      expect(budgetApi.createPersonnelPlanLine).toHaveBeenCalledWith(
        "plan-1",
        expect.objectContaining({
          position_name: "Analista de Qualidade",
          headcount_dec_2025: 0,
        }),
      );
    });
    await waitFor(() => {
      expect(budgetApi.getPersonnelPlan).toHaveBeenCalled();
    });
  });

  it("bloqueia cargo vazio na criação", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    openCc("01");
    render(<PersonnelBudgetPage />);
    await screen.findByTestId("personnel-add-line");
    fireEvent.click(screen.getByTestId("personnel-add-line"));
    fireEvent.change(screen.getByLabelText("Dez/2025"), { target: { value: "2" } });
    await vi.advanceTimersByTimeAsync(1100);
    expect(budgetApi.createPersonnelPlanLine).not.toHaveBeenCalled();
  });

  it("mostra erro de cargo duplicado", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    openCc("01");
    vi.mocked(budgetApi.resolvePersonnelPlan).mockResolvedValue({
      ...emptyPlan,
      position_count: 1,
      lines: [
        {
          id: "line-1",
          plan_id: "plan-1",
          position_name: "Operador de Produção",
          headcount_dec_2025: 1,
          version: 1,
          is_active: true,
        },
      ],
    } as never);
    render(<PersonnelBudgetPage />);
    await screen.findByDisplayValue("Operador de Produção");
    fireEvent.click(screen.getByTestId("personnel-add-line"));
    const inputs = screen.getAllByLabelText("Cargo");
    fireEvent.change(inputs[1], { target: { value: "operador de produção" } });
    await vi.advanceTimersByTimeAsync(1100);
    expect(await screen.findByText(/budget_personnel_line_duplicate_position/)).toBeTruthy();
    expect(budgetApi.createPersonnelPlanLine).not.toHaveBeenCalled();
  });

  it("rejeita headcount negativo", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    openCc("01");
    vi.mocked(budgetApi.resolvePersonnelPlan).mockResolvedValue({
      ...emptyPlan,
      lines: [
        {
          id: "line-1",
          plan_id: "plan-1",
          position_name: "Operador",
          headcount_dec_2025: 1,
          version: 1,
          is_active: true,
        },
      ],
    } as never);
    render(<PersonnelBudgetPage />);
    await screen.findByDisplayValue("Operador");
    fireEvent.change(screen.getByLabelText("Dez/2025"), { target: { value: "-3" } });
    await vi.advanceTimersByTimeAsync(1100);
    expect(await screen.findByText(/inteiro|negativo/i)).toBeTruthy();
    expect(budgetApi.updatePersonnelPlanLine).not.toHaveBeenCalled();
  });

  it("autosave de edição envia versão e atualiza após sucesso", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    openCc("01");
    vi.mocked(budgetApi.resolvePersonnelPlan).mockResolvedValue({
      ...emptyPlan,
      lines: [
        {
          id: "line-1",
          plan_id: "plan-1",
          position_name: "Operador",
          headcount_dec_2025: 1,
          version: 1,
          is_active: true,
        },
      ],
    } as never);
    vi.mocked(budgetApi.updatePersonnelPlanLine).mockResolvedValue({
      id: "line-1",
      plan_id: "plan-1",
      position_name: "Operador",
      headcount_dec_2025: 2,
      version: 2,
      is_active: true,
    });
    render(<PersonnelBudgetPage />);
    await screen.findByDisplayValue("Operador");
    fireEvent.change(screen.getByLabelText("Dez/2025"), { target: { value: "2" } });
    expect(screen.getByText("Alterado")).toBeTruthy();
    await vi.advanceTimersByTimeAsync(1100);
    await waitFor(() => {
      expect(budgetApi.updatePersonnelPlanLine).toHaveBeenCalledWith(
        "line-1",
        expect.objectContaining({ version: 1, headcount_dec_2025: 2 }),
      );
    });
    await waitFor(() => {
      expect(screen.getByText("Salvo")).toBeTruthy();
    });
  });

  it("conflito 409 oferece locais e oferece recarregar", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    openCc("01");
    vi.mocked(budgetApi.resolvePersonnelPlan).mockResolvedValue({
      ...emptyPlan,
      lines: [
        {
          id: "line-1",
          plan_id: "plan-1",
          position_name: "Operador",
          headcount_dec_2025: 1,
          version: 1,
          is_active: true,
        },
      ],
    } as never);
    vi.mocked(budgetApi.updatePersonnelPlanLine).mockRejectedValue(
      new HttpRequestError(
        "[budget_personnel_line_version_conflict] conflito",
        409,
        { code: "budget_personnel_line_version_conflict" },
      ),
    );
    render(<PersonnelBudgetPage />);
    await screen.findByDisplayValue("Operador");
    fireEvent.change(screen.getByLabelText("Dez/2025"), { target: { value: "9" } });
    await vi.advanceTimersByTimeAsync(1100);
    expect(
      await screen.findByText(/budget_personnel_line_version_conflict/),
    ).toBeTruthy();
    expect(screen.getByText(/valores locais preservados/i)).toBeTruthy();
    expect(screen.getByRole("button", { name: /recarregar a linha/i })).toBeTruthy();
    expect(screen.getByLabelText("Dez/2025")).toHaveProperty("value", "9");
  });

  it("arquiva linha com confirmação", async () => {
    openCc("01");
    vi.stubGlobal("confirm", vi.fn(() => true));
    vi.mocked(budgetApi.resolvePersonnelPlan).mockResolvedValue({
      ...emptyPlan,
      position_count: 1,
      lines: [
        {
          id: "line-1",
          plan_id: "plan-1",
          position_name: "Operador",
          headcount_dec_2025: 1,
          version: 1,
          is_active: true,
        },
      ],
    } as never);
    vi.mocked(budgetApi.archivePersonnelPlanLine).mockResolvedValue({
      id: "line-1",
      plan_id: "plan-1",
      position_name: "Operador",
      version: 2,
      is_active: false,
    } as never);
    render(<PersonnelBudgetPage />);
    await screen.findByDisplayValue("Operador");
    fireEvent.click(screen.getByRole("button", { name: /arquivar linha/i }));
    await waitFor(() => {
      expect(budgetApi.archivePersonnelPlanLine).toHaveBeenCalledWith("line-1");
    });
  });

  it("modo somente leitura com .view oculta edição", async () => {
    permissionsMock.profile = {
      permissions: [
        "planejamento-orcamentario.access",
        "planejamento-orcamentario.personnel.view",
      ],
    };
    openCc("01");
    vi.mocked(budgetApi.listPersonnelPlans).mockResolvedValue({
      items: [
        {
          ...emptyPlan,
          lines: [
            {
              id: "line-1",
              plan_id: "plan-1",
              position_name: "Operador",
              headcount_dec_2025: 1,
              version: 1,
              is_active: true,
            },
          ],
        } as never,
      ],
      pagination: { page: 1, page_size: 5, total: 1, has_more: false },
    });
    vi.mocked(budgetApi.getPersonnelPlan).mockResolvedValue({
      ...emptyPlan,
      lines: [
        {
          id: "line-1",
          plan_id: "plan-1",
          position_name: "Operador",
          headcount_dec_2025: 1,
          version: 1,
          is_active: true,
        },
      ],
    } as never);

    render(<PersonnelBudgetPage />);
    await screen.findByDisplayValue("Operador");
    expect(budgetApi.resolvePersonnelPlan).not.toHaveBeenCalled();
    expect(screen.queryByTestId("personnel-add-line")).toBeNull();
    expect(screen.queryByRole("button", { name: /arquivar/i })).toBeNull();
    expect(screen.getByLabelText("Cargo")).toHaveProperty("readOnly", true);
    expect(screen.getByText("Modo somente leitura")).toBeTruthy();
  });

  it("401 e 403 no boot", async () => {
    vi.mocked(budgetApi.fetchBudgetContext).mockRejectedValueOnce(
      new HttpRequestError("Sessão", 401),
    );
    const { unmount } = render(<PersonnelBudgetPage />);
    expect(await screen.findByText(/401/)).toBeTruthy();
    unmount();

    mockContext();
    vi.mocked(budgetApi.fetchMyPersonnelResponsibilities).mockRejectedValueOnce(
      new HttpRequestError("Negado", 403),
    );
    render(<PersonnelBudgetPage />);
    expect(await screen.findByText(/403/)).toBeTruthy();
  });

  it("exibe totais do plano", async () => {
    openCc("01");
    vi.mocked(budgetApi.resolvePersonnelPlan).mockResolvedValue({
      ...emptyPlan,
      position_count: 2,
      incomplete_line_count: 1,
      totals: {
        headcount_dec_2025: 10,
        headcount_oct_2026: 12,
        headcount_forecast: 11,
        headcount_dec_2027: 14,
      },
      lines: [],
    } as never);
    render(<PersonnelBudgetPage />);
    const totals = await screen.findByTestId("personnel-totals");
    expect(within(totals).getByText("2")).toBeTruthy();
    expect(within(totals).getByText("10")).toBeTruthy();
    expect(within(totals).getByText("Previsto", { exact: false })).toBeTruthy();
  });
});
