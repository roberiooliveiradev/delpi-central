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
const discardMock = vi.fn();
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
  discardTemplateVersion: (...args: unknown[]) => discardMock(...args),
  listTemplateEvents: (...args: unknown[]) => listEventsMock(...args),
}));

import { ChecklistAdminPage } from "./ChecklistAdminPage";

const BASE = "/apps/controllership-finance";

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

  it("renders template and version table without items expansion", async () => {
    setupHappy();
    render(<ChecklistAdminPage basePath={BASE} />);
    await waitFor(() =>
      expect(
        screen.getByText("Checklist mensal (monthly-closing-checklist)"),
      ).toBeTruthy(),
    );
    expect(await screen.findByText("v1")).toBeTruthy();
    expect(screen.getByText("v2")).toBeTruthy();
    expect(screen.getByText("Publicada")).toBeTruthy();
    expect(screen.getByText("Rascunho")).toBeTruthy();
    // UX-015: a página não expande a tabela de itens — nem consulta o
    // detalhe de versão.
    expect(screen.queryByText("Itens do checklist")).toBeNull();
    expect(getVersionMock).not.toHaveBeenCalled();
  });

  it("navigates to the dedicated version page", async () => {
    setupHappy();
    render(<ChecklistAdminPage basePath={BASE} />);
    const openButtons = await screen.findAllByRole("button", {
      name: "Abrir versão",
    });
    fireEvent.click(openButtons[0]); // v1
    expect(window.location.pathname).toBe(
      `${BASE}/closing/admin/versions/1`,
    );
  });

  it("navigates to the template history page", async () => {
    setupHappy();
    render(<ChecklistAdminPage basePath={BASE} />);
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Eventos de auditoria",
      }),
    );
    expect(window.location.pathname).toBe(
      `${BASE}/closing/admin/events`,
    );
    expect(listEventsMock).not.toHaveBeenCalled();
  });

  it("disables draft creation while a draft is open", async () => {
    setupHappy();
    render(<ChecklistAdminPage basePath={BASE} />);
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
    render(<ChecklistAdminPage basePath={BASE} />);
    await waitFor(() =>
      expect(screen.getByText(/Acesso restrito/)).toBeTruthy(),
    );
  });

  it("shows empty state when no template exists", async () => {
    listTemplatesMock.mockResolvedValue([]);
    render(<ChecklistAdminPage basePath={BASE} />);
    await waitFor(() =>
      expect(
        screen.getByText("Nenhum template de checklist registrado."),
      ).toBeTruthy(),
    );
  });

  it("publishes a version with effective period", async () => {
    listTemplatesMock.mockResolvedValue([TEMPLATE]);
    listVersionsMock.mockResolvedValue([
      VERSION_PUBLISHED,
      VERSION_REVIEW,
    ]);
    publishMock.mockResolvedValue(VERSION_REVIEW);
    render(<ChecklistAdminPage basePath={BASE} />);
    const publishBtn = await screen.findByRole("button", {
      name: "Publicar",
    });
    fireEvent.click(publishBtn);
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

  it("inactivates the published version after confirmation", async () => {
    setupHappy();
    inactivateMock.mockResolvedValue(VERSION_PUBLISHED);
    render(<ChecklistAdminPage basePath={BASE} />);
    const btn = await screen.findByRole("button", { name: "Inativar" });
    fireEvent.click(btn);
    fireEvent.click(
      await screen.findByRole("button", { name: "Inativar versão" }),
    );
    await waitFor(() => expect(inactivateMock).toHaveBeenCalled());
    expect(inactivateMock.mock.calls[0]).toEqual(["t-1", 1]);
  });

  it("submits a draft version for review", async () => {
    setupHappy();
    submitReviewMock.mockResolvedValue({
      ...VERSION_DRAFT,
      status: "REVIEW",
    });
    render(<ChecklistAdminPage basePath={BASE} />);
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
    render(<ChecklistAdminPage basePath={BASE} />);
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
