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

const REVIEW_DETAIL = {
  ...DRAFT_DETAIL,
  version_id: "v-3",
  version: 3,
  status: "REVIEW",
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

  it("navigates to the document-in-version page by row click", async () => {
    setupHappy();
    getVersionMock.mockResolvedValue(DRAFT_DETAIL);
    render(<ChecklistVersionPage basePath={BASE} version={2} />);
    const cell = await screen.findByText("CK-E-01");
    fireEvent.click(cell.closest("tr") as HTMLElement);
    expect(window.location.pathname).toBe(
      `${BASE}/closing/admin/versions/2/documents/CK-E-01`,
    );
    // Sem botão redundante "Abrir" — a linha inteira é a superfície.
    expect(screen.queryByRole("button", { name: "Abrir" })).toBeNull();
  });

  it("shows an honest identity fallback instead of the raw subject", async () => {
    setupHappy();
    getVersionMock.mockResolvedValue({
      ...PUBLISHED_DETAIL,
      published_by: "dc99fc6d-0000-4000-8000-0000000000ab",
    });
    render(<ChecklistVersionPage basePath={BASE} version={1} />);
    await screen.findByText("CK-E-01");
    // UX-014/RW02: sem contrato de identidade o subject técnico nunca
    // é apresentado como nome — permanece apenas na trilha (title).
    expect(
      screen.queryByText(/dc99fc6d-0000-4000-8000-0000000000ab/),
    ).toBeNull();
    expect(screen.getByText("Identidade não disponível")).toBeTruthy();
  });

  it("switches the documents list to card view and keeps navigation", async () => {
    setupHappy();
    getVersionMock.mockResolvedValue(DRAFT_DETAIL);
    render(<ChecklistVersionPage basePath={BASE} version={2} />);
    await screen.findByText("CK-E-01");
    fireEvent.click(screen.getByRole("button", { name: "Cards" }));
    const card = await screen.findByRole("link", {
      name: "Abrir documento Balancete",
    });
    fireEvent.click(card);
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

  it("inactivates the published version after confirmation, without navigating", async () => {
    setupHappy();
    getVersionMock.mockResolvedValue(PUBLISHED_DETAIL);
    inactivateMock.mockResolvedValue(PUBLISHED_DETAIL);
    render(<ChecklistVersionPage basePath={BASE} version={1} />);
    await screen.findByText("CK-E-01");
    const before = window.location.pathname;
    // T03/T04: Inativar no hero do detalhe, com confirmação própria.
    fireEvent.click(screen.getByRole("button", { name: "Inativar" }));
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Inativar versão",
      }),
    );
    await waitFor(() => expect(inactivateMock).toHaveBeenCalled());
    expect(inactivateMock.mock.calls[0]).toEqual(["t-1", 1]);
    expect(window.location.pathname).toBe(before);
  });

  it("publishes a review version with effective period", async () => {
    setupHappy();
    getVersionMock.mockResolvedValue(REVIEW_DETAIL);
    publishMock.mockResolvedValue({
      ...REVIEW_DETAIL,
      status: "PUBLISHED",
    });
    render(<ChecklistVersionPage basePath={BASE} version={3} />);
    await screen.findByText("CK-E-01");
    fireEvent.click(screen.getByRole("button", { name: "Publicar" }));
    const input = await screen.findByLabelText(
      "Vigente a partir de (AAAA-MM)",
    );
    fireEvent.change(input, { target: { value: "2026-07" } });
    fireEvent.click(
      screen.getByRole("button", { name: "Publicar versão" }),
    );
    await waitFor(() => expect(publishMock).toHaveBeenCalled());
    expect(publishMock.mock.calls[0][2]).toEqual({
      effective_from_period: "2026-07",
    });
  });

  it("returns a review version to draft with a reason", async () => {
    setupHappy();
    getVersionMock.mockResolvedValue(REVIEW_DETAIL);
    returnDraftMock.mockResolvedValue(DRAFT_DETAIL);
    render(<ChecklistVersionPage basePath={BASE} version={3} />);
    await screen.findByText("CK-E-01");
    fireEvent.click(screen.getByRole("button", { name: "Devolver" }));
    const reason = await screen.findByRole("textbox");
    fireEvent.change(reason, {
      target: { value: "Ajustar item 2.3" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Devolver a rascunho" }),
    );
    await waitFor(() => expect(returnDraftMock).toHaveBeenCalled());
    expect(returnDraftMock.mock.calls[0]).toEqual([
      "t-1",
      3,
      { reason: "Ajustar item 2.3" },
    ]);
  });

  it("renders the documents toolbar inside the hero and filters rows", async () => {
    setupHappy();
    getVersionMock.mockResolvedValue(DRAFT_DETAIL);
    render(<ChecklistVersionPage basePath={BASE} version={2} />);
    await screen.findByText("CK-E-01");
    const host = document.querySelector(
      "[data-testid='version-listing-toolbar']",
    ) as HTMLElement;
    expect(host).toBeTruthy();
    const search = host.querySelector(
      "input[type='search']",
    ) as HTMLInputElement;
    expect(search).toBeTruthy();
    const section = document.querySelector(
      ".cf-flex-listing section",
    ) as HTMLElement;
    expect(section?.querySelector("input[type='search']")).toBeNull();
    fireEvent.change(search, { target: { value: "ZZZ" } });
    await waitFor(() =>
      expect(screen.queryByText("CK-E-01")).toBeNull(),
    );
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
