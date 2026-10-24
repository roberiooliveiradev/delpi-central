import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@delpi/plugin-ui/index", async () => await import("../../test/pluginUiMock"));

const getValidationMock = vi.fn();
const listCorrectionsMock = vi.fn();
const listDocumentsMock = vi.fn();
const decideDocMock = vi.fn();
const decideSetMock = vi.fn();
const reverseMock = vi.fn();
const markNaMock = vi.fn();
const revertNaMock = vi.fn();
const cancelItemMock = vi.fn();
const requestCorrectionMock = vi.fn();
const reviewCorrectionMock = vi.fn();

vi.mock("../../api/competencesApi", () => ({
  getItemValidation: (...args: unknown[]) => getValidationMock(...args),
  listItemCorrections: (...args: unknown[]) =>
    listCorrectionsMock(...args),
  decideDocumentEvidence: (...args: unknown[]) => decideDocMock(...args),
  decideItemEvidenceSet: (...args: unknown[]) => decideSetMock(...args),
  reverseRejection: (...args: unknown[]) => reverseMock(...args),
  markItemNotApplicable: (...args: unknown[]) => markNaMock(...args),
  revertItemNotApplicable: (...args: unknown[]) => revertNaMock(...args),
  cancelChecklistItem: (...args: unknown[]) => cancelItemMock(...args),
  requestItemCorrection: (...args: unknown[]) =>
    requestCorrectionMock(...args),
  reviewItemCorrection: (...args: unknown[]) =>
    reviewCorrectionMock(...args),
}));

vi.mock("../../api/documentsApi", () => ({
  listClosingDocuments: (...args: unknown[]) => listDocumentsMock(...args),
}));

import { ApiError } from "../../api/httpClient";
import { ItemValidationPanel } from "./ItemValidationPanel";

const ITEM = {
  snapshot_item_id: "s-1",
  item_key: "CK-E-01",
  sort_order: 1,
  sheet: "ELETRONICO",
  name: "Extrato bancário",
  origin_kind: "EXTERNAL",
  recipient_area: "CONTABIL",
  applicability: "CONDITIONAL",
  branch_scope: "BOTH",
  totvs_report_ref: null,
  state: "EXPECTED",
  validation_scope: "PER_ATTACHMENT",
  exceptional: false,
  revision: 1,
  state_reason: null,
  purpose: null,
  requirement_notes: null,
  source_template_item_id: "t-1",
  source_version_id: "v-1",
} as const;

const DOC = {
  document_id: "d-1",
  competence_id: "c-1",
  link_kind: "competence_item",
  snapshot_item_id: "s-1",
  snapshot_item_key: "CK-E-01",
  title: "Extrato",
  attachment_role: "generic",
  state: "ATTACHED",
  current_version_no: 1,
  revision: 1,
  uploaded_by: "u-1",
  created_at: "2026-05-02T10:00:00Z",
  updated_at: "2026-05-02T10:00:00Z",
  original_name: "extrato.pdf",
  mime_type: "application/pdf",
  size_bytes: 2048,
  checksum_sha256: "a".repeat(64),
};

const VALIDATION = {
  snapshot_item_id: "s-1",
  item_key: "CK-E-01",
  state: "EXPECTED",
  validation_scope: "PER_ATTACHMENT",
  applicability: "CONDITIONAL",
  documents: [
    {
      document_id: "d-1",
      state: "ATTACHED",
      current_version_no: 1,
      current_version_decision: null,
    },
  ],
  decisions: [],
};

function setup({
  item = ITEM,
  validation = VALIDATION,
  corrections = [],
}: {
  item?: typeof ITEM;
  validation?: typeof VALIDATION;
  corrections?: unknown[];
} = {}) {
  getValidationMock.mockResolvedValue(validation);
  listDocumentsMock.mockResolvedValue({
    documents: [DOC],
    total: 1,
    limit: 50,
    offset: 0,
  });
  listCorrectionsMock.mockResolvedValue(corrections);
  const onChanged = vi.fn();
  render(
    <ItemValidationPanel
      period="2026-05"
      item={item as never}
      onChanged={onChanged}
    />,
  );
  return onChanged;
}

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("ItemValidationPanel", () => {
  it("exibe evidências aguardando validação e aceita por anexo", async () => {
    const onChanged = setup();
    decideDocMock.mockResolvedValue({});

    await waitFor(() => screen.getByText("extrato.pdf · v1"));
    expect(screen.getByText("Aguardando validação")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Aceitar" }));
    await waitFor(() =>
      expect(decideDocMock).toHaveBeenCalledWith(
        "2026-05",
        "d-1",
        { decision: "ACCEPTED" },
      ),
    );
    await waitFor(() => expect(onChanged).toHaveBeenCalled());
  });

  it("rejeita por anexo exigindo motivo estruturado", async () => {
    setup();
    decideDocMock.mockResolvedValue({});

    await waitFor(() => screen.getByText("extrato.pdf · v1"));
    fireEvent.click(screen.getByRole("button", { name: "Rejeitar" }));

    const confirm = screen.getByRole("button", {
      name: "Confirmar rejeição",
    });
    expect(confirm).toHaveProperty("disabled", true);

    fireEvent.change(screen.getByLabelText(/Motivo da rejeição/), {
      target: { value: "ILLEGIBLE" },
    });
    expect(confirm).toHaveProperty("disabled", false);
    fireEvent.click(confirm);

    await waitFor(() =>
      expect(decideDocMock).toHaveBeenCalledWith("2026-05", "d-1", {
        decision: "REJECTED",
        reason_code: "ILLEGIBLE",
      }),
    );
  });

  it("motivo «Outro» exige comentário antes de confirmar", async () => {
    setup();

    await waitFor(() => screen.getByText("extrato.pdf · v1"));
    fireEvent.click(screen.getByRole("button", { name: "Rejeitar" }));
    fireEvent.change(screen.getByLabelText(/Motivo da rejeição/), {
      target: { value: "OTHER" },
    });

    const confirm = screen.getByRole("button", {
      name: "Confirmar rejeição",
    });
    expect(confirm).toHaveProperty("disabled", true);

    fireEvent.change(screen.getByLabelText(/Comentário/), {
      target: { value: "Arquivo corrompido" },
    });
    fireEvent.click(confirm);

    await waitFor(() =>
      expect(decideDocMock).toHaveBeenCalledWith("2026-05", "d-1", {
        decision: "REJECTED",
        reason_code: "OTHER",
        comment: "Arquivo corrompido",
      }),
    );
  });

  it("conjunto (WHOLE_SET) decide a composição inteira", async () => {
    setup({
      item: { ...ITEM, validation_scope: "WHOLE_SET" },
      validation: { ...VALIDATION, validation_scope: "WHOLE_SET" },
    });
    decideSetMock.mockResolvedValue({});

    await waitFor(() => screen.getByText("extrato.pdf · v1"));
    expect(
      screen.queryByRole("button", { name: "Aceitar" }),
    ).toBeNull();

    fireEvent.click(
      screen.getByRole("button", { name: "Aceitar conjunto" }),
    );
    await waitFor(() =>
      expect(decideSetMock).toHaveBeenCalledWith("2026-05", "CK-E-01", {
        decision: "ACCEPTED",
      }),
    );
  });

  it("oferece reversão de rejeição com justificativa", async () => {
    setup({
      validation: {
        ...VALIDATION,
        documents: [
          {
            document_id: "d-1",
            state: "ATTACHED",
            current_version_no: 1,
            current_version_decision: {
              decision_id: "dec-9",
              decision: "REJECTED",
              result_state: null,
              reason_code: "ILLEGIBLE",
              comment: null,
              decided_by: "u-1",
              created_at: "2026-05-02T11:00:00Z",
            },
          },
        ],
      },
    });
    reverseMock.mockResolvedValue({});

    await waitFor(() =>
      screen.getByRole("button", { name: "Reverter rejeição" }),
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Reverter rejeição" }),
    );

    fireEvent.change(screen.getByLabelText(/Justificativa da reversão/), {
      target: { value: "Erro meu, arquivo legível" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Confirmar reversão" }),
    );

    await waitFor(() =>
      expect(reverseMock).toHaveBeenCalledWith("2026-05", "dec-9", {
        result_state: "UNDER_REVIEW",
        justification: "Erro meu, arquivo legível",
      }),
    );
  });

  it("marca item condicional como N/A com justificativa", async () => {
    setup();
    markNaMock.mockResolvedValue({});

    await waitFor(() => screen.getByText("extrato.pdf · v1"));
    fireEvent.click(
      screen.getByRole("button", {
        name: "Marcar como não aplicável",
      }),
    );
    fireEvent.change(screen.getByLabelText(/Justificativa/), {
      target: { value: "Filial sem movimento" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Confirmar" }));

    await waitFor(() =>
      expect(markNaMock).toHaveBeenCalledWith(
        "2026-05",
        "CK-E-01",
        "Filial sem movimento",
      ),
    );
  });

  it("não oferece N/A para item obrigatório", async () => {
    setup({ item: { ...ITEM, applicability: "REQUIRED" } });

    await waitFor(() => screen.getByText("extrato.pdf · v1"));
    expect(
      screen.queryByRole("button", {
        name: "Marcar como não aplicável",
      }),
    ).toBeNull();
  });

  it("exibe erro tipado do backend sem duplicar regra", async () => {
    getValidationMock.mockResolvedValue(VALIDATION);
    listDocumentsMock.mockResolvedValue({
      documents: [DOC],
      total: 1,
      limit: 50,
      offset: 0,
    });
    listCorrectionsMock.mockResolvedValue([]);
    decideDocMock.mockRejectedValue(
      new ApiError(403, "Sem autorização", "forbidden"),
    );

    render(
      <ItemValidationPanel
        period="2026-05"
        item={ITEM as never}
        onChanged={vi.fn()}
      />,
    );

    await waitFor(() => screen.getByText("extrato.pdf · v1"));
    fireEvent.click(screen.getByRole("button", { name: "Aceitar" }));

    await waitFor(() =>
      screen.getByText(/não tem autorização para esta decisão/),
    );
  });

  it("lista correções pendentes e revisa com aprovação", async () => {
    setup({
      corrections: [
        {
          correction_id: "corr-1",
          snapshot_item_id: "s-1",
          item_key: "CK-E-01",
          item_revision: 1,
          changes: { requirement_notes: "nota nova" },
          justification: "Ajuste",
          status: "PENDING",
          requested_by: "u-2",
          requested_at: "2026-05-02T12:00:00Z",
          reviewed_by: null,
          reviewed_at: null,
          review_reason: null,
        },
      ],
    });
    reviewCorrectionMock.mockResolvedValue({});

    await waitFor(() => screen.getByText("Correções estruturais"));
    fireEvent.click(screen.getByRole("button", { name: "Revisar" }));
    fireEvent.click(screen.getByRole("button", { name: "Aprovar" }));

    await waitFor(() =>
      expect(reviewCorrectionMock).toHaveBeenCalledWith(
        "2026-05",
        "CK-E-01",
        "corr-1",
        { approve: true },
      ),
    );
  });

  it("solicita correção estrutural com campo, valor e justificativa", async () => {
    setup();
    requestCorrectionMock.mockResolvedValue({});

    await waitFor(() => screen.getByText("extrato.pdf · v1"));
    fireEvent.click(
      screen.getByRole("button", { name: "Solicitar correção" }),
    );
    fireEvent.change(screen.getByLabelText(/Campo a corrigir/), {
      target: { value: "requirement_notes" },
    });
    fireEvent.change(screen.getByLabelText(/Novo valor/), {
      target: { value: "exigir PDF assinado" },
    });
    fireEvent.change(screen.getByLabelText(/Justificativa/), {
      target: { value: "Nota do template desatualizada" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Enviar correção" }),
    );

    await waitFor(() =>
      expect(requestCorrectionMock).toHaveBeenCalledWith(
        "2026-05",
        "CK-E-01",
        {
          changes: { requirement_notes: "exigir PDF assinado" },
          justification: "Nota do template desatualizada",
        },
      ),
    );
  });
});
