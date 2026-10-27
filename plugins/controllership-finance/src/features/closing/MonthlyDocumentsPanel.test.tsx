import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@delpi/plugin-ui/index", async () => await import("../../test/pluginUiMock"));

const listItemsMock = vi.fn();
const getValidationMock = vi.fn();
const listDocsMock = vi.fn();
const replaceMock = vi.fn();
const cancelDocMock = vi.fn();

vi.mock("../../api/competencesApi", () => ({
  listCompetenceItems: (...args: unknown[]) => listItemsMock(...args),
  getItemValidation: (...args: unknown[]) => getValidationMock(...args),
}));

vi.mock("../../api/documentsApi", () => ({
  CLOSING_DOCUMENT_ACCEPT: ".pdf",
  listClosingDocuments: (...args: unknown[]) => listDocsMock(...args),
  replaceClosingDocument: (...args: unknown[]) => replaceMock(...args),
  cancelClosingDocument: (...args: unknown[]) => cancelDocMock(...args),
}));

import { ApiError } from "../../api/httpClient";
import { MonthlyDocumentsPanel } from "./MonthlyDocumentsPanel";

const ITEM = {
  snapshot_item_id: "s-1",
  item_key: "CK-E-01",
  sort_order: 1,
  sheet: "ELETRONICO",
  name: "Balancete mensal",
  origin_kind: "TOTVS",
  recipient_area: "CONTABIL",
  applicability: "REQUIRED",
  branch_scope: "BOTH",
  totvs_report_ref: null,
  state: "EXPECTED",
  validation_scope: "PER_ATTACHMENT",
  exceptional: false,
  revision: 1,
  state_reason: null,
};

const DOC = {
  document_id: "d-1",
  competence_id: "c-1",
  link_kind: "competence_item",
  snapshot_item_id: "s-1",
  snapshot_item_key: "CK-E-01",
  title: "Balancete mensal",
  attachment_role: "generic",
  state: "ATTACHED",
  current_version_no: 2,
  revision: 3,
  uploaded_by: "u-1",
  created_at: "2026-05-02T10:00:00Z",
  updated_at: "2026-05-10T10:00:00Z",
  original_name: "balancete.pdf",
  mime_type: "application/pdf",
  size_bytes: 2048,
  checksum_sha256: "a".repeat(64),
};

const ADDITIONAL_DOC = {
  ...DOC,
  document_id: "d-2",
  link_kind: "competence",
  snapshot_item_id: null,
  snapshot_item_key: null,
  title: "Planilha extra",
  original_name: "planilha-extra.xlsx",
};

const EMPTY_VALIDATION = {
  snapshot_item_id: "s-1",
  item_key: "CK-E-01",
  state: "EXPECTED",
  validation_scope: "PER_ATTACHMENT",
  applicability: "REQUIRED",
  documents: [],
  decisions: [],
};

const REJECTED_VALIDATION = {
  ...EMPTY_VALIDATION,
  decisions: [
    {
      decision_id: "dec-1",
      document_id: "d-1",
      scope: "PER_ATTACHMENT",
      composition: [{ document_id: "d-1", version_no: 2 }],
      decision: "REJECTED",
      reason_code: "WRONG_COMPETENCE",
      comment: "Documento do mês anterior.",
      result_state: "UNDER_REVIEW",
      reverses_decision_id: null,
      decided_by: "revisor-1",
      created_at: "2026-05-11T10:00:00Z",
    },
  ],
};

function renderPanel(overrides: {
  search?: string;
  stateFilter?: string;
  onOpenDetail?: (ref: string) => void;
}) {
  return render(
    <MonthlyDocumentsPanel
      period="2026-05"
      search={overrides.search ?? ""}
      stateFilter={overrides.stateFilter ?? "all"}
      onFiltersChange={() => {}}
      onOpenDetail={overrides.onOpenDetail ?? (() => {})}
    />,
  );
}

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("MonthlyDocumentsPanel — cartões V0.2", () => {
  it("exige documento exigido e documento adicional em cartões", async () => {
    listItemsMock.mockResolvedValue([ITEM]);
    listDocsMock.mockResolvedValue({
      documents: [DOC, ADDITIONAL_DOC],
      total: 2,
      limit: 50,
      offset: 0,
    });
    getValidationMock.mockResolvedValue(EMPTY_VALIDATION);

    renderPanel({});

    await waitFor(() =>
      expect(screen.getByText("Balancete mensal")).toBeTruthy(),
    );
    expect(screen.getByText("Planilha extra")).toBeTruthy();
    expect(screen.getByText(/Exigido/)).toBeTruthy();
    expect(screen.getByText(/Adicional/)).toBeTruthy();
    expect(screen.getAllByText("Ver documento").length).toBe(2);
    expect(screen.getAllByText(/v2/).length).toBeGreaterThan(0);
  });

  it("item sem arquivo mostra situação de aguardo sem inventar conteúdo", async () => {
    listItemsMock.mockResolvedValue([ITEM]);
    listDocsMock.mockResolvedValue({
      documents: [],
      total: 0,
      limit: 50,
      offset: 0,
    });
    getValidationMock.mockResolvedValue(EMPTY_VALIDATION);

    renderPanel({});

    await waitFor(() =>
      expect(screen.getByText("Aguardando documento")).toBeTruthy(),
    );
    expect(screen.getByText("Balancete mensal")).toBeTruthy();
  });

  it("mês sem exigências nem arquivos mostra estado vazio honesto", async () => {
    listItemsMock.mockResolvedValue([]);
    listDocsMock.mockResolvedValue({
      documents: [],
      total: 0,
      limit: 50,
      offset: 0,
    });

    renderPanel({});

    await waitFor(() =>
      expect(
        screen.getByText(/Nenhum documento exigido para este fechamento/),
      ).toBeTruthy(),
    );
  });

  it("pesquisa por nome restringe os cartões", async () => {
    listItemsMock.mockResolvedValue([ITEM]);
    listDocsMock.mockResolvedValue({
      documents: [ADDITIONAL_DOC],
      total: 1,
      limit: 50,
      offset: 0,
    });
    getValidationMock.mockResolvedValue(EMPTY_VALIDATION);

    renderPanel({ search: "planilha" });

    await waitFor(() =>
      expect(screen.getByText("Planilha extra")).toBeTruthy(),
    );
    expect(screen.queryByText("Balancete mensal")).toBeNull();
  });

  it("filtro de situação restringe aos conferidos", async () => {
    listItemsMock.mockResolvedValue([
      ITEM,
      { ...ITEM, item_key: "CK-E-02", snapshot_item_id: "s-2", name: "Razão", state: "ACCEPTED" },
    ]);
    listDocsMock.mockResolvedValue({
      documents: [],
      total: 0,
      limit: 50,
      offset: 0,
    });
    getValidationMock.mockResolvedValue(EMPTY_VALIDATION);

    renderPanel({ stateFilter: "accepted" });

    await waitFor(() => expect(screen.getByText("Razão")).toBeTruthy());
    expect(screen.queryByText("Balancete mensal")).toBeNull();
  });

  it("resumo lista solicitações reais de ajuste e abre a conversa", async () => {
    listItemsMock.mockResolvedValue([ITEM]);
    listDocsMock.mockResolvedValue({
      documents: [DOC],
      total: 1,
      limit: 50,
      offset: 0,
    });
    getValidationMock.mockResolvedValue(REJECTED_VALIDATION);
    const onOpenDetail = vi.fn();

    renderPanel({ onOpenDetail });

    await waitFor(() =>
      expect(screen.getByText(/Documento do mês anterior/)).toBeTruthy(),
    );
    expect(screen.getByText(/revisor-1/)).toBeTruthy();
    expect(
      screen.getByText(/solicitação\(ões\) aguardando atenção/),
    ).toBeTruthy();

    fireEvent.click(screen.getByText("Abrir conversa"));
    expect(onOpenDetail).toHaveBeenCalledWith("item:CK-E-01");
  });

  it("Ver documento navega com a referência correta por tipo", async () => {
    listItemsMock.mockResolvedValue([ITEM]);
    listDocsMock.mockResolvedValue({
      documents: [ADDITIONAL_DOC],
      total: 1,
      limit: 50,
      offset: 0,
    });
    getValidationMock.mockResolvedValue(EMPTY_VALIDATION);
    const onOpenDetail = vi.fn();

    renderPanel({ onOpenDetail });
    await waitFor(() => expect(screen.getAllByText("Ver documento").length).toBe(2));

    const buttons = screen.getAllByText("Ver documento");
    fireEvent.click(buttons[0]);
    expect(onOpenDetail).toHaveBeenCalledWith("item:CK-E-01");
    fireEvent.click(buttons[1]);
    expect(onOpenDetail).toHaveBeenCalledWith("d-2");
  });

  it("Adicionar documento abre a referência new", async () => {
    listItemsMock.mockResolvedValue([]);
    listDocsMock.mockResolvedValue({
      documents: [],
      total: 0,
      limit: 50,
      offset: 0,
    });
    const onOpenDetail = vi.fn();

    renderPanel({ onOpenDetail });
    await waitFor(() =>
      expect(screen.getByText("Adicionar documento")).toBeTruthy(),
    );
    fireEvent.click(screen.getByText("Adicionar documento"));
    expect(onOpenDetail).toHaveBeenCalledWith("new");
  });

  it("falha de autorização exibe banner e não inventa cartões", async () => {
    listItemsMock.mockRejectedValue(
      new ApiError(403, "Forbidden", "forbidden"),
    );
    listDocsMock.mockResolvedValue({
      documents: [],
      total: 0,
      limit: 50,
      offset: 0,
    });

    renderPanel({});

    await waitFor(() =>
      expect(screen.getByText(/não tem autorização/)).toBeTruthy(),
    );
  });

  it("documento cancelado não aparece como adicional ativo", async () => {
    listItemsMock.mockResolvedValue([]);
    listDocsMock.mockResolvedValue({
      documents: [{ ...ADDITIONAL_DOC, state: "CANCELLED" }],
      total: 1,
      limit: 50,
      offset: 0,
    });

    renderPanel({});

    await waitFor(() =>
      expect(
        screen.getByText(/Nenhum documento exigido para este fechamento/),
      ).toBeTruthy(),
    );
    expect(screen.queryByText("Planilha extra")).toBeNull();
  });
});

describe("MonthlyDocumentsPanel — menu de três pontos", () => {
  it("abre menu acessível com ações do documento", async () => {
    listItemsMock.mockResolvedValue([ITEM]);
    listDocsMock.mockResolvedValue({
      documents: [DOC],
      total: 1,
      limit: 50,
      offset: 0,
    });
    getValidationMock.mockResolvedValue(EMPTY_VALIDATION);
    const onOpenDetail = vi.fn();

    renderPanel({ onOpenDetail });

    await waitFor(() =>
      expect(
        screen.getByLabelText("Ações de Balancete mensal"),
      ).toBeTruthy(),
    );
    fireEvent.click(screen.getByLabelText("Ações de Balancete mensal"));

    const menu = screen.getByRole("menu");
    expect(menu).toBeTruthy();
    fireEvent.click(
      screen.getByRole("menuitem", { name: "Abrir documento" }),
    );
    expect(onOpenDetail).toHaveBeenCalledWith("item:CK-E-01");
  });

  it("item sem arquivo não oferece nova versão nem remoção", async () => {
    listItemsMock.mockResolvedValue([ITEM]);
    listDocsMock.mockResolvedValue({
      documents: [],
      total: 0,
      limit: 50,
      offset: 0,
    });
    getValidationMock.mockResolvedValue(EMPTY_VALIDATION);

    renderPanel({});

    await waitFor(() =>
      expect(
        screen.getByLabelText("Ações de Balancete mensal"),
      ).toBeTruthy(),
    );
    fireEvent.click(screen.getByLabelText("Ações de Balancete mensal"));

    expect(
      screen.getByRole("menuitem", { name: "Abrir documento" }),
    ).toBeTruthy();
    expect(
      screen.queryByRole("menuitem", { name: "Enviar nova versão" }),
    ).toBeNull();
    expect(
      screen.queryByRole("menuitem", { name: "Remover documento" }),
    ).toBeNull();
  });

  it("nova versão pelo cartão usa U5 com revisão e idempotência", async () => {
    listItemsMock.mockResolvedValue([]);
    listDocsMock.mockResolvedValue({
      documents: [ADDITIONAL_DOC],
      total: 1,
      limit: 50,
      offset: 0,
    });
    replaceMock.mockResolvedValue({
      ...ADDITIONAL_DOC,
      current_version_no: 3,
    });

    const { container } = renderPanel({});

    await waitFor(() =>
      expect(
        screen.getByLabelText("Ações de Planilha extra"),
      ).toBeTruthy(),
    );
    fireEvent.click(screen.getByLabelText("Ações de Planilha extra"));
    fireEvent.click(
      screen.getByRole("menuitem", { name: "Enviar nova versão" }),
    );
    fireEvent.change(
      container.querySelector("input[type=file]") as HTMLInputElement,
      {
        target: {
          files: [new File(["x"], "v3.xlsx")],
        },
      },
    );

    await waitFor(() => expect(replaceMock).toHaveBeenCalled());
    const [, documentId, payload] = replaceMock.mock.calls[0];
    expect(documentId).toBe("d-2");
    expect(payload.revision).toBe(3);
    expect(payload.idempotencyKey).toBeTruthy();
    await waitFor(() =>
      expect(screen.getByText(/versão anterior foi preservada/)).toBeTruthy(),
    );
  });

  it("remoção lógica pelo cartão confirma e chama U7", async () => {
    listItemsMock.mockResolvedValue([]);
    listDocsMock.mockResolvedValue({
      documents: [ADDITIONAL_DOC],
      total: 1,
      limit: 50,
      offset: 0,
    });
    cancelDocMock.mockResolvedValue({
      ...ADDITIONAL_DOC,
      state: "CANCELLED",
    });

    renderPanel({});

    await waitFor(() =>
      expect(
        screen.getByLabelText("Ações de Planilha extra"),
      ).toBeTruthy(),
    );
    fireEvent.click(screen.getByLabelText("Ações de Planilha extra"));
    fireEvent.click(
      screen.getByRole("menuitem", { name: "Remover documento" }),
    );

    // Confirmação cita o arquivo e a preservação do histórico.
    expect(screen.getByText(/planilha-extra\.xlsx/)).toBeTruthy();
    expect(
      screen.getByText(/versões e o histórico ficam preservados/),
    ).toBeTruthy();

    const confirm = screen.getAllByRole("button", {
      name: "Remover documento",
    });
    fireEvent.click(confirm[confirm.length - 1]);

    await waitFor(() =>
      expect(cancelDocMock).toHaveBeenCalledWith(
        "2026-05",
        "d-2",
        { revision: 3 },
      ),
    );
    await waitFor(() =>
      expect(
        screen.getByText(/histórico foram preservados/),
      ).toBeTruthy(),
    );
  });

  it("confirmação de remoção em item exigido avisa que a exigência permanece", async () => {
    listItemsMock.mockResolvedValue([ITEM]);
    listDocsMock.mockResolvedValue({
      documents: [DOC],
      total: 1,
      limit: 50,
      offset: 0,
    });
    getValidationMock.mockResolvedValue(EMPTY_VALIDATION);

    renderPanel({});

    await waitFor(() =>
      expect(
        screen.getByLabelText("Ações de Balancete mensal"),
      ).toBeTruthy(),
    );
    fireEvent.click(screen.getByLabelText("Ações de Balancete mensal"));
    fireEvent.click(
      screen.getByRole("menuitem", { name: "Remover documento" }),
    );

    expect(
      screen.getByText(/exigência deste documento continua valendo/),
    ).toBeTruthy();

    fireEvent.click(screen.getByText("Voltar"));
    expect(cancelDocMock).not.toHaveBeenCalled();
  });
});
