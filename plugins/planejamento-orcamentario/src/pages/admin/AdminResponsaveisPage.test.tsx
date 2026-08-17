import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";

const permissionsState = {
  profile: {
    permissions: [
      "planejamento-orcamentario.access",
      "planejamento-orcamentario.scopes.manage",
      "planejamento-orcamentario.admin",
    ],
  },
  loading: false,
  error: null as string | null,
};

vi.mock("@delpi/plugin-ui/index", () => ({
  sectionCardPacBemClasses: () => ({}),
  UserDirectoryPicker: ({
    onChange,
    labels,
  }: {
    onChange: (users: Array<{ id: string; name: string; email: string }>) => void;
    labels?: { title?: string };
  }) => (
    <div>
      <span>{labels?.title ?? "picker"}</span>
      <button
        type="button"
        onClick={() =>
          onChange([{ id: "sub-maria", name: "Maria da Silva", email: "maria@delpi.local" }])
        }
      >
        Selecionar Maria
      </button>
    </div>
  ),
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

vi.mock("../../hooks/usePermissions", () => ({
  usePermissions: () => permissionsState,
}));

import { AdminResponsaveisPage } from "./AdminResponsaveisPage";
import * as budgetApi from "../../api/budgetPlanningApi";
import { HttpRequestError } from "../../api/httpClient";

vi.mock("../../api/budgetPlanningApi");

const exercise = {
  id: "ex-2027",
  year: 2027,
  name: "PO 2027",
  status: "open" as const,
  is_active: true,
};

const catalog = {
  units: [
    { code: "01", name: "SC" },
    { code: "02", name: "ES" },
  ],
  areas: [{ code: "PROD", name: "Produção", unit_code: "01" }],
  cost_centers: [
    {
      id: "cc1",
      branch: "01",
      code: "1234",
      name: "Produção",
      unit_code: "01",
      area_code: "PROD",
      active: true,
    },
    {
      id: "cc2",
      branch: "02",
      code: "1234",
      name: "Produção ES",
      unit_code: "02",
      active: true,
    },
  ],
};

const row = {
  id: "r1",
  exercise_id: "ex-2027",
  module: "capex",
  user_sub: "sub-maria",
  user_name_snapshot: "Maria da Silva",
  user_email_snapshot: "maria@delpi.local",
  unit_id: "01",
  area_id: "PROD",
  cost_center_id: "1234",
  responsibility_type: "owner" as const,
  valid_from: "2026-01-01",
  valid_until: "2026-12-31",
  is_active: true,
  updated_at: "2026-08-04T12:00:00Z",
};

const rowPersonnel = {
  ...row,
  id: "r2",
  module: "personnel" as const,
};

beforeEach(() => {
  permissionsState.profile.permissions = [
    "planejamento-orcamentario.access",
    "planejamento-orcamentario.scopes.manage",
    "planejamento-orcamentario.admin",
  ];
  permissionsState.loading = false;
  vi.mocked(budgetApi.listAdminExercises).mockResolvedValue([exercise]);
  vi.mocked(budgetApi.listAdminScopes).mockResolvedValue({ items: [], catalog });
  vi.mocked(budgetApi.listAdminBudgetResponsibilities).mockResolvedValue({
    items: [row, rowPersonnel],
    pagination: { page: 1, page_size: 20, total: 2, has_more: false },
  });
  vi.mocked(budgetApi.createAdminBudgetResponsibilityPair).mockResolvedValue({
    capex: row,
    personnel: rowPersonnel,
  });
  vi.mocked(budgetApi.updateAdminBudgetResponsibility).mockResolvedValue({
    ...row,
    responsibility_type: "collaborator",
  });
  vi.mocked(budgetApi.deactivateAdminBudgetResponsibility).mockResolvedValue({
    ...row,
    is_active: false,
  });
  vi.mocked(budgetApi.reactivateAdminBudgetResponsibility).mockResolvedValue(row);
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

function createSection() {
  return screen.getByTestId("section-Novo vínculo");
}

describe("AdminResponsaveisPage", () => {
  it("carrega listagem e exibe vínculo unificado CAPEX+Pessoal", async () => {
    render(<AdminResponsaveisPage />);
    await screen.findByText("Maria da Silva");
    expect(budgetApi.listAdminBudgetResponsibilities).toHaveBeenCalled();
    expect(screen.getAllByText(/Filial 01 · 1234 — Produção/).length).toBeGreaterThan(0);
    expect(screen.getByText("CAPEX")).toBeTruthy();
    expect(screen.getByText("Pessoal")).toBeTruthy();
    expect(screen.getAllByText("Maria da Silva")).toHaveLength(1);
  });

  it("aplica filtros e paginação via API", async () => {
    vi.mocked(budgetApi.listAdminBudgetResponsibilities).mockResolvedValue({
      items: [row],
      pagination: { page: 1, page_size: 20, total: 40, has_more: true },
    });
    render(<AdminResponsaveisPage />);
    await screen.findByText("Filtros");
    const filters = screen.getByTestId("section-Filtros");
    fireEvent.change(within(filters).getByLabelText("Status"), {
      target: { value: "active" },
    });
    await waitFor(() => {
      expect(budgetApi.listAdminBudgetResponsibilities).toHaveBeenCalledWith(
        expect.objectContaining({ is_active: true, page: 1 }),
        expect.anything(),
      );
    });
    fireEvent.change(within(filters).getByLabelText("Tipo"), {
      target: { value: "collaborator" },
    });
    await waitFor(() => {
      expect(budgetApi.listAdminBudgetResponsibilities).toHaveBeenCalledWith(
        expect.objectContaining({ responsibility_type: "collaborator" }),
        expect.anything(),
      );
    });
    fireEvent.click(screen.getByRole("button", { name: "Próxima" }));
    await waitFor(() => {
      expect(budgetApi.listAdminBudgetResponsibilities).toHaveBeenCalledWith(
        expect.objectContaining({ page: 2 }),
        expect.anything(),
      );
    });
  });

  it("pesquisa usuário no filtro via diretório", async () => {
    render(<AdminResponsaveisPage />);
    await screen.findByText("Filtros");
    const filters = screen.getByTestId("section-Filtros");
    fireEvent.click(within(filters).getByRole("button", { name: "Selecionar Maria" }));
    await waitFor(() => {
      expect(budgetApi.listAdminBudgetResponsibilities).toHaveBeenCalledWith(
        expect.objectContaining({ user_sub: "sub-maria" }),
        expect.anything(),
      );
    });
  });

  it("cria vínculo com unidade → área → centro e resumo", async () => {
    render(<AdminResponsaveisPage />);
    await screen.findByText("Maria da Silva");
    fireEvent.click(screen.getByRole("button", { name: /Novo vínculo/i }));
    const form = createSection();
    fireEvent.click(within(form).getByRole("button", { name: "Selecionar Maria" }));
    fireEvent.change(within(form).getByLabelText("Filial"), { target: { value: "01" } });
    fireEvent.change(within(form).getByLabelText("Área"), { target: { value: "PROD" } });
    fireEvent.change(within(form).getByLabelText("Centro de custo"), {
      target: { value: "1234" },
    });
    await within(form).findByText(/Maria da Silva será responsável/i);
    fireEvent.click(within(form).getByRole("button", { name: "Salvar vínculo" }));
    await waitFor(() => {
      expect(budgetApi.createAdminBudgetResponsibilityPair).toHaveBeenCalledWith(
        expect.objectContaining({
          user_sub: "sub-maria",
          unit_id: "01",
          area_id: "PROD",
          cost_center_id: "1234",
          responsibility_type: "owner",
        }),
      );
    });
  });

  it("bloqueia período inválido na criação", async () => {
    render(<AdminResponsaveisPage />);
    fireEvent.click(await screen.findByRole("button", { name: /Novo vínculo/i }));
    const form = createSection();
    fireEvent.click(within(form).getByRole("button", { name: "Selecionar Maria" }));
    fireEvent.change(within(form).getByLabelText("Filial"), { target: { value: "01" } });
    fireEvent.change(within(form).getByLabelText("Centro de custo"), {
      target: { value: "1234" },
    });
    fireEvent.change(within(form).getByLabelText("Vigência início"), {
      target: { value: "2026-12-01" },
    });
    fireEvent.change(within(form).getByLabelText("Vigência fim"), {
      target: { value: "2026-01-01" },
    });
    fireEvent.click(within(form).getByRole("button", { name: "Salvar vínculo" }));
    await screen.findByText(/não pode ser anterior/i);
    expect(budgetApi.createAdminBudgetResponsibilityPair).not.toHaveBeenCalled();
  });

  it("trata duplicidade retornada pela API", async () => {
    vi.mocked(budgetApi.createAdminBudgetResponsibilityPair).mockRejectedValueOnce(
      new Error(
        "Já existe vínculo ativo para este usuário, exercício, filial e centro de custo (CAPEX e Pessoal).",
      ),
    );
    render(<AdminResponsaveisPage />);
    fireEvent.click(await screen.findByRole("button", { name: /Novo vínculo/i }));
    const form = createSection();
    fireEvent.click(within(form).getByRole("button", { name: "Selecionar Maria" }));
    fireEvent.change(within(form).getByLabelText("Filial"), { target: { value: "01" } });
    fireEvent.change(within(form).getByLabelText("Centro de custo"), {
      target: { value: "1234" },
    });
    fireEvent.click(within(form).getByRole("button", { name: "Salvar vínculo" }));
    await screen.findByText(/Já existe vínculo ativo/i);
  });

  it("edita tipo/vigência e desativa o par com confirmação", async () => {
    vi.stubGlobal(
      "confirm",
      vi.fn(() => true),
    );
    render(<AdminResponsaveisPage />);
    await screen.findByText("Maria da Silva");
    fireEvent.click(screen.getByRole("button", { name: /Editar/i }));
    const edit = screen.getByTestId("section-Alterar tipo e vigência");
    fireEvent.change(within(edit).getByLabelText("Tipo"), {
      target: { value: "collaborator" },
    });
    fireEvent.click(within(edit).getByRole("button", { name: "Salvar alterações" }));
    await waitFor(() => {
      expect(budgetApi.updateAdminBudgetResponsibility).toHaveBeenCalledTimes(2);
      expect(budgetApi.updateAdminBudgetResponsibility).toHaveBeenCalledWith(
        "r1",
        expect.objectContaining({ responsibility_type: "collaborator" }),
      );
      expect(budgetApi.updateAdminBudgetResponsibility).toHaveBeenCalledWith(
        "r2",
        expect.objectContaining({ responsibility_type: "collaborator" }),
      );
    });
    fireEvent.click(screen.getByRole("button", { name: /Desativar/i }));
    await waitFor(() => {
      expect(budgetApi.deactivateAdminBudgetResponsibility).toHaveBeenCalledTimes(2);
      expect(budgetApi.deactivateAdminBudgetResponsibility).toHaveBeenCalledWith(
        "r1",
        "Desativação pela administração",
      );
      expect(budgetApi.deactivateAdminBudgetResponsibility).toHaveBeenCalledWith(
        "r2",
        "Desativação pela administração",
      );
    });
  });

  it("reativa vínculo inativo", async () => {
    vi.mocked(budgetApi.listAdminBudgetResponsibilities).mockResolvedValue({
      items: [
        { ...row, is_active: false },
        { ...rowPersonnel, is_active: false },
      ],
      pagination: { page: 1, page_size: 20, total: 2, has_more: false },
    });
    render(<AdminResponsaveisPage />);
    await screen.findByText("Reativar");
    fireEvent.click(screen.getByRole("button", { name: /Reativar/i }));
    await waitFor(() => {
      expect(budgetApi.reactivateAdminBudgetResponsibility).toHaveBeenCalledTimes(2);
      expect(budgetApi.reactivateAdminBudgetResponsibility).toHaveBeenCalledWith("r1");
      expect(budgetApi.reactivateAdminBudgetResponsibility).toHaveBeenCalledWith("r2");
    });
  });

  it("nega acesso sem permissão administrativa", async () => {
    permissionsState.profile.permissions = ["planejamento-orcamentario.access"];
    render(<AdminResponsaveisPage />);
    await screen.findByText(/Sem permissão para gerenciar responsáveis/i);
  });

  it("exibe erro 403 na listagem", async () => {
    vi.mocked(budgetApi.listAdminBudgetResponsibilities).mockRejectedValue(
      new HttpRequestError("forbidden", 403),
    );
    render(<AdminResponsaveisPage />);
    await screen.findByText(/Acesso negado \(403\)/i);
  });

  it("exibe erro 401 na listagem", async () => {
    vi.mocked(budgetApi.listAdminBudgetResponsibilities).mockRejectedValue(
      new HttpRequestError("unauthorized", 401),
    );
    render(<AdminResponsaveisPage />);
    await screen.findByText(/Sessão expirada \(401\)/i);
  });

  it("exibe estado vazio", async () => {
    vi.mocked(budgetApi.listAdminBudgetResponsibilities).mockResolvedValue({
      items: [],
      pagination: { page: 1, page_size: 20, total: 0, has_more: false },
    });
    render(<AdminResponsaveisPage />);
    await screen.findByText(/Nenhum vínculo encontrado/i);
  });

  it("exibe skeleton enquanto carrega", async () => {
    vi.mocked(budgetApi.listAdminBudgetResponsibilities).mockImplementation(
      () => new Promise(() => undefined) as never,
    );
    render(<AdminResponsaveisPage />);
    expect(await screen.findByLabelText("Carregando listagem")).toBeTruthy();
  });
});

