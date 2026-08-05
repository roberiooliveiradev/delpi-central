import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { ReactNode } from "react";

vi.mock("@delpi/plugin-ui/index", () => ({
  sectionCardPacBemClasses: () => ({}),
  createDashboardSectionCard:
    () =>
    function SectionCard({ title, children }: { title: string; children: ReactNode }) {
      return (
        <section data-testid={`section-${title}`}>
          <h2>{title}</h2>
          {children}
        </section>
      );
    },
  createDashboardLoadingActivityCard:
    () =>
    function LoadingActivityCard({ title }: { title: string }) {
      return <div>{title}</div>;
    },
  createDashboardStateBox:
    () =>
    function StateBox({ children }: { children: ReactNode }) {
      return <div role="alert">{children}</div>;
    },
}));

import { CapexInvestmentAttachmentsPanel } from "../components/CapexInvestmentAttachmentsPanel";
import * as budgetApi from "../api/budgetPlanningApi";
import { HttpRequestError } from "../api/httpClient";

vi.mock("../api/budgetPlanningApi");

const sample = {
  id: "att-1",
  investment_id: "inv-1",
  attachment_type: "quotation",
  display_name: "Orçamento A",
  description: "PDF fornecedor",
  original_filename: "orc.pdf",
  mime_type: "application/pdf",
  file_size: 2048,
  created_by: "user-1",
  created_at: "2026-08-05T12:00:00Z",
  is_active: true,
};

beforeEach(() => {
  vi.mocked(budgetApi.listCapexInvestmentAttachments).mockResolvedValue([sample]);
  vi.mocked(budgetApi.uploadCapexInvestmentAttachment).mockResolvedValue({
    ...sample,
    id: "att-2",
    display_name: "Novo",
  });
  vi.mocked(budgetApi.downloadCapexAttachment).mockResolvedValue(new Blob(["pdf"]));
  vi.mocked(budgetApi.archiveCapexAttachment).mockResolvedValue({
    ...sample,
    is_active: false,
  });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("CapexInvestmentAttachmentsPanel", () => {
  it("exibe orientação antes da criação do rascunho", () => {
    render(<CapexInvestmentAttachmentsPanel investmentId={null} />);
    expect(screen.getByText(/Salve o rascunho para adicionar documentos/i)).toBeTruthy();
    expect(budgetApi.listCapexInvestmentAttachments).not.toHaveBeenCalled();
  });

  it("carrega a lista de anexos", async () => {
    render(<CapexInvestmentAttachmentsPanel investmentId="inv-1" />);
    await screen.findByText("Orçamento A");
    expect(budgetApi.listCapexInvestmentAttachments).toHaveBeenCalledWith(
      "inv-1",
      expect.any(AbortSignal),
    );
    expect(screen.getByText("Orçamento A")).toBeTruthy();
    expect(screen.queryByText(/storage_key/i)).toBeNull();
    expect(document.body.textContent).not.toMatch(/storage_key/i);
  });

  it("lista vazia", async () => {
    vi.mocked(budgetApi.listCapexInvestmentAttachments).mockResolvedValue([]);
    render(<CapexInvestmentAttachmentsPanel investmentId="inv-1" />);
    await screen.findByTestId("capex-attachments-empty");
    expect(
      screen.getByText(/Nenhum documento foi anexado a este investimento/i),
    ).toBeTruthy();
  });

  it("valida nome e tipo antes do envio", async () => {
    render(<CapexInvestmentAttachmentsPanel investmentId="inv-1" />);
    await screen.findByTestId("capex-attachment-upload-form");
    const form = screen.getByTestId("capex-attachment-upload-form");
    const file = new File([new Uint8Array([1, 2, 3])], "a.pdf", { type: "application/pdf" });
    fireEvent.change(within(form).getByLabelText("Arquivo"), { target: { files: [file] } });
    fireEvent.change(within(form).getByLabelText("Nome de exibição"), {
      target: { value: "" },
    });
    fireEvent.click(within(form).getByRole("button", { name: /Enviar anexo/i }));
    await screen.findByText(/nome de exibição/i);
    expect(budgetApi.uploadCapexInvestmentAttachment).not.toHaveBeenCalled();
  });

  it("rejeita arquivo acima do limite no cliente", async () => {
    render(<CapexInvestmentAttachmentsPanel investmentId="inv-1" />);
    await screen.findByTestId("capex-attachment-upload-form");
    const form = screen.getByTestId("capex-attachment-upload-form");
    const huge = new File([new Uint8Array(26 * 1024 * 1024)], "big.pdf", {
      type: "application/pdf",
    });
    fireEvent.change(within(form).getByLabelText("Arquivo"), { target: { files: [huge] } });
    fireEvent.change(within(form).getByLabelText("Tipo"), {
      target: { value: "other" },
    });
    fireEvent.click(within(form).getByRole("button", { name: /Enviar anexo/i }));
    await screen.findByText(/25 MB/i);
    expect(budgetApi.uploadCapexInvestmentAttachment).not.toHaveBeenCalled();
  });

  it("faz upload multipart com progresso e atualiza a lista", async () => {
    let capturedProgress: ((r: number) => void) | undefined;
    vi.mocked(budgetApi.uploadCapexInvestmentAttachment).mockImplementation(
      async (_input, options) => {
        capturedProgress = options?.onProgress;
        capturedProgress?.(0.4);
        capturedProgress?.(1);
        return { ...sample, id: "att-new", display_name: "Novo anexo" };
      },
    );
    vi.mocked(budgetApi.listCapexInvestmentAttachments)
      .mockResolvedValueOnce([sample])
      .mockResolvedValueOnce([
        sample,
        { ...sample, id: "att-new", display_name: "Novo anexo" },
      ]);

    render(<CapexInvestmentAttachmentsPanel investmentId="inv-1" />);
    await screen.findByText("Orçamento A");
    const form = screen.getByTestId("capex-attachment-upload-form");
    const file = new File([new Uint8Array([1, 2, 3])], "prop.pdf", {
      type: "application/pdf",
    });
    fireEvent.change(within(form).getByLabelText("Arquivo"), { target: { files: [file] } });
    fireEvent.change(within(form).getByLabelText("Nome de exibição"), {
      target: { value: "Novo anexo" },
    });
    fireEvent.change(within(form).getByLabelText("Tipo"), {
      target: { value: "commercial_proposal" },
    });
    fireEvent.click(within(form).getByRole("button", { name: /Enviar anexo/i }));

    await waitFor(() => {
      expect(budgetApi.uploadCapexInvestmentAttachment).toHaveBeenCalledWith(
        expect.objectContaining({
          investmentId: "inv-1",
          attachmentType: "commercial_proposal",
          displayName: "Novo anexo",
          idempotencyKey: expect.any(String),
        }),
        expect.objectContaining({ onProgress: expect.any(Function) }),
      );
    });
    await screen.findByText(/Anexo enviado com sucesso/i);
    await screen.findByText("Novo anexo");
    expect(vi.mocked(budgetApi.listCapexInvestmentAttachments).mock.calls.length).toBeGreaterThanOrEqual(
      2,
    );
  });

  it("trata erro de MIME do backend", async () => {
    vi.mocked(budgetApi.uploadCapexInvestmentAttachment).mockRejectedValueOnce(
      new HttpRequestError("[budget_capex_attachment_mime_invalid] inválido", 422),
    );
    render(<CapexInvestmentAttachmentsPanel investmentId="inv-1" />);
    await screen.findByTestId("capex-attachment-upload-form");
    const form = screen.getByTestId("capex-attachment-upload-form");
    const file = new File([new Uint8Array([1])], "a.pdf", { type: "application/pdf" });
    fireEvent.change(within(form).getByLabelText("Arquivo"), { target: { files: [file] } });
    fireEvent.change(within(form).getByLabelText("Tipo"), { target: { value: "other" } });
    fireEvent.click(within(form).getByRole("button", { name: /Enviar anexo/i }));
    await screen.findByText(/MIME/i);
  });

  it("trata erro de extensão do backend", async () => {
    vi.mocked(budgetApi.uploadCapexInvestmentAttachment).mockRejectedValueOnce(
      new HttpRequestError("[budget_capex_attachment_extension_invalid] x", 422),
    );
    render(<CapexInvestmentAttachmentsPanel investmentId="inv-1" />);
    await screen.findByTestId("capex-attachment-upload-form");
    const form = screen.getByTestId("capex-attachment-upload-form");
    const file = new File([new Uint8Array([1])], "a.pdf", { type: "application/pdf" });
    fireEvent.change(within(form).getByLabelText("Arquivo"), { target: { files: [file] } });
    fireEvent.change(within(form).getByLabelText("Tipo"), { target: { value: "other" } });
    fireEvent.click(within(form).getByRole("button", { name: /Enviar anexo/i }));
    await screen.findByText(/extensão/i);
  });

  it("trata erro de tamanho do backend", async () => {
    vi.mocked(budgetApi.uploadCapexInvestmentAttachment).mockRejectedValueOnce(
      new HttpRequestError("[budget_capex_attachment_too_large] x", 422),
    );
    render(<CapexInvestmentAttachmentsPanel investmentId="inv-1" />);
    await screen.findByTestId("capex-attachment-upload-form");
    const form = screen.getByTestId("capex-attachment-upload-form");
    const file = new File([new Uint8Array([1])], "a.pdf", { type: "application/pdf" });
    fireEvent.change(within(form).getByLabelText("Arquivo"), { target: { files: [file] } });
    fireEvent.change(within(form).getByLabelText("Tipo"), { target: { value: "other" } });
    fireEvent.click(within(form).getByRole("button", { name: /Enviar anexo/i }));
    await screen.findByText(/25 MB/i);
  });

  it("download autenticado", async () => {
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
    render(<CapexInvestmentAttachmentsPanel investmentId="inv-1" />);
    await screen.findByText("Orçamento A");
    fireEvent.click(screen.getByRole("button", { name: /Baixar/i }));
    await waitFor(() => {
      expect(budgetApi.downloadCapexAttachment).toHaveBeenCalledWith("att-1");
    });
    clickSpy.mockRestore();
  });

  it("erro de download", async () => {
    vi.mocked(budgetApi.downloadCapexAttachment).mockRejectedValueOnce(
      new HttpRequestError("x", 404),
    );
    render(<CapexInvestmentAttachmentsPanel investmentId="inv-1" />);
    await screen.findByText("Orçamento A");
    fireEvent.click(screen.getByRole("button", { name: /Baixar/i }));
    await screen.findByText(/não encontrado|Recurso não encontrado/i);
  });

  it("confirma e arquiva anexo", async () => {
    vi.spyOn(window, "confirm").mockReturnValue(true);
    vi.mocked(budgetApi.listCapexInvestmentAttachments)
      .mockResolvedValueOnce([sample])
      .mockResolvedValueOnce([]);
    render(<CapexInvestmentAttachmentsPanel investmentId="inv-1" />);
    await screen.findByText("Orçamento A");
    fireEvent.click(screen.getByRole("button", { name: /Arquivar/i }));
    await waitFor(() => {
      expect(budgetApi.archiveCapexAttachment).toHaveBeenCalledWith("att-1");
    });
    await screen.findByText(/Anexo arquivado/i);
    await screen.findByTestId("capex-attachments-empty");
  });

  it("investimento arquivado fica somente leitura", async () => {
    render(<CapexInvestmentAttachmentsPanel investmentId="inv-1" readOnly />);
    await screen.findByText("Orçamento A");
    expect(screen.queryByTestId("capex-attachment-upload-form")).toBeNull();
    expect(screen.queryByRole("button", { name: /Arquivar/i })).toBeNull();
    expect(screen.getByRole("button", { name: /Baixar/i })).toBeTruthy();
  });

  it("trata 401 na listagem", async () => {
    vi.mocked(budgetApi.listCapexInvestmentAttachments).mockRejectedValueOnce(
      new HttpRequestError("unauthorized", 401),
    );
    render(<CapexInvestmentAttachmentsPanel investmentId="inv-1" />);
    await screen.findByText(/Sessão expirada/i);
  });

  it("trata 403 na listagem", async () => {
    vi.mocked(budgetApi.listCapexInvestmentAttachments).mockRejectedValueOnce(
      new HttpRequestError("forbidden", 403),
    );
    render(<CapexInvestmentAttachmentsPanel investmentId="inv-1" />);
    await screen.findByText(/Acesso negado/i);
  });
});
