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
const listVersionsMock = vi.fn();
const getVersionMock = vi.fn();
const createDraftMock = vi.fn();
const updateDraftMock = vi.fn();
const publishMock = vi.fn();
const submitReviewMock = vi.fn();
const returnDraftMock = vi.fn();
const inactivateMock = vi.fn();
const listEventsMock = vi.fn();

vi.mock("../../api/adminApi", () => ({
  listChecklistTemplates: (...args: unknown[]) =>
    listTemplatesMock(...args),
  listTemplateVersions: (...args: unknown[]) =>
    listVersionsMock(...args),
  getTemplateVersion: (...args: unknown[]) => getVersionMock(...args),
  createTemplateDraft: (...args: unknown[]) => createDraftMock(...args),
  updateTemplateDraft: (...args: unknown[]) => updateDraftMock(...args),
  publishTemplateVersion: (...args: unknown[]) => publishMock(...args),
  submitVersionForReview: (...args: unknown[]) =>
    submitReviewMock(...args),
  returnVersionToDraft: (...args: unknown[]) =>
    returnDraftMock(...args),
  inactivateTemplateVersion: (...args: unknown[]) =>
    inactivateMock(...args),
  listTemplateEvents: (...args: unknown[]) => listEventsMock(...args),
}));

import { ChecklistAdminPage } from "./ChecklistAdminPage";

const TEMPLATE = {
  template_id: "t-1",
  code: "monthly-closing-checklist",
  name: "Checklist mensal",
};

const VERSION_PUBLISHED = {
  version_id: "v-1",
  version: 1,
  status: "PUBLISHED",
  item_count: 2,
  effective_from_period: "2026-05",
  published_at: "2026-04-15T10:00:00Z",
  revision: 3,
};

const VERSION_DRAFT = {
  version_id: "v-2",
  version: 2,
  status: "DRAFT",
  item_count: 2,
  effective_from_period: null,
  published_at: null,
  revision: 1,
};

const VERSION_REVIEW = {
  ...VERSION_DRAFT,
  version_id: "v-3",
  version: 3,
  status: "REVIEW",
};

const DRAFT_DETAIL = {
  ...VERSION_DRAFT,
  items: [
    {
      item_id: "i-1",
      item_key: "1.1",
      sort_order: 1,
      sheet: "ELETRONICO",
      name: "Balancete",
      purpose: null,
      origin_kind: "TOTVS",
      recipient_area: "CONTABIL",
      applicability: "REQUIRED",
      branch_scope: "BOTH",
      totvs_report_ref: "MATR460",
      requirement_notes: null,
      validation_scope: "PER_ATTACHMENT",
    },
  ],
};

function setupHappy() {
  listTemplatesMock.mockResolvedValue([TEMPLATE]);
  listVersionsMock.mockResolvedValue([
    VERSION_PUBLISHED,
    VERSION_DRAFT,
  ]);
}

describe("ChecklistAdminPage", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("renders template and version table", async () => {
    setupHappy();
    render(<ChecklistAdminPage />);
    await waitFor(() =>
      expect(
        screen.getByText("Checklist mensal (monthly-closing-checklist)"),
      ).toBeTruthy(),
    );
    expect(await screen.findByText("v1")).toBeTruthy();
    expect(screen.getByText("v2")).toBeTruthy();
    expect(screen.getByText("Publicada")).toBeTruthy();
    expect(screen.getByText("Rascunho")).toBeTruthy();
  });

  it("disables draft creation while a draft is open", async () => {
    setupHappy();
    render(<ChecklistAdminPage />);
    await screen.findByText("v2");
    const button = await screen.findByRole("button", {
      name: "Criar versão rascunho",
    });
    expect(button).toHaveProperty("disabled", true);
  });

  it("shows authorization error for 403", async () => {
    listTemplatesMock.mockRejectedValue(
      new ApiError(403, "Forbidden", "forbidden"),
    );
    render(<ChecklistAdminPage />);
    await waitFor(() =>
      expect(screen.getByText(/Acesso restrito/)).toBeTruthy(),
    );
  });

  it("shows empty state when no template exists", async () => {
    listTemplatesMock.mockResolvedValue([]);
    render(<ChecklistAdminPage />);
    await waitFor(() =>
      expect(
        screen.getByText("Nenhum template de checklist registrado."),
      ).toBeTruthy(),
    );
  });

  it("opens draft items in editable mode and saves with revision", async () => {
    setupHappy();
    getVersionMock.mockResolvedValue(DRAFT_DETAIL);
    updateDraftMock.mockResolvedValue({
      ...DRAFT_DETAIL,
      revision: 2,
    });
    render(<ChecklistAdminPage />);
    const itemButtons = await screen.findAllByRole("button", {
      name: "Itens",
    });
    fireEvent.click(itemButtons[1]); // v2 DRAFT
    await waitFor(() => expect(getVersionMock).toHaveBeenCalled());
    const save = await screen.findByRole("button", {
      name: "Salvar rascunho",
    });
    fireEvent.click(save);
    await waitFor(() => expect(updateDraftMock).toHaveBeenCalled());
    const [templateId, version, body] = updateDraftMock.mock.calls[0];
    expect(templateId).toBe("t-1");
    expect(version).toBe(2);
    expect(body.revision).toBe(1);
    expect(body.items).toHaveLength(1);
    expect(body.items[0].item_key).toBe("1.1");
  });

  it("maps stale_revision conflict to a reload message", async () => {
    setupHappy();
    getVersionMock.mockResolvedValue(DRAFT_DETAIL);
    updateDraftMock.mockRejectedValue(
      new ApiError(409, "Stale", "stale_revision"),
    );
    render(<ChecklistAdminPage />);
    const itemButtons = await screen.findAllByRole("button", {
      name: "Itens",
    });
    fireEvent.click(itemButtons[1]);
    const save = await screen.findByRole("button", {
      name: "Salvar rascunho",
    });
    fireEvent.click(save);
    await waitFor(() =>
      expect(screen.getByText(/revisão desatualizada|recarregue/i))
        .toBeTruthy(),
    );
  });

  it("publishes a version with effective period", async () => {
    listTemplatesMock.mockResolvedValue([TEMPLATE]);
    listVersionsMock.mockResolvedValue([
      VERSION_PUBLISHED,
      VERSION_REVIEW,
    ]);
    publishMock.mockResolvedValue(VERSION_REVIEW);
    render(<ChecklistAdminPage />);
    const publishBtn = await screen.findByRole("button", {
      name: "Publicar",
    });
    fireEvent.click(publishBtn);
    const input = await screen.findByPlaceholderText("2026-06");
    fireEvent.change(input, { target: { value: "2026-07" } });
    fireEvent.click(
      screen.getByRole("button", { name: "Publicar versão" }),
    );
    await waitFor(() => expect(publishMock).toHaveBeenCalled());
    expect(publishMock.mock.calls[0][2]).toEqual({
      effective_from_period: "2026-07",
    });
  });

  it("inactivates the published version after confirmation", async () => {
    setupHappy();
    inactivateMock.mockResolvedValue(VERSION_PUBLISHED);
    render(<ChecklistAdminPage />);
    const btn = await screen.findByRole("button", { name: "Inativar" });
    fireEvent.click(btn);
    fireEvent.click(
      await screen.findByRole("button", { name: "Inativar versão" }),
    );
    await waitFor(() => expect(inactivateMock).toHaveBeenCalled());
    expect(inactivateMock.mock.calls[0]).toEqual(["t-1", 1]);
  });

  it("lists template audit events", async () => {
    setupHappy();
    listEventsMock.mockResolvedValue([
      {
        event_id: "e-1",
        event_type: "VERSION_PUBLISHED",
        actor_subject: "u-1",
        detail: {},
        created_at: "2026-04-15T10:00:00Z",
        version: 1,
      },
    ]);
    render(<ChecklistAdminPage />);
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Eventos de auditoria",
      }),
    );
    await waitFor(() =>
      expect(screen.getByText(/Versão publicada/)).toBeTruthy(),
    );
    expect(listEventsMock).toHaveBeenCalledWith("t-1");
  });

  it("submits a draft version for review", async () => {
    setupHappy();
    submitReviewMock.mockResolvedValue({
      ...VERSION_DRAFT,
      status: "REVIEW",
    });
    render(<ChecklistAdminPage />);
    const btn = await screen.findByRole("button", {
      name: "Enviar para revisão",
    });
    fireEvent.click(btn);
    await waitFor(() => expect(submitReviewMock).toHaveBeenCalled());
    expect(submitReviewMock.mock.calls[0]).toEqual(["t-1", 2]);
  });

  it("returns a review version to draft with a reason", async () => {
    listTemplatesMock.mockResolvedValue([TEMPLATE]);
    listVersionsMock.mockResolvedValue([
      VERSION_PUBLISHED,
      VERSION_REVIEW,
    ]);
    returnDraftMock.mockResolvedValue(VERSION_DRAFT);
    render(<ChecklistAdminPage />);
    const btn = await screen.findByRole("button", { name: "Devolver" });
    fireEvent.click(btn);
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
});
