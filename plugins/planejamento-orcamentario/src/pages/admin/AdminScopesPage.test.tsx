import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
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
          onChange([{ id: "sub-abc", name: "Ana Gestora", email: "ana@delpi.local" }])
        }
      >
        Selecionar Ana
      </button>
    </div>
  ),
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
}));

vi.mock("../../hooks/usePermissions", () => ({
  usePermissions: () => permissionsState,
}));

import { AdminScopesPage } from "./AdminScopesPage";
import * as budgetApi from "../../api/budgetPlanningApi";

vi.mock("../../api/budgetPlanningApi");

beforeEach(() => {
  permissionsState.profile.permissions = [
    "planejamento-orcamentario.access",
    "planejamento-orcamentario.scopes.manage",
    "planejamento-orcamentario.admin",
  ];
  permissionsState.loading = false;
  permissionsState.error = null;
  vi.mocked(budgetApi.listAdminScopes).mockResolvedValue({
    items: [],
    catalog: {
      units: [
        { code: "01", name: "SC" },
        { code: "02", name: "ES" },
      ],
      areas: [],
      cost_centers: [
        {
          id: "a",
          branch: "01",
          code: "205",
          name: "TI SC",
          unit_code: "01",
          active: true,
        },
        {
          id: "b",
          branch: "02",
          code: "205",
          name: "TI ES",
          unit_code: "02",
          active: true,
        },
      ],
    },
  });
  vi.mocked(budgetApi.createAdminScope).mockResolvedValue({
    id: "s1",
    user_sub: "sub-abc",
    unit_code: "01",
    cost_center_code: "205",
    scope_level: "cost_center",
    active: true,
  });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("AdminScopesPage", () => {
  it("filtra centros por filial e limpa CC ao trocar filial", async () => {
    render(<AdminScopesPage />);
    await screen.findByText("Novo escopo");
    const unitSelect = screen.getByLabelText("Filial");
    const ccSelect = screen.getByLabelText("Centro de custo") as HTMLSelectElement;

    fireEvent.change(unitSelect, { target: { value: "01" } });
    expect(Array.from(ccSelect.options).some((o) => o.text.includes("Filial 01 · 205"))).toBe(
      true,
    );
    expect(Array.from(ccSelect.options).some((o) => o.text.includes("Filial 02 · 205"))).toBe(
      false,
    );

    fireEvent.change(ccSelect, { target: { value: "205" } });
    expect(ccSelect.value).toBe("205");

    fireEvent.change(unitSelect, { target: { value: "02" } });
    expect(ccSelect.value).toBe("");
    expect(Array.from(ccSelect.options).some((o) => o.text.includes("Filial 02 · 205"))).toBe(
      true,
    );
  });

  it("exige seleção no diretório e cria escopo com sub real", async () => {
    render(<AdminScopesPage />);
    await screen.findByText("Novo escopo");
    fireEvent.change(screen.getByLabelText("Filial"), { target: { value: "01" } });
    fireEvent.change(screen.getByLabelText("Centro de custo"), { target: { value: "205" } });
    const submit = screen.getByRole("button", { name: "Vincular escopo" }) as HTMLButtonElement;
    expect(submit.disabled).toBe(true);

    fireEvent.click(screen.getByRole("button", { name: "Selecionar Ana" }));
    await screen.findByText(/Ana Gestora/);
    expect(submit.disabled).toBe(false);
    fireEvent.click(submit);
    await waitFor(() => {
      expect(budgetApi.createAdminScope).toHaveBeenCalledWith(
        expect.objectContaining({
          user_sub: "sub-abc",
          user_name: "Ana Gestora",
          user_email: "ana@delpi.local",
          unit_code: "01",
          cost_center_code: "205",
        }),
      );
    });
  });

  it("bloqueia acesso sem permissão administrativa de escopos", async () => {
    permissionsState.profile.permissions = ["planejamento-orcamentario.access"];
    render(<AdminScopesPage />);
    await screen.findByText(/Sem permissão para gerenciar escopos/i);
  });
});
