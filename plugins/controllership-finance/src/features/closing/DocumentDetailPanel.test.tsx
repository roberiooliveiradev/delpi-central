import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import {
  afterEach,
  beforeEach,
  describe,
  expect,
  it,
  vi,
} from "vitest";

vi.mock("@delpi/plugin-ui/index", async () => await import("../../test/pluginUiMock"));

const getItemMock = vi.fn();
const getValidationMock = vi.fn();
const listCorrectionsMock = vi.fn();
const listDocsMock = vi.fn();
const getDocMock = vi.fn();
const listVersionsMock = vi.fn();
const listEventsMock = vi.fn();
const listMessagesMock = vi.fn();
const postMessageMock = vi.fn();
const lookupParticipantsMock = vi.fn();
const downloadAvatarMock = vi.fn();
const downloadMock = vi.fn();
const saveBlobMock = vi.fn();
const uploadMock = vi.fn();
const replaceMock = vi.fn();
const cancelDocMock = vi.fn();

vi.mock("../../api/competencesApi", () => ({
  getCompetenceItem: (...args: unknown[]) => getItemMock(...args),
  getItemValidation: (...args: unknown[]) => getValidationMock(...args),
  listItemCorrections: (...args: unknown[]) =>
    listCorrectionsMock(...args),
  cancelChecklistItem: () =>
    Promise.reject(new Error("not mocked")),
  decideDocumentEvidence: () =>
    Promise.reject(new Error("not mocked")),
  decideItemEvidenceSet: () =>
    Promise.reject(new Error("not mocked")),
  markItemNotApplicable: () =>
    Promise.reject(new Error("not mocked")),
  requestItemCorrection: () =>
    Promise.reject(new Error("not mocked")),
  reverseRejection: () =>
    Promise.reject(new Error("not mocked")),
  reviewItemCorrection: () =>
    Promise.reject(new Error("not mocked")),
  revertItemNotApplicable: () =>
    Promise.reject(new Error("not mocked")),
}));

vi.mock("../../api/documentsApi", () => ({
  CLOSING_DOCUMENT_ACCEPT: ".pdf",
  listClosingDocuments: (...args: unknown[]) => listDocsMock(...args),
  getClosingDocument: (...args: unknown[]) => getDocMock(...args),
  listDocumentVersions: (...args: unknown[]) => listVersionsMock(...args),
  listDocumentEvents: (...args: unknown[]) => listEventsMock(...args),
  downloadClosingDocument: (...args: unknown[]) => downloadMock(...args),
  saveDocumentBlob: (...args: unknown[]) => saveBlobMock(...args),
  uploadClosingDocument: (...args: unknown[]) => uploadMock(...args),
  replaceClosingDocument: (...args: unknown[]) => replaceMock(...args),
  cancelClosingDocument: (...args: unknown[]) => cancelDocMock(...args),
  listDocumentMessages: (...args: unknown[]) => listMessagesMock(...args),
  postDocumentMessage: (...args: unknown[]) => postMessageMock(...args),
}));

vi.mock("../../api/participantsApi", () => ({
  lookupParticipants: (...args: unknown[]) =>
    lookupParticipantsMock(...args),
  downloadParticipantAvatar: (...args: unknown[]) =>
    downloadAvatarMock(...args),
}));

import { ApiError } from "../../api/httpClient";
import { DocumentDetailPanel } from "./DocumentDetailPanel";

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
  purpose: null,
  requirement_notes: null,
  source_template_item_id: null,
  source_version_id: null,
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
  current_version_no: 1,
  revision: 3,
  uploaded_by: "u-1",
  created_at: "2026-05-02T10:00:00Z",
  updated_at: "2026-05-02T10:00:00Z",
  original_name: "balancete.pdf",
  mime_type: "application/pdf",
  size_bytes: 2048,
  checksum_sha256: "a".repeat(64),
};

const VALIDATION = {
  snapshot_item_id: "s-1",
  item_key: "CK-E-01",
  state: "EXPECTED",
  validation_scope: "PER_ATTACHMENT",
  applicability: "REQUIRED",
  documents: [],
  decisions: [],
};

function renderDetail(documentRef: string, extras?: {
  onBack?: () => void;
  onOpenRef?: (ref: string) => void;
}) {
  return render(
    <DocumentDetailPanel
      period="2026-05"
      documentRef={documentRef}
      onBack={extras?.onBack ?? (() => {})}
      onOpenRef={extras?.onOpenRef ?? (() => {})}
    />,
  );
}

beforeEach(() => {
  listCorrectionsMock.mockResolvedValue([]);
  getValidationMock.mockResolvedValue(VALIDATION);
  listVersionsMock.mockResolvedValue([]);
  listEventsMock.mockResolvedValue({
    events: [],
    total: 0,
    limit: 50,
    offset: 0,
  });
  listMessagesMock.mockResolvedValue({
    messages: [],
    total: 0,
    limit: 100,
    offset: 0,
  });
  lookupParticipantsMock.mockResolvedValue({ items: [] });
  downloadAvatarMock.mockResolvedValue(new Blob(["png"]));
  downloadMock.mockResolvedValue(new Blob(["pdf"]));
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("DocumentDetailPanel — item exigido", () => {
  it("abre o detalhe pelo item com decisões reais e histórico", async () => {
    getItemMock.mockResolvedValue(ITEM);
    listDocsMock.mockResolvedValue({
      documents: [DOC],
      total: 1,
      limit: 50,
      offset: 0,
    });
    getValidationMock.mockResolvedValue({
      ...VALIDATION,
      decisions: [
        {
          decision_id: "dec-1",
          document_id: "d-1",
          scope: "PER_ATTACHMENT",
          composition: [],
          decision: "REJECTED",
          reason_code: "ILLEGIBLE",
          comment: "Arquivo ilegível.",
          result_state: "UNDER_REVIEW",
          reverses_decision_id: null,
          decided_by: "revisor-1",
          created_at: "2026-05-11T10:00:00Z",
        },
      ],
    });
    listVersionsMock.mockResolvedValue([
      {
        document_version_id: "v-1",
        document_id: "d-1",
        version_no: 1,
        state: "ATTACHED",
        uploaded_by: "u-1",
        created_at: "2026-05-02T10:00:00Z",
        original_name: "balancete.pdf",
        mime_type: "application/pdf",
        size_bytes: 2048,
        checksum_sha256: "a".repeat(64),
      },
    ]);
    listEventsMock.mockResolvedValue({
      events: [
        {
          event_id: "e-1",
          event_type: "DOCUMENT_UPLOADED",
          actor_subject: "u-1",
          detail: { version_no: 1 },
          created_at: "2026-05-02T10:00:00Z",
        },
      ],
      total: 1,
      limit: 50,
      offset: 0,
    });

    renderDetail("item:CK-E-01");

    await waitFor(() =>
      expect(screen.getByText("Balancete mensal")).toBeTruthy(),
    );
    expect(getItemMock).toHaveBeenCalledWith(
      "2026-05",
      "CK-E-01",
      expect.anything(),
    );
    expect(listDocsMock).toHaveBeenCalledWith(
      "2026-05",
      { snapshotItemId: "s-1" },
      expect.anything(),
    );
    // Decisões reais de validação renderizadas pelo painel embutido.
    await waitFor(() =>
      expect(screen.getAllByText(/Rejeitado/).length).toBeGreaterThan(0),
    );
    expect(screen.getByText(/Arquivo ilegível/)).toBeTruthy();
    expect(screen.getByText(/revisor-1/)).toBeTruthy();
    await waitFor(() =>
      expect(screen.getByText(/Arquivo anexado/)).toBeTruthy(),
    );
    expect(screen.getByTestId("file-preview")).toBeTruthy();
  });

  it("item sem arquivo mostra dropzone e envia anexo contextual", async () => {
    getItemMock.mockResolvedValue(ITEM);
    listDocsMock.mockResolvedValue({
      documents: [],
      total: 0,
      limit: 50,
      offset: 0,
    });
    getValidationMock.mockResolvedValue(VALIDATION);
    uploadMock.mockResolvedValue(DOC);

    renderDetail("item:CK-E-01");

    await waitFor(() =>
      expect(screen.getByText(/Nenhum arquivo anexado ainda/)).toBeTruthy(),
    );
    fireEvent.click(
      screen.getByLabelText("Anexar arquivo ao documento"),
    );
    await waitFor(() => expect(uploadMock).toHaveBeenCalled());
    const [period, payload] = uploadMock.mock.calls[0];
    expect(period).toBe("2026-05");
    expect(payload.snapshotItemId).toBe("s-1");
    expect(payload.title).toBe("Balancete mensal");
    expect(payload.idempotencyKey).toBeTruthy();
  });

  it("download e nova versão preservam revisão e idempotência", async () => {
    getItemMock.mockResolvedValue(ITEM);
    listDocsMock.mockResolvedValue({
      documents: [DOC],
      total: 1,
      limit: 50,
      offset: 0,
    });
    getValidationMock.mockResolvedValue(VALIDATION);
    listVersionsMock.mockResolvedValue([]);
    listEventsMock.mockResolvedValue({
      events: [],
      total: 0,
      limit: 50,
      offset: 0,
    });
    downloadMock.mockResolvedValue(new Blob(["pdf"]));
    replaceMock.mockResolvedValue({ ...DOC, current_version_no: 2 });

    const { container } = renderDetail("item:CK-E-01");

    await waitFor(() =>
      expect(screen.getByText("Baixar")).toBeTruthy(),
    );
    fireEvent.click(screen.getByText("Baixar"));
    await waitFor(() =>
      expect(downloadMock).toHaveBeenCalledWith("2026-05", "d-1", 1),
    );

    fireEvent.click(screen.getByText("Enviar nova versão"));
    fireEvent.change(
      container.querySelector('input[type="file"]') as HTMLInputElement,
      {
        target: {
          files: [new File(["x"], "v2.pdf", { type: "application/pdf" })],
        },
      },
    );
    await waitFor(() => expect(replaceMock).toHaveBeenCalled());
    const [, documentId, payload] = replaceMock.mock.calls[0];
    expect(documentId).toBe("d-1");
    expect(payload.revision).toBe(3);
    expect(payload.idempotencyKey).toBeTruthy();
  });
});

describe("DocumentDetailPanel — documento adicional", () => {
  it("abre pelo id com prévia, interações honestas e histórico", async () => {
    getDocMock.mockResolvedValue({
      ...DOC,
      link_kind: "competence",
      snapshot_item_id: null,
    });
    listVersionsMock.mockResolvedValue([]);
    listEventsMock.mockResolvedValue({
      events: [],
      total: 0,
      limit: 50,
      offset: 0,
    });

    renderDetail("d-1");

    await waitFor(() =>
      expect(screen.getByTestId("file-preview")).toBeTruthy(),
    );
    expect(getDocMock).toHaveBeenCalledWith(
      "2026-05",
      "d-1",
      expect.anything(),
    );
    await waitFor(() =>
      expect(
        screen.getByText(
          /Nenhuma mensagem ainda\. Você pode iniciar a conversa/,
        ),
      ).toBeTruthy(),
    );
    expect(
      screen.getByRole("button", { name: "Enviar mensagem" }),
    ).toBeTruthy();
  });
});

describe("DocumentDetailPanel — novo documento adicional", () => {
  it("anexa sem exigência e navega ao documento criado", async () => {
    uploadMock.mockResolvedValue({ ...DOC, document_id: "d-9" });
    const onOpenRef = vi.fn();

    renderDetail("new", { onOpenRef });

    fireEvent.change(screen.getByLabelText("Nome do documento"), {
      target: { value: "Comprovante extra" },
    });
    fireEvent.click(
      screen.getByLabelText("Anexar documento adicional"),
    );

    await waitFor(() => expect(uploadMock).toHaveBeenCalled());
    const [period, payload] = uploadMock.mock.calls[0];
    expect(period).toBe("2026-05");
    expect(payload.snapshotItemId).toBeNull();
    expect(payload.title).toBe("Comprovante extra");
    await waitFor(() =>
      expect(onOpenRef).toHaveBeenCalledWith("d-9"),
    );
  });
});

describe("DocumentDetailPanel — estados honestos", () => {
  it("documento inexistente exibe erro sem inventar conteúdo", async () => {
    getDocMock.mockRejectedValue(
      new ApiError(404, "Not found", "document_not_found"),
    );

    renderDetail("d-404");

    await waitFor(() =>
      expect(
        screen.getByText(/não encontrado ou fora do escopo/),
      ).toBeTruthy(),
    );
  });

  it("voltar chama o retorno contextual", async () => {
    getDocMock.mockResolvedValue(DOC);
    const onBack = vi.fn();

    renderDetail("d-1", { onBack });

    fireEvent.click(screen.getByText(/Voltar aos documentos/));
    expect(onBack).toHaveBeenCalled();
  });
});

describe("DocumentDetailPanel — prévia e ciclo de vida", () => {
  const DOC_WITH_VERSIONS = [
    {
      document_version_id: "v-1",
      document_id: "d-1",
      version_no: 1,
      state: "SUPERSEDED",
      uploaded_by: "u-1",
      created_at: "2026-05-02T10:00:00Z",
      original_name: "balancete.pdf",
      mime_type: "application/pdf",
      size_bytes: 2048,
      checksum_sha256: "a".repeat(64),
    },
    {
      document_version_id: "v-2",
      document_id: "d-1",
      version_no: 2,
      state: "ATTACHED",
      uploaded_by: "u-2",
      created_at: "2026-05-10T10:00:00Z",
      original_name: "balancete.pdf",
      mime_type: "application/pdf",
      size_bytes: 4096,
      checksum_sha256: "b".repeat(64),
    },
  ];

  it("regressão: a prévia chama o download uma única vez por documento", async () => {
    getDocMock.mockResolvedValue({
      ...DOC,
      link_kind: "competence",
      snapshot_item_id: null,
      current_version_no: 2,
    });

    renderDetail("d-1");

    await waitFor(() =>
      expect(downloadMock).toHaveBeenCalledWith("2026-05", "d-1", 2),
    );
    // Re-renderizações subsequentes NÃO podem refazer o fetch (raiz do
    // bug produtivo: spinner infinito + enxurrada de DOCUMENT_DOWNLOADED).
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(downloadMock).toHaveBeenCalledTimes(1);
  });

  it("falha na prévia oferece retry sem travar o download manual", async () => {
    getDocMock.mockResolvedValue({
      ...DOC,
      link_kind: "competence",
      snapshot_item_id: null,
    });
    downloadMock
      .mockRejectedValueOnce(new ApiError(500, "erro", null))
      .mockResolvedValue(new Blob(["pdf"]));

    renderDetail("d-1");

    await waitFor(() =>
      expect(screen.getByText("Tentar novamente")).toBeTruthy(),
    );
    // Download manual independe da prévia.
    fireEvent.click(screen.getByText("Baixar"));
    await waitFor(() =>
      expect(saveBlobMock).toHaveBeenCalled(),
    );

    fireEvent.click(screen.getByText("Tentar novamente"));
    await waitFor(() =>
      expect(downloadMock).toHaveBeenCalledTimes(3),
    );
  });

  it("selecionar versão anterior troca prévia e download para v1", async () => {
    getDocMock.mockResolvedValue({
      ...DOC,
      link_kind: "competence",
      snapshot_item_id: null,
      current_version_no: 2,
    });
    listVersionsMock.mockResolvedValue(DOC_WITH_VERSIONS);

    renderDetail("d-1");

    await waitFor(() =>
      expect(downloadMock).toHaveBeenCalledWith("2026-05", "d-1", 2),
    );
    fireEvent.click(screen.getByText(/v1 — substituída/));
    await waitFor(() =>
      expect(downloadMock).toHaveBeenCalledWith("2026-05", "d-1", 1),
    );
    fireEvent.click(screen.getByText("Baixar"));
    await waitFor(() =>
      expect(downloadMock).toHaveBeenLastCalledWith("2026-05", "d-1", 1),
    );
  });

  it("remoção lógica: confirma, chama U7 com a revisão e sai da lista", async () => {
    getDocMock.mockResolvedValue({
      ...DOC,
      link_kind: "competence",
      snapshot_item_id: null,
    });
    cancelDocMock.mockResolvedValue({ ...DOC, state: "CANCELLED" });
    const onBack = vi.fn();

    renderDetail("d-1", { onBack });

    await waitFor(() =>
      expect(screen.getByText("Remover documento")).toBeTruthy(),
    );
    fireEvent.click(screen.getByText("Remover documento"));
    const removeButtons = screen.getAllByRole("button", {
      name: "Remover documento",
    });
    fireEvent.click(removeButtons[removeButtons.length - 1]);

    await waitFor(() =>
      expect(cancelDocMock).toHaveBeenCalledWith(
        "2026-05",
        "d-1",
        { revision: 3 },
      ),
    );
    await waitFor(() => expect(onBack).toHaveBeenCalled());
  });

  it("cancelamento da confirmação não chama U7", async () => {
    getDocMock.mockResolvedValue({
      ...DOC,
      link_kind: "competence",
      snapshot_item_id: null,
    });

    renderDetail("d-1");

    await waitFor(() =>
      expect(screen.getByText("Remover documento")).toBeTruthy(),
    );
    fireEvent.click(screen.getByText("Remover documento"));
    fireEvent.click(screen.getByText("Voltar"));
    expect(cancelDocMock).not.toHaveBeenCalled();
  });

  it("histórico operacional não exibe eventos de download", async () => {
    getDocMock.mockResolvedValue({
      ...DOC,
      link_kind: "competence",
      snapshot_item_id: null,
    });
    listEventsMock.mockResolvedValue({
      events: [
        {
          event_id: "e-1",
          event_type: "DOCUMENT_UPLOADED",
          actor_subject: "u-1",
          detail: { version_no: 1 },
          created_at: "2026-05-02T10:00:00Z",
        },
        {
          event_id: "e-2",
          event_type: "DOCUMENT_DOWNLOADED",
          actor_subject: "u-1",
          detail: { version_no: 1, result: "AUTHORIZED" },
          created_at: "2026-05-02T11:00:00Z",
        },
      ],
      total: 2,
      limit: 50,
      offset: 0,
    });

    renderDetail("d-1");

    await waitFor(() =>
      expect(screen.getByText("Arquivo anexado")).toBeTruthy(),
    );
    expect(screen.queryByText("Download", { exact: true })).toBeNull();
    expect(
      screen.getByText(/trilha de auditoria/),
    ).toBeTruthy();
  });
});

describe("DocumentDetailPanel — conversa do documento (U9)", () => {
  const MESSAGE = {
    message_id: "m-1",
    document_id: "d-1",
    competence_id: "c-1",
    version_no: 1,
    audience: "INTERNAL",
    body: "Documento recebido para conferência.",
    author_subject: "u-9",
    author_name: "Ana Souza",
    created_at: "2026-05-12T10:00:00Z",
    mine: false,
  };

  function renderDocument() {
    getDocMock.mockResolvedValue({ ...DOC });
    renderDetail("d-1");
  }

  it("carrega a conversa persistida com autor e texto", async () => {
    listMessagesMock.mockResolvedValue({
      messages: [MESSAGE],
      total: 1,
      limit: 100,
      offset: 0,
    });

    renderDocument();

    await waitFor(() =>
      expect(
        screen.getByText(/Documento recebido para conferência\./),
      ).toBeTruthy(),
    );
    expect(screen.getByText(/Ana Souza/)).toBeTruthy();
    expect(listMessagesMock).toHaveBeenCalledWith(
      "2026-05",
      "d-1",
      expect.anything(),
      expect.anything(),
    );
    expect(
      screen.getByRole("button", { name: "Enviar mensagem" }),
    ).toBeTruthy();
  });

  it("envia a primeira mensagem e exibe somente após confirmação", async () => {
    postMessageMock.mockResolvedValue({ ...MESSAGE, mine: true });

    renderDocument();

    await waitFor(() =>
      expect(
        screen.getByText(/Nenhuma mensagem ainda/),
      ).toBeTruthy(),
    );
    fireEvent.change(
      screen.getByLabelText(
        "Escreva uma mensagem sobre este documento…",
      ),
      { target: { value: "Favor conferir os valores de setembro." } },
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Enviar mensagem" }),
    );

    await waitFor(() =>
      expect(postMessageMock).toHaveBeenCalledWith(
        "2026-05",
        "d-1",
        {
          body: "Favor conferir os valores de setembro.",
          idempotencyKey: expect.any(String),
        },
      ),
    );
    await waitFor(() =>
      expect(
        screen.getByText(/Documento recebido para conferência\./),
      ).toBeTruthy(),
    );
    expect(
      (screen.getByLabelText(
        "Escreva uma mensagem sobre este documento…",
      ) as HTMLTextAreaElement).value,
    ).toBe("");
  });

  it("falha no envio preserva o texto e mostra erro", async () => {
    postMessageMock.mockRejectedValue(
      new Error("boom"),
    );

    renderDocument();

    await waitFor(() =>
      expect(
        screen.getByText(/Nenhuma mensagem ainda/),
      ).toBeTruthy(),
    );
    fireEvent.change(
      screen.getByLabelText(
        "Escreva uma mensagem sobre este documento…",
      ),
      { target: { value: "Texto que deve sobreviver." } },
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Enviar mensagem" }),
    );

    await waitFor(() =>
      expect(
        screen.getByText(/Falha ao enviar a mensagem/),
      ).toBeTruthy(),
    );
    expect(
      (screen.getByLabelText(
        "Escreva uma mensagem sobre este documento…",
      ) as HTMLTextAreaElement).value,
    ).toBe("Texto que deve sobreviver.");
  });

  it("retry do mesmo texto reutiliza a idempotency_key", async () => {
    postMessageMock
      .mockRejectedValueOnce(new Error("boom"))
      .mockResolvedValueOnce({ ...MESSAGE, mine: true });

    renderDocument();

    await waitFor(() =>
      expect(
        screen.getByText(/Nenhuma mensagem ainda/),
      ).toBeTruthy(),
    );
    fireEvent.change(
      screen.getByLabelText(
        "Escreva uma mensagem sobre este documento…",
      ),
      { target: { value: "Mesma tentativa" } },
    );
    const send = () =>
      fireEvent.click(
        screen.getByRole("button", { name: "Enviar mensagem" }),
      );
    send();
    await waitFor(() =>
      expect(
        screen.getByText(/Falha ao enviar a mensagem/),
      ).toBeTruthy(),
    );
    send();
    await waitFor(() =>
      expect(postMessageMock).toHaveBeenCalledTimes(2),
    );
    const first = postMessageMock.mock.calls[0][2] as {
      idempotencyKey: string;
    };
    const second = postMessageMock.mock.calls[1][2] as {
      idempotencyKey: string;
    };
    expect(second.idempotencyKey).toBe(first.idempotencyKey);
  });

  it("item exigido também tem conversa no documento selecionado", async () => {
    getItemMock.mockResolvedValue(ITEM);
    listDocsMock.mockResolvedValue({
      documents: [DOC],
      total: 1,
      limit: 50,
      offset: 0,
    });

    renderDetail("item:CK-E-01");

    await waitFor(() =>
      expect(listMessagesMock).toHaveBeenCalledWith(
        "2026-05",
        "d-1",
        expect.anything(),
        expect.anything(),
      ),
    );
    expect(
      screen.getByRole("button", { name: "Enviar mensagem" }),
    ).toBeTruthy();
  });
});

describe("DocumentDetailPanel — linha do tempo e avatares (UX-009)", () => {
  const EVENT = {
    event_id: "ev-1",
    event_type: "DOCUMENT_UPLOADED",
    actor_subject: "11111111-2222-3333-4444-555555555555",
    detail: { version_no: 1 },
    created_at: "2026-05-02T10:00:00Z",
  };

  function renderDocument() {
    getDocMock.mockResolvedValue({ ...DOC });
    renderDetail("d-1");
  }

  it("apresenta o histórico como linha do tempo com nome oficial do autor", async () => {
    listEventsMock.mockResolvedValue({
      events: [EVENT],
      total: 1,
      limit: 50,
      offset: 0,
    });
    lookupParticipantsMock.mockResolvedValue({
      items: [
        {
          user_id: EVENT.actor_subject,
          display_name: "Ana Souza",
          has_photo: false,
        },
      ],
    });

    renderDocument();

    await waitFor(() =>
      expect(screen.getByText("Arquivo anexado")).toBeTruthy(),
    );
    // UUID nunca aparece na UI; nome oficial do diretório Core sim.
    expect(screen.queryByText(new RegExp(EVENT.actor_subject))).toBeNull();
    await waitFor(() =>
      expect(screen.getByText("Ana Souza")).toBeTruthy(),
    );
    expect(lookupParticipantsMock).toHaveBeenCalledWith(
      [EVENT.actor_subject],
      expect.anything(),
    );
  });

  it("mantém downloads e mensagens fora da linha do tempo", async () => {
    listEventsMock.mockResolvedValue({
      events: [
        EVENT,
        {
          ...EVENT,
          event_id: "ev-2",
          event_type: "DOCUMENT_DOWNLOADED",
        },
        {
          ...EVENT,
          event_id: "ev-3",
          event_type: "DOCUMENT_MESSAGE_POSTED",
        },
      ],
      total: 3,
      limit: 50,
      offset: 0,
    });

    renderDocument();

    await waitFor(() =>
      expect(screen.getByText("Arquivo anexado")).toBeTruthy(),
    );
    expect(screen.queryByText("Download")).toBeNull();
  });

  it("exibe o estado vazio honesto quando não há eventos materiais", async () => {
    renderDocument();

    await waitFor(() =>
      expect(
        screen.getByText(
          "Ainda não há alterações registradas neste documento.",
        ),
      ).toBeTruthy(),
    );
  });

  it("resolve a foto do autor da mensagem via contrato de participantes", async () => {
    const author = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee";
    listMessagesMock.mockResolvedValue({
      messages: [
        {
          message_id: "m-1",
          document_id: "d-1",
          competence_id: "c-1",
          version_no: 1,
          audience: "INTERNAL",
          body: "Conferido o balancete.",
          author_subject: author,
          author_name: null,
          created_at: "2026-05-12T10:00:00Z",
          mine: false,
        },
      ],
      total: 1,
      limit: 100,
      offset: 0,
    });
    lookupParticipantsMock.mockResolvedValue({
      items: [
        {
          user_id: author,
          display_name: "Robério Oliveira",
          has_photo: true,
        },
      ],
    });
    const createUrl = vi.fn(() => "blob:http://localhost/photo-1");
    const revokeUrl = vi.fn();
    vi.stubGlobal("URL", {
      ...URL,
      createObjectURL: createUrl,
      revokeObjectURL: revokeUrl,
    });
    try {
      const { container } = render(
        <DocumentDetailPanel
          period="2026-05"
          documentRef="d-1"
          onBack={() => {}}
          onOpenRef={() => {}}
        />,
      );

      await waitFor(() =>
        expect(downloadAvatarMock).toHaveBeenCalledWith(
          author,
          expect.anything(),
        ),
      );
      const item = container.querySelector(
        "li[data-author-src]",
      ) as HTMLElement | null;
      expect(item?.dataset.authorSrc).toBe(
        "blob:http://localhost/photo-1",
      );
      expect(screen.getByText(/Robério Oliveira/)).toBeTruthy();
    } finally {
      vi.unstubAllGlobals();
    }
  });

  it("perfil indisponível cai em identificação neutra, nunca UUID", async () => {
    listMessagesMock.mockResolvedValue({
      messages: [
        {
          message_id: "m-2",
          document_id: "d-1",
          competence_id: "c-1",
          version_no: 1,
          audience: "INTERNAL",
          body: "Olá.",
          author_subject:
            "ffffffff-1111-2222-3333-444444444444",
          author_name: null,
          created_at: "2026-05-12T10:00:00Z",
          mine: false,
        },
      ],
      total: 1,
      limit: 100,
      offset: 0,
    });
    lookupParticipantsMock.mockRejectedValue(
      new Error("core down"),
    );

    renderDocument();

    await waitFor(() =>
      expect(screen.getByText(/Participante/)).toBeTruthy(),
    );
    expect(
      screen.queryByText(/ffffffff-1111/),
    ).toBeNull();
  });
});
