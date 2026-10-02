import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactElement } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { RequestFormPage } from "./RequestFormPage";
import * as api from "../../data/api/invoicePostingApi";
import { ApiError } from "../../data/api/httpClient";

vi.mock("../../data/api/invoicePostingApi");
vi.mock("@delpi/plugin-ui/index", () => ({
  FilePreviewModal: ({
    open,
    source,
  }: {
    open?: boolean;
    source?: (() => Promise<unknown>) | null;
  }) => {
    if (open && source) void source();
    return null;
  },
}));

function renderCreate(ui: ReactElement) {
  const view = render(ui);
  const manual = screen.queryByRole("button", { name: /Inclusão manual/ });
  if (manual) fireEvent.click(manual);
  return view;
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("RequestFormPage", () => {
  it("valida documento e mostra normalização", () => {
    renderCreate(
      <RequestFormPage
        mode="create"
        onCancel={() => undefined}
        onSuccess={() => undefined}
      />,
    );
    fireEvent.change(screen.getByLabelText("Número da nota"), {
      target: { value: "123456" },
    });
    expect(screen.getByTestId("document-preview").textContent).toContain("000123456");
    expect(screen.getByTestId("document-preview").textContent).toMatch(
      /Apresentação: 000123456 · chave: 000123456/,
    );
  });

  it("pré-preenche recebimento com data/hora atual", () => {
    renderCreate(
      <RequestFormPage
        mode="create"
        onCancel={() => undefined}
        onSuccess={() => undefined}
      />,
    );
    const received = screen.getByLabelText("Recebimento físico") as HTMLInputElement;
    expect(received.value).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/);
  });

  it("exige série no cadastro", async () => {
    vi.mocked(api.searchSuppliers).mockResolvedValue([
      {
        supplier_code: "000001",
        supplier_store: "01",
        supplier_name: "Alpha",
        supplier_short_name: "A",
        tax_id: "123",
        state: "SC",
        blocked: false,
      },
    ]);
    renderCreate(
      <RequestFormPage mode="create" onCancel={() => undefined} onSuccess={() => undefined} />,
    );
    fireEvent.change(screen.getByLabelText("Número da nota"), {
      target: { value: "123" },
    });
    fireEvent.change(screen.getByLabelText("Data de emissão"), {
      target: { value: "2026-07-01" },
    });
    fireEvent.change(screen.getByLabelText("Valor"), { target: { value: "10" } });
    fireEvent.change(screen.getByPlaceholderText(/mín\. 2 caracteres/i), {
      target: { value: "Alpha" },
    });
    await waitFor(() => expect(screen.getByText(/000001\/01/)).toBeTruthy());
    fireEvent.click(screen.getByText(/000001\/01/));
    fireEvent.click(screen.getByTestId("btn-submit-request"));
    expect(screen.getByText(/Informe a série/i)).toBeTruthy();
    expect(api.createRequest).not.toHaveBeenCalled();
  });

  it("exige o tipo da nota no cadastro", async () => {
    vi.mocked(api.searchSuppliers).mockResolvedValue([
      {
        supplier_code: "000001",
        supplier_store: "01",
        supplier_name: "Alpha",
        supplier_short_name: "A",
        tax_id: "123",
        state: "SC",
        blocked: false,
      },
    ]);
    renderCreate(
      <RequestFormPage mode="create" onCancel={() => undefined} onSuccess={() => undefined} />,
    );
    fireEvent.change(screen.getByLabelText("Número da nota"), {
      target: { value: "123" },
    });
    fireEvent.change(screen.getByLabelText("Série"), { target: { value: "1" } });
    fireEvent.change(screen.getByLabelText("Data de emissão"), {
      target: { value: "2026-07-01" },
    });
    fireEvent.change(screen.getByLabelText("Valor"), { target: { value: "10" } });
    fireEvent.change(screen.getByPlaceholderText(/mín\. 2 caracteres/i), {
      target: { value: "Alpha" },
    });
    await waitFor(() => expect(screen.getByText(/000001\/01/)).toBeTruthy());
    fireEvent.click(screen.getByText(/000001\/01/));
    fireEvent.click(screen.getByTestId("btn-submit-request"));
    expect(screen.getByText(/NF-e ou NFS-e/i)).toBeTruthy();
    expect(api.createRequest).not.toHaveBeenCalled();
  });

  it("cadastra NFS-e sem série e mantém a série obrigatória na NF-e", async () => {
    vi.mocked(api.searchSuppliers).mockResolvedValue([
      {
        supplier_code: "000001",
        supplier_store: "01",
        supplier_name: "Alpha",
        supplier_short_name: "A",
        tax_id: "123",
        state: "SC",
        blocked: false,
      },
    ]);
    vi.mocked(api.createRequest).mockResolvedValue({ id: "nfse-1" } as never);
    renderCreate(
      <RequestFormPage mode="create" onCancel={() => undefined} onSuccess={() => undefined} />,
    );

    fireEvent.change(screen.getByLabelText("Número da nota"), { target: { value: "55" } });
    fireEvent.change(screen.getByLabelText("Tipo da nota"), { target: { value: "nfe" } });
    fireEvent.change(screen.getByLabelText("Data de emissão"), { target: { value: "2026-07-01" } });
    fireEvent.change(screen.getByLabelText("Valor"), { target: { value: "10" } });
    fireEvent.change(screen.getByPlaceholderText(/mín\. 2 caracteres/i), {
      target: { value: "Alpha" },
    });
    await waitFor(() => expect(screen.getByText(/000001\/01/)).toBeTruthy());
    fireEvent.click(screen.getByText(/000001\/01/));
    fireEvent.click(screen.getByTestId("btn-submit-request"));
    expect(screen.getByText(/Informe a série/i)).toBeTruthy();
    expect(api.createRequest).not.toHaveBeenCalled();

    fireEvent.change(screen.getByLabelText("Tipo da nota"), { target: { value: "nfse" } });
    expect(screen.getByLabelText("Série").getAttribute("aria-required")).toBe("false");
    fireEvent.click(screen.getByTestId("btn-submit-request"));
    await waitFor(() => expect(api.createRequest).toHaveBeenCalled());
    expect(api.createRequest).toHaveBeenCalledWith(
      expect.objectContaining({ fiscal_model: "nfse", series: "", document: "55" }),
    );
  });

  it("Enter avança o foco como Tab", () => {
    renderCreate(
      <RequestFormPage mode="create" onCancel={() => undefined} onSuccess={() => undefined} />,
    );
    const documentInput = screen.getByLabelText("Número da nota");
    documentInput.focus();
    fireEvent.keyDown(documentInput, { key: "Enter", bubbles: true });
    expect(document.activeElement).toBe(screen.getByLabelText("Série"));
  });

  it("cadastra com payload correto", async () => {
    vi.mocked(api.searchSuppliers).mockResolvedValue([
      {
        supplier_code: "000001",
        supplier_store: "01",
        supplier_name: "Alpha",
        supplier_short_name: "A",
        tax_id: "123",
        state: "SC",
        blocked: false,
      },
    ]);
    vi.mocked(api.createRequest).mockResolvedValue({
      id: "new-1",
    } as never);
    const onSuccess = vi.fn();
    renderCreate(
      <RequestFormPage mode="create" onCancel={() => undefined} onSuccess={onSuccess} />,
    );

    fireEvent.change(screen.getByLabelText("Número da nota"), {
      target: { value: "123" },
    });
    fireEvent.change(screen.getByLabelText("Série"), { target: { value: "1" } });
    fireEvent.change(screen.getByLabelText("Tipo da nota"), { target: { value: "nfe" } });
    fireEvent.change(screen.getByLabelText("Data de emissão"), {
      target: { value: "2026-07-01" },
    });
    fireEvent.change(screen.getByLabelText("Valor"), { target: { value: "10.5" } });
    fireEvent.change(screen.getByLabelText("Recebimento físico"), {
      target: { value: "2026-07-02T10:00" },
    });
    fireEvent.change(screen.getByPlaceholderText(/mín\. 2 caracteres/i), {
      target: { value: "Alpha" },
    });
    await waitFor(() => {
      expect(screen.getByText(/000001\/01/)).toBeTruthy();
    });
    fireEvent.click(screen.getByText(/000001\/01/));
    fireEvent.click(screen.getByTestId("btn-submit-request"));

    await waitFor(() => expect(api.createRequest).toHaveBeenCalled());
    expect(api.createRequest).toHaveBeenCalledWith(
      expect.objectContaining({
        branch: "01",
        document: "123",
        series: "1",
        fiscal_model: "nfe",
        supplier_code: "000001",
        supplier_store: "01",
        amount: 10.5,
      }),
    );
    expect(onSuccess).toHaveBeenCalledWith("new-1");
  });

  it("exibe duplicidade da API", async () => {
    vi.mocked(api.searchSuppliers).mockResolvedValue([
      {
        supplier_code: "000001",
        supplier_store: "01",
        supplier_name: "Alpha",
        supplier_short_name: null,
        tax_id: null,
        state: null,
        blocked: false,
      },
    ]);
    vi.mocked(api.createRequest).mockRejectedValue(
      new ApiError("Já existe solicitação ativa com a mesma chave fiscal.", {
        status: 409,
        code: "invoice_posting_request.duplicate",
        meta: { existing_request_id: "dup-9" },
      }),
    );
    renderCreate(
      <RequestFormPage
        mode="create"
        onCancel={() => undefined}
        onSuccess={() => undefined}
      />,
    );
    fireEvent.change(screen.getByLabelText("Número da nota"), {
      target: { value: "1" },
    });
    fireEvent.change(screen.getByLabelText("Série"), { target: { value: "1" } });
    fireEvent.change(screen.getByLabelText("Tipo da nota"), { target: { value: "nfe" } });
    fireEvent.change(screen.getByLabelText("Data de emissão"), {
      target: { value: "2026-07-01" },
    });
    fireEvent.change(screen.getByLabelText("Valor"), { target: { value: "1" } });
    fireEvent.change(screen.getByLabelText("Recebimento físico"), {
      target: { value: "2026-07-02T10:00" },
    });
    fireEvent.change(screen.getByPlaceholderText(/mín\. 2 caracteres/i), {
      target: { value: "Alpha" },
    });
    await waitFor(() => expect(screen.getByText(/000001\/01/)).toBeTruthy());
    fireEvent.click(screen.getByText(/000001\/01/));
    fireEvent.click(screen.getByTestId("btn-submit-request"));
    await waitFor(() => {
      expect(screen.getByTestId("form-submit-error").textContent).toContain("dup-9");
    });
  });

  it("não permite selecionar fornecedor bloqueado", async () => {
    vi.mocked(api.searchSuppliers).mockResolvedValue([
      {
        supplier_code: "000002",
        supplier_store: "01",
        supplier_name: "Bloqueado SA",
        supplier_short_name: null,
        tax_id: null,
        state: null,
        blocked: true,
      },
    ]);
    renderCreate(
      <RequestFormPage
        mode="create"
        onCancel={() => undefined}
        onSuccess={() => undefined}
      />,
    );
    fireEvent.change(screen.getByPlaceholderText(/mín\. 2 caracteres/i), {
      target: { value: "Bloq" },
    });
    await waitFor(() => expect(screen.getByText(/Bloqueado SA/)).toBeTruthy());
    const option = screen.getByText(/Bloqueado SA/).closest("button");
    expect(option).toBeTruthy();
    expect((option as HTMLButtonElement).disabled).toBe(true);
  });

  it("inclusão manual não consulta notas fiscais", () => {
    renderCreate(
      <RequestFormPage mode="create" onCancel={() => undefined} onSuccess={() => undefined} />,
    );
    expect(api.searchReceivedInvoices).not.toHaveBeenCalled();
    expect(screen.getByLabelText("Número da nota")).toBeTruthy();
  });

  it("busca a NF-e só ao enviar o filtro e exige DANFE para avançar", async () => {
    vi.mocked(api.searchReceivedInvoices).mockResolvedValue({
      items: [
        {
          documentId: "aabbccddeeff001122334455",
          accessKey: "1".repeat(44),
          invoiceNumber: "22844",
          series: "1",
          issuerName: "Fornecedor",
          issuerCnpj: null,
          branchCode: "01",
          emissionAt: "2026-09-30T21:40:44Z",
          amount: "108.00",
          amountFormatted: "R$ 108,00",
          danfeAvailable: false,
        },
      ],
      pagination: { page: 1, pageSize: 25, totalItems: 1, hasNext: false, hasPrevious: false },
    });
    render(
      <RequestFormPage mode="create" onCancel={() => undefined} onSuccess={() => undefined} />,
    );
    fireEvent.click(screen.getByTestId("btn-select-nfe"));
    fireEvent.change(screen.getByLabelText("Número da NF"), { target: { value: "22844" } });
    expect(api.searchReceivedInvoices).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Buscar" }));
    await waitFor(() =>
      expect(api.searchReceivedInvoices).toHaveBeenCalledWith({
        invoiceNumber: "22844",
        supplierCnpj: undefined,
        page: 1,
      }),
    );
    expect((screen.getByRole("button", { name: "Avançar" }) as HTMLButtonElement).disabled).toBe(true);
  });

  it("ao avançar preenche a nota e anexa a chave no cadastro", async () => {
    const accessKey = "2".repeat(44);
    vi.mocked(api.searchReceivedInvoices).mockResolvedValue({
      items: [
        {
          documentId: "aabbccddeeff001122334455",
          accessKey,
          invoiceNumber: "22844",
          series: "1",
          issuerName: "Fornecedor",
          issuerCnpj: "12345678000199",
          emissionAt: "2026-09-30",
          amount: "108.00",
          amountFormatted: "R$ 108,00",
          danfeAvailable: true,
          branchCode: "02",
        },
      ],
      pagination: { page: 1, pageSize: 25, totalItems: 1, hasNext: false, hasPrevious: false },
    });
    vi.mocked(api.searchSuppliers).mockResolvedValue([
      {
        supplier_code: "000010",
        supplier_store: "01",
        supplier_name: "Fornecedor",
        supplier_short_name: null,
        tax_id: "12345678000199",
        state: "SC",
        blocked: false,
      },
    ]);
    vi.mocked(api.createRequest).mockResolvedValue({ id: "nfe-1" } as never);
    render(
      <RequestFormPage mode="create" onCancel={() => undefined} onSuccess={() => undefined} />,
    );
    expect(screen.getByText(/visualizar o DANFE antes de avançar/i)).toBeTruthy();
    fireEvent.click(screen.getByTestId("btn-select-nfe"));
    fireEvent.change(screen.getByLabelText("CNPJ do fornecedor"), {
      target: { value: "12.345.678/0001-99" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Buscar" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Avançar" })).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: "Visualizar" }));
    await waitFor(() =>
      expect(api.fetchReceivedInvoicePreview).toHaveBeenCalledWith(
        "aabbccddeeff001122334455",
        accessKey,
        "02",
      ),
    );
    fireEvent.click(screen.getByRole("button", { name: "Avançar" }));
    await waitFor(() => expect(screen.getByDisplayValue("22844")).toBeTruthy());
    expect(screen.getByTestId("danfe-attach-notice").textContent).toMatch(/anexado/i);
    fireEvent.change(screen.getByLabelText("Recebimento físico"), {
      target: { value: "2026-10-01T09:30" },
    });
    fireEvent.click(screen.getByTestId("btn-submit-request"));
    await waitFor(() => expect(api.createRequest).toHaveBeenCalled());
    expect(api.createRequest).toHaveBeenCalledWith(
      expect.objectContaining({
        source: "received_nfe",
        document_id: "aabbccddeeff001122334455",
        access_key: accessKey,
        source_branch: "02",
        branch: "02",
        fiscal_model: "nfe",
        document: "22844",
        supplier_code: "000010",
      }),
    );
    expect((screen.getByLabelText("Filial") as HTMLSelectElement).value).toBe("02");
  });

  it("não avança quando a nota é de outra filial que a rota travada", async () => {
    vi.mocked(api.searchReceivedInvoices).mockResolvedValue({
      items: [
        {
          documentId: "aabbccddeeff001122334455",
          accessKey: "2".repeat(44),
          invoiceNumber: "132004",
          series: "1",
          issuerName: "Fornecedor",
          issuerCnpj: null,
          emissionAt: "2026-09-30",
          amount: "10.00",
          amountFormatted: "R$ 10,00",
          danfeAvailable: true,
          branchCode: "02",
        },
      ],
      pagination: { page: 1, pageSize: 25, totalItems: 1, hasNext: false, hasPrevious: false },
    });
    render(
      <RequestFormPage
        mode="create"
        lockedBranch="01"
        onCancel={() => undefined}
        onSuccess={() => undefined}
      />,
    );
    fireEvent.click(screen.getByTestId("btn-select-nfe"));
    fireEvent.change(screen.getByLabelText("Número da NF"), { target: { value: "132004" } });
    fireEvent.click(screen.getByRole("button", { name: "Buscar" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Avançar" })).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: "Avançar" }));
    expect((await screen.findByRole("alert")).textContent).toMatch(/filial 02/);
    expect(screen.queryByLabelText("Número da nota")).toBeNull();
    expect(api.createRequest).not.toHaveBeenCalled();
  });
});
