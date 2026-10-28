import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
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

/** Escopo da listagem — o hero exibe a última versão (`v2`), então
 * consultas de célula precisam mirar a superfície `cf-flex-listing`. */
function listing() {
  return within(
    document.querySelector(".cf-flex-listing") as HTMLElement,
  );
}

describe("ChecklistAdminPage", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("renders hero and version table without items expansion", async () => {
    setupHappy();
    render(<ChecklistAdminPage basePath={BASE} />);
    // UX-016: hero contextual com o nome do template — nunca o
    // identificador técnico `monthly-closing-checklist`.
    await waitFor(() =>
      expect(screen.getByText("Checklist mensal")).toBeTruthy(),
    );
    expect(screen.queryByText(/monthly-closing-checklist/)).toBeNull();
    // Hero: ações administrativas reais.
    expect(
      screen.getByRole("button", { name: "Nova versão" }),
    ).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Auditoria" }),
    ).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Documentos" }),
    ).toBeTruthy();
    // Listagem única abaixo do hero.
    expect(
      screen.getByRole("heading", { name: "Versões" }),
    ).toBeTruthy();
    expect(await listing().findByText("v1")).toBeTruthy();
    expect(listing().getByText("v2")).toBeTruthy();
    expect(listing().getByText("Publicada")).toBeTruthy();
    expect(listing().getByText("Rascunho")).toBeTruthy();
    // UX-015: a página não expande a tabela de itens — nem consulta o
    // detalhe de versão.
    expect(screen.queryByText("Itens do checklist")).toBeNull();
    expect(getVersionMock).not.toHaveBeenCalled();
  });

  it("shows no actions column nor destructive controls in the listing", async () => {
    setupHappy();
    render(<ChecklistAdminPage basePath={BASE} />);
    await screen.findByText("v1");
    // UX016-03: inativação e demais ações de estado vivem só no
    // detalhe da versão — a listagem não tem coluna Ações.
    expect(screen.queryByText("Ações")).toBeNull();
    expect(
      screen.queryByRole("button", { name: "Inativar" }),
    ).toBeNull();
    expect(
      screen.queryByRole("button", { name: "Descartar" }),
    ).toBeNull();
    expect(
      screen.queryByRole("button", { name: "Abrir versão" }),
    ).toBeNull();
  });

  it("renders the listing toolbar inside the hero and filters rows", async () => {
    setupHappy();
    render(<ChecklistAdminPage basePath={BASE} />);
    await screen.findByText("v1");
    // UX016-02: pesquisa/toggle/colunas vivem no hero (portal real,
    // mesma instância) — nunca duplicadas na seção.
    const host = document.querySelector(
      "[data-testid='admin-listing-toolbar']",
    ) as HTMLElement;
    expect(host).toBeTruthy();
    const search = host.querySelector(
      "input[type='search']",
    ) as HTMLInputElement;
    expect(search).toBeTruthy();
    expect(host.querySelector("button")).toBeTruthy();
    const section = document.querySelector(
      ".cf-flex-listing section",
    ) as HTMLElement;
    expect(section?.querySelector("input[type='search']")).toBeNull();
    // T05: a busca no hero filtra as linhas reais da tabela.
    fireEvent.change(search, { target: { value: "Rascunho" } });
    await waitFor(() =>
      expect(listing().queryByText("v1")).toBeNull(),
    );
    expect(listing().getByText("v2")).toBeTruthy();
  });

  it("navigates to the dedicated version page by row click", async () => {
    setupHappy();
    render(<ChecklistAdminPage basePath={BASE} />);
    const cell = await screen.findByText("v1");
    fireEvent.click(cell.closest("tr") as HTMLElement);
    expect(window.location.pathname).toBe(
      `${BASE}/closing/admin/versions/1`,
    );
    // Sem botão redundante "Abrir versão" — a linha é a superfície.
    expect(
      screen.queryByRole("button", { name: "Abrir versão" }),
    ).toBeNull();
  });

  it("keeps destructive controls out of the listing (detail only)", async () => {
    setupHappy();
    render(<ChecklistAdminPage basePath={BASE} />);
    await screen.findByText("v1");
    // UX016-03/UX016-04: nenhum controle destrutivo na página da lista —
    // clicar na linha só navega para o detalhe.
    const cell = screen.getByText("v1");
    fireEvent.click(cell.closest("tr") as HTMLElement);
    expect(window.location.pathname).toBe(
      `${BASE}/closing/admin/versions/1`,
    );
  });

  it("sorts versions by column", async () => {
    listTemplatesMock.mockResolvedValue([TEMPLATE]);
    listVersionsMock.mockResolvedValue([
      VERSION_DRAFT,
      VERSION_PUBLISHED,
    ]);
    render(<ChecklistAdminPage basePath={BASE} />);
    await screen.findByText("v1");
    const sortable = screen.getByRole("button", {
      name: "Ordenar por Versão",
    });
    fireEvent.click(sortable);
    let labels = listing()
      .getAllByText(/^v\d$/)
      .map((n) => n.textContent);
    expect(labels).toEqual(["v1", "v2"]);
    fireEvent.click(sortable);
    labels = listing()
      .getAllByText(/^v\d$/)
      .map((n) => n.textContent);
    expect(labels).toEqual(["v2", "v1"]);
  });

  it("switches to card view and keeps row navigation", async () => {
    setupHappy();
    render(<ChecklistAdminPage basePath={BASE} />);
    await screen.findByText("v1");
    fireEvent.click(screen.getByRole("button", { name: "Cards" }));
    const card = await screen.findByRole("link", {
      name: "Abrir versão 1",
    });
    expect(card).toBeTruthy();
    fireEvent.click(card);
    expect(window.location.pathname).toBe(
      `${BASE}/closing/admin/versions/1`,
    );
  });

  it("navigates to the template history page", async () => {
    setupHappy();
    render(<ChecklistAdminPage basePath={BASE} />);
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Auditoria",
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
    await screen.findByText("v1");
    expect(listing().getByText("v2")).toBeTruthy();
    const button = await screen.findByRole("button", {
      name: "Nova versão",
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

  // As ações de ciclo de vida (publicar, revisar, devolver, inativar,
  // descartar) vivem exclusivamente no detalhe da versão — a cobertura
  // correspondente está em ChecklistVersionPage.test.tsx.
});
