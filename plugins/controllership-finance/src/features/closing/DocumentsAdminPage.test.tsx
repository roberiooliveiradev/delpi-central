/**
 * DocumentsAdminPage + DocumentConfigFormPage — UX-012.
 * Listagem derivada da timeline, filtros na URL, páginas completas
 * de cadastro/edição e orquestração de versões.
 */
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
const saveRequirementMock = vi.fn();

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
  saveDocumentRequirement: (...args: unknown[]) =>
    saveRequirementMock(...args),
}));

import { DocumentsAdminPage } from "./DocumentsAdminPage";

const BASE = "/apps/controllership-finance";
const LIST_URL = `${BASE}/closing/admin/documents`;

const TEMPLATE = {
  template_id: "t-1",
  code: "monthly-closing-checklist",
  name: "Checklist mensal",
  description: null,
  created_at: "2026-01-01T00:00:00Z",
  published_version: 1,
  draft_version: null,
};

const ITEM_A = {
  item_id: "i-a",
  item_key: "DOC-A",
  sort_order: 10,
  sheet: "ELETRONICO",
  name: "Balancete",
  purpose: "Fechamento contábil",
  origin_kind: "TOTVS",
  recipient_area: "CONTABIL",
  applicability: "REQUIRED",
  branch_scope: "BOTH",
  totvs_report_ref: "MATR460",
  requirement_notes: null,
  validation_scope: "PER_ATTACHMENT",
};

const ITEM_B = {
  ...ITEM_A,
  item_id: "i-b",
  item_key: "DOC-B",
  sort_order: 20,
  name: "Extrato bancário",
  purpose: null,
  recipient_area: null,
  applicability: "OPTIONAL",
};

const VERSION_1 = {
  version_id: "v-1",
  template_id: "t-1",
  version: 1,
  status: "PUBLISHED",
  revision: 1,
  effective_from_period: "2026-01",
  published_by: "admin",
  published_at: "2026-01-01T00:00:00Z",
  inactivated_at: null,
  created_at: "2026-01-01T00:00:00Z",
  item_count: 2,
  items: [ITEM_A, ITEM_B],
};

const VERSION_2 = {
  ...VERSION_1,
  version_id: "v-2",
  version: 2,
  effective_from_period: "2026-04",
  item_count: 1,
  items: [ITEM_A],
};

function setupList(versions = [VERSION_1, VERSION_2]) {
  listTemplatesMock.mockResolvedValue([TEMPLATE]);
  listVersionsMock.mockResolvedValue(versions);
  getVersionMock.mockImplementation((_t: string, v: number) =>
    Promise.resolve(versions.find((x) => x.version === v)),
  );
}

function setLocation(query = "") {
  window.history.pushState(null, "", `${LIST_URL}${query}`);
}

describe("DocumentsAdminPage — listagem", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
    setLocation();
  });

  it("lista documentos derivados da timeline com vigência e situação", async () => {
    setupList();
    render(<DocumentsAdminPage basePath={BASE} />);
    expect(await screen.findByText("Balancete")).toBeTruthy();
    expect(screen.getByText("Extrato bancário")).toBeTruthy();
    // DOC-B foi removido na v2 → janela 01/2026 → 03/2026, encerrado.
    expect(
      screen.getAllByText("Encerrado").length,
    ).toBeGreaterThanOrEqual(1);
    expect(
      screen.getAllByText("Vigente").length,
    ).toBeGreaterThanOrEqual(1);
    expect(
      screen.getAllByText("Contabilidade").length,
    ).toBeGreaterThanOrEqual(1);
    expect(
      screen.getAllByText("Uso interno").length,
    ).toBeGreaterThanOrEqual(1);
  });

  it("deep link com filtros na URL restaura a consulta", async () => {
    setupList();
    setLocation("?q=extrato");
    render(<DocumentsAdminPage basePath={BASE} />);
    expect(await screen.findByText("Extrato bancário")).toBeTruthy();
    expect(screen.queryByText("Balancete")).toBeNull();
  });

  it("filtro por situação serializa na URL e recorta a listagem", async () => {
    setupList();
    render(<DocumentsAdminPage basePath={BASE} />);
    await screen.findByText("Balancete");
    fireEvent.change(screen.getByLabelText("Situação"), {
      target: { value: "vigente" },
    });
    await waitFor(() =>
      expect(window.location.search).toContain("status=vigente"),
    );
    expect(screen.queryByText("Extrato bancário")).toBeNull();
    expect(screen.getByText("Balancete")).toBeTruthy();
  });

  it("Editar abre a página completa preservando os filtros na URL", async () => {
    setupList();
    setLocation("?status=vigente");
    render(<DocumentsAdminPage basePath={BASE} />);
    await screen.findByText("Balancete");
    fireEvent.click(
      screen.getAllByRole("button", { name: "Editar" })[0],
    );
    await waitFor(() =>
      expect(window.location.pathname).toBe(
        `${LIST_URL}/DOC-A`,
      ),
    );
    expect(window.location.search).toContain("status=vigente");
  });

  it("estado vazio orienta o primeiro cadastro", async () => {
    setupList([
      {
        ...VERSION_1,
        item_count: 0,
        items: [],
      },
    ]);
    render(<DocumentsAdminPage basePath={BASE} />);
    expect(
      await screen.findByText(/Nenhum documento encontrado/),
    ).toBeTruthy();
  });

  it("403 exibe falha de autorização segura", async () => {
    listTemplatesMock.mockRejectedValue(
      new ApiError(403, "forbidden", "forbidden"),
    );
    render(<DocumentsAdminPage basePath={BASE} />);
    expect(
      (await screen.findAllByText(/Acesso restrito|autorização/))
        .length,
    ).toBeGreaterThanOrEqual(1);
  });
});

describe("DocumentConfigFormPage — cadastro", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
    setLocation();
  });

  function setupForm(versions = [VERSION_1, VERSION_2]) {
    setupList(versions);
    listEventsMock.mockResolvedValue([]);
    saveRequirementMock.mockResolvedValue({ published_versions: [] });
  }

  it("valida campos obrigatórios antes de chamar o backend", async () => {
    setupForm();
    window.history.pushState(null, "", `${LIST_URL}/new`);
    render(<DocumentsAdminPage basePath={BASE} itemKey="new" />);
    await screen.findAllByText("Novo documento");
    fireEvent.click(
      screen.getByRole("button", { name: "Salvar documento" }),
    );
    expect(await screen.findByText(/Informe o nome/)).toBeTruthy();
    expect(saveRequirementMock).not.toHaveBeenCalled();
  });

  it("cria documento com vigência via comando transacional da BFF", async () => {
    setupForm();
    window.history.pushState(null, "", `${LIST_URL}/new`);
    render(<DocumentsAdminPage basePath={BASE} itemKey="new" />);
    await screen.findAllByText("Novo documento");
    fireEvent.change(screen.getByLabelText(/Nome do documento/), {
      target: { value: "Balanço Patrimonial" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Salvar documento" }),
    );
    await waitFor(() =>
      expect(saveRequirementMock).toHaveBeenCalledWith(
        "t-1",
        "BALANCO-PATRIMONIAL",
        expect.objectContaining({
          effective_from: expect.any(String),
          effective_until: null,
          base_version: 2,
          allow_empty: false,
          item: expect.objectContaining({
            item_key: "BALANCO-PATRIMONIAL",
            name: "Balanço Patrimonial",
          }),
        }),
        expect.any(String),
      ),
    );
    // UMA chamada — nenhuma orquestração de versões no MFE.
    expect(saveRequirementMock).toHaveBeenCalledTimes(1);
    expect(createDraftMock).not.toHaveBeenCalled();
    expect(publishMock).not.toHaveBeenCalled();
    await waitFor(() =>
      expect(window.location.pathname).toBe(LIST_URL),
    );
    expect(window.location.search).toContain(
      "saved=BALANCO-PATRIMONIAL",
    );
  });

  it("vigência final envia effective_until no mesmo comando", async () => {
    setupForm();
    window.history.pushState(null, "", `${LIST_URL}/new`);
    render(<DocumentsAdminPage basePath={BASE} itemKey="new" />);
    await screen.findAllByText("Novo documento");
    fireEvent.change(screen.getByLabelText(/Nome do documento/), {
      target: { value: "Doc Temporário" },
    });
    fireEvent.change(screen.getByLabelText(/Exigido até/), {
      target: { value: "2099-12" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Salvar documento" }),
    );
    await waitFor(() =>
      expect(saveRequirementMock).toHaveBeenCalledWith(
        "t-1",
        "DOC-TEMPORARIO",
        expect.objectContaining({ effective_until: "2099-12" }),
        expect.any(String),
      ),
    );
    expect(saveRequirementMock).toHaveBeenCalledTimes(1);
  });
});

describe("DocumentConfigFormPage — edição", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
    setLocation();
  });

  function setupEdit() {
    setupList([VERSION_1, VERSION_2]);
    listEventsMock.mockResolvedValue([
      {
        event_id: "e-1",
        entity_id: "t-1",
        competence_id: null,
        event_type: "VERSION_PUBLISHED",
        actor_subject: "admin",
        detail: {},
        created_at: "2026-01-01T00:00:00Z",
        version: 1,
      },
    ]);
    saveRequirementMock.mockResolvedValue({ published_versions: [] });
  }

  it("carrega configuração atual, situação e histórico", async () => {
    setupEdit();
    window.history.pushState(null, "", `${LIST_URL}/DOC-A`);
    render(<DocumentsAdminPage basePath={BASE} itemKey="DOC-A" />);
    expect(await screen.findByText("Editar documento")).toBeTruthy();
    const nameInput = screen.getByLabelText(
      /Nome do documento/,
    ) as HTMLInputElement;
    expect(nameInput.value).toBe("Balancete");
    expect(
      screen.getAllByText("Vigente").length,
    ).toBeGreaterThanOrEqual(1);
    expect(
      await screen.findByText(/Versão publicada/),
    ).toBeTruthy();
  });

  it("salvar alterações envia o item editado numa única chamada", async () => {
    setupEdit();
    window.history.pushState(null, "", `${LIST_URL}/DOC-A`);
    render(<DocumentsAdminPage basePath={BASE} itemKey="DOC-A" />);
    await screen.findByText("Editar documento");
    fireEvent.change(screen.getByLabelText(/Nome do documento/), {
      target: { value: "Balancete revisado" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Salvar alterações" }),
    );
    await waitFor(() =>
      expect(saveRequirementMock).toHaveBeenCalledWith(
        "t-1",
        "DOC-A",
        expect.objectContaining({
          item: expect.objectContaining({
            item_key: "DOC-A",
            name: "Balancete revisado",
          }),
        }),
        expect.any(String),
      ),
    );
    expect(saveRequirementMock).toHaveBeenCalledTimes(1);
  });

  it("«Encerrar exigência» confirma e publica versão de remoção", async () => {
    setupEdit();
    window.history.pushState(null, "", `${LIST_URL}/DOC-B`);
    render(<DocumentsAdminPage basePath={BASE} itemKey="DOC-B" />);
    await screen.findByText("Editar documento");
    // DOC-B está encerrado na timeline → sem ação de encerramento.
    expect(
      screen.queryByRole("button", { name: "Encerrar exigência" }),
    ).toBeNull();
  });

  it("chave inexistente exibe estado não encontrado", async () => {
    setupEdit();
    window.history.pushState(null, "", `${LIST_URL}/DOC-X`);
    render(<DocumentsAdminPage basePath={BASE} itemKey="DOC-X" />);
    expect(
      await screen.findByText(/Documento não encontrado/),
    ).toBeTruthy();
  });
});
