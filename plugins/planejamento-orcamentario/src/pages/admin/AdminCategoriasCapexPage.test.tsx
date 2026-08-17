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

import { AdminCategoriasCapexPage } from "./AdminCategoriasCapexPage";
import * as budgetApi from "../../api/budgetPlanningApi";

vi.mock("../../api/budgetPlanningApi");

const row = {
  id: "c1",
  code: "FERRAMENTAS",
  name: "Ferramentas",
  description: "Kit geral",
  display_order: 20,
  is_active: true,
  is_system_default: true,
};

beforeEach(() => {
  permissionsState.profile.permissions = [
    "planejamento-orcamentario.access",
    "planejamento-orcamentario.scopes.manage",
    "planejamento-orcamentario.admin",
  ];
  permissionsState.loading = false;
  vi.mocked(budgetApi.listAdminCapexCategories).mockResolvedValue({ items: [row] });
  vi.mocked(budgetApi.createAdminCapexCategory).mockResolvedValue({
    ...row,
    id: "c2",
    code: "NOVA",
    name: "Nova",
    is_system_default: false,
  });
  vi.mocked(budgetApi.updateAdminCapexCategory).mockResolvedValue({
    ...row,
    name: "Ferramentas editada",
  });
  vi.mocked(budgetApi.deactivateAdminCapexCategory).mockResolvedValue({
    ...row,
    is_active: false,
  });
  vi.mocked(budgetApi.reactivateAdminCapexCategory).mockResolvedValue(row);
  vi.mocked(budgetApi.uploadAdminCapexCategoryIconImage).mockResolvedValue({
    ...row,
    has_custom_icon: true,
    icon_image_mime: "image/png",
  });
  vi.mocked(budgetApi.clearAdminCapexCategoryIconImage).mockResolvedValue({
    ...row,
    has_custom_icon: false,
  });
  vi.mocked(budgetApi.fetchCapexCategoryIconImageBlob).mockResolvedValue(
    new Blob(["x"], { type: "image/png" }),
  );
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
  vi.unstubAllGlobals();
});

describe("AdminCategoriasCapexPage", () => {
  it("carrega listagem", async () => {
    render(<AdminCategoriasCapexPage />);
    await screen.findByText("Ferramentas");
    expect(screen.getByText("FERRAMENTAS")).toBeTruthy();
    expect(budgetApi.listAdminCapexCategories).toHaveBeenCalled();
  });

  it("aplica pesquisa e filtro de status no backend", async () => {
    render(<AdminCategoriasCapexPage />);
    await screen.findByText("Filtros");
    const filters = screen.getByTestId("section-Filtros");
    fireEvent.change(within(filters).getByLabelText("Pesquisar"), {
      target: { value: "Veíc" },
    });
    fireEvent.click(within(filters).getByRole("button", { name: "Aplicar pesquisa" }));
    await waitFor(() => {
      expect(budgetApi.listAdminCapexCategories).toHaveBeenCalledWith(
        expect.objectContaining({ q: "Veíc" }),
        expect.anything(),
      );
    });
    fireEvent.change(within(filters).getByLabelText("Status"), {
      target: { value: "inactive" },
    });
    await waitFor(() => {
      expect(budgetApi.listAdminCapexCategories).toHaveBeenCalledWith(
        expect.objectContaining({ is_active: false }),
        expect.anything(),
      );
    });
  });

  it("cria categoria", async () => {
    render(<AdminCategoriasCapexPage />);
    fireEvent.click(await screen.findByRole("button", { name: /Nova categoria/i }));
    const form = screen.getByTestId("section-Nova categoria");
    fireEvent.change(within(form).getByLabelText("Código"), { target: { value: "NOVA" } });
    fireEvent.change(within(form).getByLabelText("Nome"), { target: { value: "Nova" } });
    fireEvent.click(within(form).getByRole("button", { name: "Salvar categoria" }));
    await waitFor(() => {
      expect(budgetApi.createAdminCapexCategory).toHaveBeenCalledWith(
        expect.objectContaining({ code: "NOVA", name: "Nova", icon_key: null }),
      );
    });
  });

  it("edita nome/ordem e ícone após selecionar tile", async () => {
    render(<AdminCategoriasCapexPage />);
    fireEvent.click(await screen.findByRole("button", { name: /Ferramentas/i }));
    fireEvent.click(screen.getByRole("button", { name: /^Editar$/i }));
    const edit = screen.getByTestId("section-Editar categoria");
    fireEvent.change(within(edit).getByLabelText("Nome"), {
      target: { value: "Ferramentas editada" },
    });
    fireEvent.click(within(edit).getByRole("button", { name: "Salvar alterações" }));
    await waitFor(() => {
      expect(budgetApi.updateAdminCapexCategory).toHaveBeenCalledWith(
        "c1",
        expect.objectContaining({ name: "Ferramentas editada", icon_key: null }),
      );
    });
  });

  it("envia imagem customizada ao editar categoria", async () => {
    render(<AdminCategoriasCapexPage />);
    fireEvent.click(await screen.findByRole("button", { name: /Ferramentas/i }));
    fireEvent.click(screen.getByRole("button", { name: /^Editar$/i }));
    const edit = screen.getByTestId("section-Editar categoria");
    const fileInput = edit.querySelector('input[type="file"]') as HTMLInputElement;
    expect(fileInput).toBeTruthy();
    const file = new File([new Uint8Array([1, 2, 3])], "icone.png", {
      type: "image/png",
    });
    fireEvent.change(fileInput, { target: { files: [file] } });
    await waitFor(() => {
      expect(budgetApi.uploadAdminCapexCategoryIconImage).toHaveBeenCalledWith(
        "c1",
        file,
      );
    });
  });

  it("desativa com confirmação e reativa", async () => {
    vi.stubGlobal(
      "confirm",
      vi.fn(() => true),
    );
    render(<AdminCategoriasCapexPage />);
    fireEvent.click(await screen.findByRole("button", { name: /Ferramentas/i }));
    fireEvent.click(screen.getByRole("button", { name: /Desativar/i }));
    await waitFor(() => {
      expect(budgetApi.deactivateAdminCapexCategory).toHaveBeenCalledWith("c1");
    });

    vi.mocked(budgetApi.listAdminCapexCategories).mockResolvedValue({
      items: [{ ...row, is_active: false }],
    });
    cleanup();
    render(<AdminCategoriasCapexPage />);
    fireEvent.click(await screen.findByRole("button", { name: /Ferramentas/i }));
    fireEvent.click(screen.getByRole("button", { name: /Reativar/i }));
    await waitFor(() => {
      expect(budgetApi.reactivateAdminCapexCategory).toHaveBeenCalledWith("c1");
    });
  });
});

describe("AdminCategoriasCapexPage access", () => {
  it("nega acesso sem permissão", async () => {
    permissionsState.profile.permissions = ["planejamento-orcamentario.access"];
    render(<AdminCategoriasCapexPage />);
    await screen.findByText(/Sem permissão para gerenciar categorias CAPEX/i);
  });

  it("exibe loading e estado vazio", async () => {
    vi.mocked(budgetApi.listAdminCapexCategories).mockImplementation(
      () => new Promise(() => undefined) as never,
    );
    const { unmount } = render(<AdminCategoriasCapexPage />);
    expect(await screen.findByLabelText("Carregando categorias")).toBeTruthy();
    unmount();

    vi.mocked(budgetApi.listAdminCapexCategories).mockResolvedValue({ items: [] });
    render(<AdminCategoriasCapexPage />);
    await screen.findByText(/Nenhuma categoria encontrada/i);
  });
});
