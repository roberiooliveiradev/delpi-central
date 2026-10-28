import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../../api/httpClient";

vi.mock(
  "@delpi/plugin-ui/index",
  async () => await import("../../test/pluginUiMock"),
);

const listTemplatesMock = vi.fn();
const getVersionMock = vi.fn();

vi.mock("../../api/adminApi", () => ({
  listChecklistTemplates: (...args: unknown[]) =>
    listTemplatesMock(...args),
  getTemplateVersion: (...args: unknown[]) => getVersionMock(...args),
}));

import { ChecklistVersionDocumentPage } from "./ChecklistVersionDocumentPage";

const BASE = "/apps/controllership-finance";

const TEMPLATE = {
  template_id: "t-1",
  code: "monthly-closing-checklist",
  name: "Checklist mensal",
};

const ITEM_A = {
  item_id: "i-1",
  item_key: "CK-E-01",
  sort_order: 1,
  sheet: "ELETRONICO",
  name: "Balancete",
  purpose: "Fechamento contábil",
  origin_kind: "TOTVS",
  recipient_area: "CONTABIL",
  applicability: "REQUIRED",
  branch_scope: "BOTH",
  totvs_report_ref: "MATR460",
  requirement_notes: "Gerar PDF",
  validation_scope: "PER_ATTACHMENT",
};

const PUBLISHED_DETAIL = {
  version_id: "v-1",
  version: 1,
  status: "PUBLISHED",
  item_count: 1,
  effective_from_period: "2026-05",
  published_at: "2026-04-15T10:00:00Z",
  published_by: null,
  created_at: "2026-04-01T10:00:00Z",
  revision: 3,
  items: [ITEM_A],
};

const DRAFT_DETAIL = {
  ...PUBLISHED_DETAIL,
  version_id: "v-2",
  version: 2,
  status: "DRAFT",
  effective_from_period: null,
  published_at: null,
  revision: 1,
};

describe("ChecklistVersionDocumentPage", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("renders the historical document fields read-only", async () => {
    listTemplatesMock.mockResolvedValue([TEMPLATE]);
    getVersionMock.mockResolvedValue(PUBLISHED_DETAIL);
    render(
      <ChecklistVersionDocumentPage
        basePath={BASE}
        version={1}
        itemKey="CK-E-01"
      />,
    );
    await waitFor(() =>
      expect(
        screen.getAllByText("Balancete").length,
      ).toBeGreaterThanOrEqual(1),
    );
    expect(screen.getByText("Fechamento contábil")).toBeTruthy();
    expect(screen.getByText("Gerar PDF")).toBeTruthy();
    expect(screen.getByText("ERP TOTVS")).toBeTruthy();
    expect(screen.getByText("Contábil")).toBeTruthy();
    expect(
      screen.getAllByText("Obrigatório").length,
    ).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Matriz e filiais")).toBeTruthy();
    expect(screen.getByText("Por anexo")).toBeTruthy();
    expect(screen.getByText("MATR460")).toBeTruthy();
    expect(
      screen.getAllByText("Versão v1").length,
    ).toBeGreaterThanOrEqual(1);
    expect(
      screen.getAllByText("Publicada").length,
    ).toBeGreaterThanOrEqual(1);
    // Read-only: nenhum controle de formulário editável.
    expect(screen.queryByRole("textbox")).toBeNull();
    expect(screen.queryByText("Salvar rascunho")).toBeNull();
  });

  it("hands off to the governed catalog flow for prospective edit", async () => {
    listTemplatesMock.mockResolvedValue([TEMPLATE]);
    getVersionMock.mockResolvedValue(PUBLISHED_DETAIL);
    render(
      <ChecklistVersionDocumentPage
        basePath={BASE}
        version={1}
        itemKey="CK-E-01"
      />,
    );
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Editar exigência futura",
      }),
    );
    expect(window.location.pathname).toBe(
      `${BASE}/closing/admin/documents/CK-E-01`,
    );
  });

  it("offers in-draft editing navigation on draft versions", async () => {
    listTemplatesMock.mockResolvedValue([TEMPLATE]);
    getVersionMock.mockResolvedValue(DRAFT_DETAIL);
    render(
      <ChecklistVersionDocumentPage
        basePath={BASE}
        version={2}
        itemKey="CK-E-01"
      />,
    );
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Editar item no rascunho",
      }),
    );
    expect(window.location.pathname).toBe(
      `${BASE}/closing/admin/versions/2`,
    );
  });

  it("shows an honest empty state when the item is not in the version", async () => {
    listTemplatesMock.mockResolvedValue([TEMPLATE]);
    getVersionMock.mockResolvedValue(PUBLISHED_DETAIL);
    render(
      <ChecklistVersionDocumentPage
        basePath={BASE}
        version={1}
        itemKey="CK-Z-99"
      />,
    );
    await waitFor(() =>
      expect(
        screen.getByText(/não pertence à versão v1/),
      ).toBeTruthy(),
    );
    // Não oferece edição de um item inexistente.
    expect(
      screen.queryByRole("button", { name: "Editar exigência futura" }),
    ).toBeNull();
  });

  it("shows error state when the version does not exist", async () => {
    listTemplatesMock.mockResolvedValue([TEMPLATE]);
    getVersionMock.mockRejectedValue(
      new ApiError(404, "Not Found", "version_not_found"),
    );
    render(
      <ChecklistVersionDocumentPage
        basePath={BASE}
        version={9}
        itemKey="CK-E-01"
      />,
    );
    await waitFor(() =>
      expect(screen.getByText(/não encontrada/i)).toBeTruthy(),
    );
  });

  it("shows authorization error for 403", async () => {
    listTemplatesMock.mockRejectedValue(
      new ApiError(403, "Forbidden", "forbidden"),
    );
    render(
      <ChecklistVersionDocumentPage
        basePath={BASE}
        version={1}
        itemKey="CK-E-01"
      />,
    );
    await waitFor(() =>
      expect(screen.getByText(/Acesso restrito/)).toBeTruthy(),
    );
  });
});
