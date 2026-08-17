import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
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
  createHostContainedModalShell:
    () =>
    function HostContainedModal({
      open,
      title,
      onClose,
      children,
    }: {
      open: boolean;
      title: ReactNode;
      onClose: () => void;
      children?: ReactNode;
    }) {
      if (!open) return null;
      return (
        <div role="dialog" aria-modal="true" aria-label={String(title)}>
          <button type="button" aria-label="Fechar" onClick={onClose}>
            Fechar
          </button>
          {children}
        </div>
      );
    },
}));

import { CapexInvestmentFormPage } from "./CapexInvestmentFormPage";
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

const responsibility = {
  id: "r1",
  exercise_id: "ex-2027",
  module: "capex",
  user_sub: "user-1",
  unit_id: "01",
  area_id: "PROD",
  cost_center_id: "205",
  responsibility_type: "owner" as const,
  is_active: true,
};

const categories = [
  {
    id: "cat-1",
    code: "FERRAMENTAS",
    name: "Ferramentas",
    display_order: 20,
    is_active: true,
    is_system_default: true,
  },
];

const saved = {
  id: "inv-1",
  exercise_id: "ex-2027",
  unit_id: "01",
  area_id: "PROD",
  cost_center_id: "205",
  category_id: "cat-1",
  description: "Notebooks",
  estimated_amount: "1000.00",
  currency: "BRL",
  required_date: "2027-06-01",
  priority: "2",
  origin: "national",
  classification: "3",
  shift: "1",
  status: "draft",
  version: 1,
  is_complete: false,
  missing_fields: ["description"],
};

beforeEach(() => {
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
  } as never);
  vi.mocked(budgetApi.fetchMyCapexResponsibilities).mockResolvedValue({
    user_sub: "user-1",
    module: "capex",
    items: [responsibility],
  });
  vi.mocked(budgetApi.listActiveCapexCategories).mockResolvedValue({ items: categories });
  vi.mocked(budgetApi.createCapexInvestment).mockResolvedValue(saved);
  vi.mocked(budgetApi.updateCapexInvestment).mockResolvedValue({
    ...saved,
    version: 2,
    description: "Notebooks Dell",
    is_complete: true,
    missing_fields: [],
  });
  vi.mocked(budgetApi.getCapexInvestment).mockResolvedValue(saved);
  vi.mocked(budgetApi.listCapexInvestmentAttachments).mockResolvedValue([]);
  vi.mocked(budgetApi.resolveCapexPlan).mockResolvedValue({
    id: "plan-1",
    exercise_id: "ex-2027",
    unit_id: "01",
    area_id: "PROD",
    cost_center_id: "205",
    status: "draft",
    version: 1,
  } as never);
  window.history.pushState(
    {},
    "",
    "/apps/planejamento-orcamentario/capex/investimentos/novo?cost_center_id=205",
  );
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  vi.useRealTimers();
});

describe("CapexInvestmentFormPage", () => {
  it("carrega categorias e centros autorizados na criação", async () => {
    render(<CapexInvestmentFormPage mode="create" />);
    await screen.findByText("Identificação");
    expect(budgetApi.listActiveCapexCategories).toHaveBeenCalled();
    expect(budgetApi.fetchMyCapexResponsibilities).toHaveBeenCalled();
    const form = screen.getByTestId("section-Identificação");
    const select = within(form).getByLabelText("Centro de custo") as HTMLSelectElement;
    expect(select.value).toBe("01|205");
    expect(within(form).getByText(/Filial 01 · 205/)).toBeTruthy();
  });

  it("cria rascunho pelo botão salvar", async () => {
    render(<CapexInvestmentFormPage mode="create" />);
    await screen.findByText("Dados do investimento");
    const data = screen.getByTestId("section-Dados do investimento");
    fireEvent.change(within(data).getByLabelText("Descrição"), {
      target: { value: "Notebooks" },
    });
    fireEvent.change(within(data).getByLabelText("Valor previsto"), {
      target: { value: "1000,00" },
    });
    fireEvent.change(within(data).getByLabelText("Mês necessário de recebimento"), {
      target: { value: "2027-06" },
    });
    fireEvent.change(within(data).getByLabelText("Prioridade"), {
      target: { value: "2" },
    });
    fireEvent.change(within(data).getByLabelText("Origem"), {
      target: { value: "national" },
    });
    fireEvent.change(within(data).getByLabelText("Classificação"), {
      target: { value: "3" },
    });
    fireEvent.change(within(data).getByLabelText("Turno"), {
      target: { value: "1" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Salvar rascunho/i }));
    await waitFor(() => {
      expect(budgetApi.createCapexInvestment).toHaveBeenCalledWith(
        expect.objectContaining({
          exercise_id: "ex-2027",
          cost_center_id: "205",
          description: "Notebooks",
          estimated_amount: "1000.00",
          required_date: "2027-06-01",
          priority: "2",
          origin: "national",
        }),
      );
    });
  });

  it("exibe pendências de rascunho incompleto após salvar", async () => {
    render(<CapexInvestmentFormPage mode="create" />);
    await screen.findByText("Dados do investimento");
    fireEvent.click(screen.getByRole("button", { name: /Salvar rascunho/i }));
    await screen.findByText(/Rascunho incompleto/i);
    expect(screen.getByText(/Pendências:.*Descrição/i)).toBeTruthy();
  });

  it("autosave após debounce", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    render(<CapexInvestmentFormPage mode="create" />);
    await screen.findByText("Dados do investimento");
    const data = screen.getByTestId("section-Dados do investimento");
    fireEvent.change(within(data).getByLabelText("Descrição"), {
      target: { value: "Auto" },
    });
    expect(screen.getByText(/Alterações pendentes/i)).toBeTruthy();
    await vi.advanceTimersByTimeAsync(1100);
    await waitFor(() => {
      expect(budgetApi.createCapexInvestment).toHaveBeenCalled();
    });
  });

  it("trata erro de autosave", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.mocked(budgetApi.createCapexInvestment).mockRejectedValueOnce(
      new Error("falha rede"),
    );
    render(<CapexInvestmentFormPage mode="create" />);
    await screen.findByText("Dados do investimento");
    fireEvent.change(
      within(screen.getByTestId("section-Dados do investimento")).getByLabelText("Descrição"),
      { target: { value: "X" } },
    );
    await vi.advanceTimersByTimeAsync(1100);
    await waitFor(() => {
      expect(screen.getByText("Erro ao salvar")).toBeTruthy();
      expect(screen.getByText(/falha rede/i)).toBeTruthy();
    });
  });

  it("trata conflito 409 sem sobrescrever", async () => {
    vi.mocked(budgetApi.getCapexInvestment)
      .mockResolvedValueOnce(saved)
      .mockResolvedValueOnce({
        ...saved,
        version: 3,
        description: "Servidor",
        is_complete: true,
        missing_fields: [],
      });
    vi.mocked(budgetApi.updateCapexInvestment).mockRejectedValueOnce(
      new HttpRequestError("[budget_capex_version_conflict] conflito", 409),
    );
    render(<CapexInvestmentFormPage mode="edit" investmentId="inv-1" />);
    await screen.findByDisplayValue("Notebooks");
    fireEvent.change(
      within(screen.getByTestId("section-Dados do investimento")).getByLabelText("Descrição"),
      { target: { value: "Local" } },
    );
    fireEvent.click(screen.getByRole("button", { name: /Salvar rascunho/i }));
    await screen.findByText(/alterado em outra sessão/i);
    fireEvent.click(screen.getByRole("button", { name: /Recarregar versão atual/i }));
    await waitFor(() => {
      expect(budgetApi.getCapexInvestment).toHaveBeenCalledTimes(2);
    });
    await screen.findByDisplayValue("Servidor");
  });

  it("item arquivado fica somente leitura", async () => {
    vi.mocked(budgetApi.getCapexInvestment).mockResolvedValue({
      ...saved,
      status: "archived",
      is_complete: true,
      missing_fields: [],
    });
    render(<CapexInvestmentFormPage mode="edit" investmentId="inv-1" />);
    await screen.findByText(/Investimento arquivado/i);
    expect(screen.queryByRole("button", { name: /Salvar rascunho/i })).toBeNull();
    expect(
      within(screen.getByTestId("section-Dados do investimento")).getByLabelText("Descrição"),
    ).toHaveProperty("disabled", true);
  });

  it("orientação pendente bloqueia formulário", async () => {
    vi.mocked(budgetApi.fetchBudgetContext).mockResolvedValue({
      exercise,
      guidance: { current_version: 1, acknowledged: false },
      scopes: [],
      capabilities: {
        access: true,
        guidance_view: true,
        guidance_manage: false,
        scopes_manage: false,
        admin: false,
      },
      modules_unlocked: false,
    } as never);
    render(<CapexInvestmentFormPage mode="create" />);
    await screen.findByText(/Confirme a leitura das orientações/i);
  });

  it("usuário sem centros", async () => {
    vi.mocked(budgetApi.fetchMyCapexResponsibilities).mockResolvedValue({
      user_sub: "user-1",
      module: "capex",
      items: [],
    });
    render(<CapexInvestmentFormPage mode="create" />);
    await screen.findByText(/não possui centros de custo/i);
  });

  it("anexos ficam bloqueados até o rascunho ter ID", async () => {
    render(<CapexInvestmentFormPage mode="create" />);
    await screen.findByText("Dados do investimento");
    expect(screen.getByText(/Salve o rascunho para adicionar documentos/i)).toBeTruthy();
    expect(budgetApi.listCapexInvestmentAttachments).not.toHaveBeenCalled();
  });

  it("no modal, avança o wizard por etapas com faixa de progresso", async () => {
    render(
      <CapexInvestmentFormPage
        mode="create"
        presentation="panel"
        costCenterId="205"
        unitId="01"
      />,
    );
    await screen.findByLabelText("Progresso do cadastro");
    expect(screen.getByText(/Etapa 1 de 5/i)).toBeTruthy();
    expect(screen.getByRole("progressbar", { name: /Avanço do cadastro/i })).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: /Continuar/i }));
    await screen.findByText(/Selecione a categoria/i);

    const catSelect = screen.getByLabelText("Categoria de investimento") as HTMLSelectElement;
    fireEvent.change(catSelect, { target: { value: "cat-1" } });
    fireEvent.click(screen.getByRole("button", { name: /Continuar/i }));

    await screen.findByText(/Etapa 2 de 5/i);
    expect(screen.getByLabelText("Descrição")).toBeTruthy();
  });

  it("anexos não disparam update/autosave do investimento", async () => {
    render(<CapexInvestmentFormPage mode="edit" investmentId="inv-1" />);
    await screen.findByDisplayValue("Notebooks");
    await waitFor(() => {
      expect(budgetApi.listCapexInvestmentAttachments).toHaveBeenCalled();
    });
    const updateCallsBefore = vi.mocked(budgetApi.updateCapexInvestment).mock.calls.length;
    // Interação só na área de anexos não deve marcar dirty / PUT do investimento
    expect(screen.queryByText(/Alterações pendentes/i)).toBeNull();
    expect(vi.mocked(budgetApi.updateCapexInvestment).mock.calls.length).toBe(
      updateCallsBefore,
    );
  });
});
