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

import { AdminCentrosCustoPage } from "./AdminCentrosCustoPage";
import * as budgetApi from "../../api/budgetPlanningApi";
import { HttpRequestError } from "../../api/httpClient";

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
          id: "cc-01-205",
          branch: "01",
          code: "205",
          name: "TI SC",
          unit_code: "01",
          source: "erp",
          active: true,
        },
      ],
    },
  });

  vi.mocked(budgetApi.listErpCostCenters).mockImplementation(async (branch) => {
    if (branch === "01") {
      return {
        branch: "01",
        items: [
          { branch: "01", code: "1234", description: "Produção SC" },
          { branch: "01", code: "205", description: "TI SC" },
        ],
      };
    }
    return {
      branch: "02",
      items: [
        { branch: "02", code: "1234", description: "Produção ES" },
        { branch: "02", code: "999", description: "Só ES" },
      ],
    };
  });

  vi.mocked(budgetApi.createOrgCostCenterFromErp).mockResolvedValue({
    id: "new-1",
    branch: "01",
    code: "1234",
    name: "Produção SC",
    description: "Produção SC",
    unit_code: "01",
    source: "erp",
    active: true,
  });

  vi.mocked(budgetApi.updateOrgCostCenterIcon).mockImplementation(async (input) => ({
    id: "cc-01-205",
    branch: input.branch,
    code: input.code,
    name: "TI SC",
    unit_code: input.branch,
    source: "erp",
    active: true,
    icon_key: input.icon_key,
  }));
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("AdminCentrosCustoPage", () => {
  it("exige selecionar filial antes de consultar ERP", async () => {
    render(<AdminCentrosCustoPage />);
    await waitFor(() => expect(screen.getByText("Centros de Custo")).toBeTruthy());
    expect(
      screen.getByText(/Selecione uma filial para consultar os centros/i),
    ).toBeTruthy();
    expect(budgetApi.listErpCostCenters).not.toHaveBeenCalled();
  });

  it("consulta filial 01 e marca centro já cadastrado", async () => {
    render(<AdminCentrosCustoPage />);
    await waitFor(() => expect(screen.getByLabelText("Filial")).toBeTruthy());
    fireEvent.change(screen.getByLabelText("Filial"), {
      target: { value: "01" },
    });
    await waitFor(() => expect(budgetApi.listErpCostCenters).toHaveBeenCalledWith("01", expect.anything()));
    expect(screen.getByText("Filial 01 · 1234 — Produção SC")).toBeTruthy();
    expect(screen.getByText("Já cadastrado")).toBeTruthy();
    expect(screen.getByText("Disponível")).toBeTruthy();
  });

  it("consulta filial 02 e permite mesmo código sem colisão visual", async () => {
    render(<AdminCentrosCustoPage />);
    await waitFor(() => expect(screen.getByLabelText("Filial")).toBeTruthy());
    fireEvent.change(screen.getByLabelText("Filial"), {
      target: { value: "02" },
    });
    await waitFor(() =>
      expect(screen.getByText("Filial 02 · 1234 — Produção ES")).toBeTruthy(),
    );
    expect(screen.queryByText("Filial 01 · 1234 — Produção SC")).toBeNull();
  });

  it("filtra por código e descrição", async () => {
    render(<AdminCentrosCustoPage />);
    fireEvent.change(await screen.findByLabelText("Filial"), {
      target: { value: "01" },
    });
    await waitFor(() => expect(screen.getByText("Filial 01 · 205 — TI SC")).toBeTruthy());
    fireEvent.change(screen.getByPlaceholderText(/Código ou descrição/i), {
      target: { value: "produ" },
    });
    const erpSection = screen.getByRole("heading", {
      name: "Centros disponíveis no ERP",
    }).closest("section");
    expect(erpSection).toBeTruthy();
    expect(within(erpSection!).getByText("Filial 01 · 1234 — Produção SC")).toBeTruthy();
    expect(within(erpSection!).queryByText("Filial 01 · 205 — TI SC")).toBeNull();
  });

  it("cadastra a partir do ERP", async () => {
    render(<AdminCentrosCustoPage />);
    fireEvent.change(await screen.findByLabelText("Filial"), {
      target: { value: "01" },
    });
    await waitFor(() => expect(screen.getByText("Adicionar ao planejamento")).toBeTruthy());
    fireEvent.click(screen.getByText("Adicionar ao planejamento"));
    await waitFor(() =>
      expect(budgetApi.createOrgCostCenterFromErp).toHaveBeenCalledWith({
        branch: "01",
        code: "1234",
        unit_id: "01",
      }),
    );
    expect(await screen.findByText(/Centro cadastrado/i)).toBeTruthy();
  });

  it("trata erro do ERP", async () => {
    vi.mocked(budgetApi.listErpCostCenters).mockRejectedValueOnce(
      new Error("ERP indisponível"),
    );
    render(<AdminCentrosCustoPage />);
    fireEvent.change(await screen.findByLabelText("Filial"), {
      target: { value: "01" },
    });
    expect(await screen.findByText("ERP indisponível")).toBeTruthy();
  });

  it("trata 401 e 403", async () => {
    vi.mocked(budgetApi.listAdminScopes).mockRejectedValueOnce(
      new HttpRequestError("denied", 403),
    );
    render(<AdminCentrosCustoPage />);
    expect(await screen.findByText(/Acesso negado \(403\)/i)).toBeTruthy();
  });

  it("bloqueia acesso sem permissão", async () => {
    permissionsState.profile.permissions = ["planejamento-orcamentario.access"];
    render(<AdminCentrosCustoPage />);
    expect(await screen.findByText(/Sem permissão/i)).toBeTruthy();
  });

  it("permite personalizar ícone do centro cadastrado", async () => {
    render(<AdminCentrosCustoPage />);
    const trigger = await screen.findByRole("button", {
      name: /Ícone de Filial 01 · 205/i,
    });
    fireEvent.click(trigger);
    fireEvent.click(await screen.findByTitle("TI"));
    await waitFor(() => {
      expect(budgetApi.updateOrgCostCenterIcon).toHaveBeenCalledWith({
        branch: "01",
        code: "205",
        icon_key: "laptop",
      });
    });
  });
});
