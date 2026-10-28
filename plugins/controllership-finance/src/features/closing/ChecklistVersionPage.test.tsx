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
const updateDraftMock = vi.fn();
const publishMock = vi.fn();
const submitReviewMock = vi.fn();
const returnDraftMock = vi.fn();
const inactivateMock = vi.fn();
const discardMock = vi.fn();
const listEventsMock = vi.fn();

vi.mock("../../api/adminApi", () => ({
  listChecklistTemplates: (...args: unknown[]) =>
    listTemplatesMock(...args),
  getTemplateVersion: (...args: unknown[]) => getVersionMock(...args),
  updateTemplateDraft: (...args: unknown[]) => updateDraftMock(...args),
  publishTemplateVersion: (...args: unknown[]) => publishMock(...args),
  submitVersionForReview: (...args: unknown[]) =>
    submitReviewMock(...args),
  returnVersionToDraft: (...args: unknown[]) =>
    returnDraftMock(...args),
  inactivateTemplateVersion: (...args: unknown[]) =>
    inactivateMock(...args),
  discardTemplateVersion: (...args: unknown[]) => discardMock(...args),
  listTemplateEvents: (...args: unknown[]) => listEventsMock(...args),
}));

import { ChecklistVersionPage } from "./ChecklistVersionPage";

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

const DRAFT_DETAIL = {
  version_id: "v-2",
  version: 2,
  status: "DRAFT",
  item_count: 1,
  effective_from_period: null,
  published_at: null,
  published_by: null,
  created_at: "2026-04-01T10:00:00Z",
  revision: 1,
  items: [ITEM_A],
};

const PUBLISHED_DETAIL = {
  ...DRAFT_DETAIL,
  version_id: "v-1",
  version: 1,
  status: "PUBLISHED",
  effective_from_period: "2026-05",
  published_at: "2026-04-15T10:00:00Z",
};

function setupHappy() {
  listTemplatesMock.mockResolvedValue([TEMPLATE]);
}

describe("ChecklistVersionPage", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("renders version metadata and its documents", async () => {
    setupHappy();
    getVersionMock.mockResolvedValue(DRAFT_DETAIL);
    render(<ChecklistVersionPage basePath={BASE} version={2} />);
    expect(await screen.findByText("CK-E-01")).toBeTruthy();
    expect(getVersionMock).toHaveBeenCalledWith(
      "t-1",
      2,
      expect.anything(),
    );
    expect(
      screen.getAllByText("Versão v2").length,
    ).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Balancete")).toBeTruthy();
    expect(screen.getByText("Rascunho")).toBeTruthy();
    expect(screen.getByText("Vigente desde")).toBeTruthy();
    expect(screen.getByText("Documentos da versão")).toBeTruthy();
  });

  it("navigates to the document-in-version page", async () => {
    setupHappy();
    getVersionMock.mockResolvedValue(DRAFT_DETAIL);
    render(<ChecklistVersionPage basePath={BASE} version={2} />);
    const open = await screen.findByRole("button", { name: "Abrir" });
    fireEvent.click(open);
    expect(window.location.pathname).toBe(
      `${BASE}/closing/admin/versions/2/documents/CK-E-01`,
    );
  });

  it("navigates to the version history page", async () => {
    setupHappy();
    getVersionMock.mockResolvedValue(DRAFT_DETAIL);
    render(<ChecklistVersionPage basePath={BASE} version={2} />);
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Histórico da versão",
      }),
    );
    expect(window.location.pathname).toBe(
      `${BASE}/closing/admin/versions/2/events`,
    );
  });

  it("keeps published versions read-only", async () => {
    setupHappy();
    getVersionMock.mockResolvedValue(PUBLISHED_DETAIL);
    render(<ChecklistVersionPage basePath={BASE} version={1} />);
    await screen.findByText("CK-E-01");
    expect(screen.queryByText("Editar itens")).toBeNull();
    expect(screen.queryByText("Salvar rascunho")).toBeNull();
    expect(screen.queryByText("Adicionar item")).toBeNull();
    expect(
      screen.getByRole("button", { name: "Inativar" }),
    ).toBeTruthy();
  });

  it("edits draft items and saves atomically with revision", async () => {
    setupHappy();
    getVersionMock.mockResolvedValue(DRAFT_DETAIL);
    updateDraftMock.mockResolvedValue({
      ...DRAFT_DETAIL,
      revision: 2,
    });
    render(<ChecklistVersionPage basePath={BASE} version={2} />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Editar itens" }),
    );
    fireEvent.click(
      await screen.findByRole("button", { name: "Salvar rascunho" }),
    );
    await waitFor(() => expect(updateDraftMock).toHaveBeenCalled());
    const [templateId, version, body] = updateDraftMock.mock.calls[0];
    expect(templateId).toBe("t-1");
    expect(version).toBe(2);
    expect(body.revision).toBe(1);
    expect(body.items).toHaveLength(1);
    expect(body.items[0].item_key).toBe("CK-E-01");
  });

  it("maps stale_revision conflict to a reload message", async () => {
    setupHappy();
    getVersionMock.mockResolvedValue(DRAFT_DETAIL);
    updateDraftMock.mockRejectedValue(
      new ApiError(409, "Stale", "stale_revision"),
    );
    render(<ChecklistVersionPage basePath={BASE} version={2} />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Editar itens" }),
    );
    fireEvent.click(
      await screen.findByRole("button", { name: "Salvar rascunho" }),
    );
    await waitFor(() =>
      expect(
        screen.getByText(/revisão desatualizada|recarregue/i),
      ).toBeTruthy(),
    );
  });

  it("offers review submission on draft versions", async () => {
    setupHappy();
    getVersionMock.mockResolvedValue(DRAFT_DETAIL);
    submitReviewMock.mockResolvedValue({
      ...DRAFT_DETAIL,
      status: "REVIEW",
    });
    render(<ChecklistVersionPage basePath={BASE} version={2} />);
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Enviar para revisão",
      }),
    );
    await waitFor(() => expect(submitReviewMock).toHaveBeenCalled());
    expect(submitReviewMock.mock.calls[0]).toEqual(["t-1", 2]);
  });

  it("returns to the admin list after discarding the draft", async () => {
    setupHappy();
    getVersionMock.mockResolvedValue(DRAFT_DETAIL);
    discardMock.mockResolvedValue({
      version_id: "v-2",
      version: 2,
      status: "DISCARDED",
    });
    render(<ChecklistVersionPage basePath={BASE} version={2} />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Descartar" }),
    );
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Descartar rascunho",
      }),
    );
    await waitFor(() => expect(discardMock).toHaveBeenCalled());
    expect(discardMock.mock.calls[0]).toEqual(["t-1", 2, 1]);
    await waitFor(() =>
      expect(window.location.pathname).toBe(`${BASE}/closing/admin`),
    );
  });

  it("shows error state when the version does not exist", async () => {
    setupHappy();
    getVersionMock.mockRejectedValue(
      new ApiError(404, "Not Found", "version_not_found"),
    );
    render(<ChecklistVersionPage basePath={BASE} version={9} />);
    await waitFor(() =>
      expect(
        screen.getByText(/não encontrada/i),
      ).toBeTruthy(),
    );
  });

  it("shows authorization error for 403", async () => {
    listTemplatesMock.mockRejectedValue(
      new ApiError(403, "Forbidden", "forbidden"),
    );
    render(<ChecklistVersionPage basePath={BASE} version={1} />);
    await waitFor(() =>
      expect(screen.getByText(/Acesso restrito/)).toBeTruthy(),
    );
  });

  it("renders an empty item list for an empty published version", async () => {
    setupHappy();
    getVersionMock.mockResolvedValue({
      ...PUBLISHED_DETAIL,
      item_count: 0,
      items: [],
    });
    render(<ChecklistVersionPage basePath={BASE} version={1} />);
    await waitFor(() =>
      expect(
        screen.getByText("Nenhum item nesta versão."),
      ).toBeTruthy(),
    );
  });
});
