import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { RequestFormPage } from "./RequestFormPage";
import * as api from "../../data/api/invoicePostingApi";
import { ApiError } from "../../data/api/httpClient";

vi.mock("../../data/api/invoicePostingApi");

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("RequestFormPage", () => {
  it("valida documento e mostra normalização", () => {
    render(
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
    render(
      <RequestFormPage mode="create" onCancel={() => undefined} onSuccess={onSuccess} />,
    );

    fireEvent.change(screen.getByLabelText("Número da nota"), {
      target: { value: "123" },
    });
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
        supplier_code: "000001",
        supplier_store: "01",
        amount: "10.5",
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
    render(
      <RequestFormPage
        mode="create"
        onCancel={() => undefined}
        onSuccess={() => undefined}
      />,
    );
    fireEvent.change(screen.getByLabelText("Número da nota"), {
      target: { value: "1" },
    });
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
    render(
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
});
