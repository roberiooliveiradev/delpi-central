import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { IssuanceWizardPage } from "./IssuanceWizardPage";
import { IssuancePermissionsContext } from "../../application/issuancePermissionsContextValue";
import { resolveIssuancePermissions } from "../../domain/permissions";
import type { IssuanceRequest } from "../../domain/types";
import type { ReactNode } from "react";

vi.mock("../../data/api/invoiceIssuanceApi");
vi.mock("@delpi/plugin-ui/index", async () => await import("../../test/pluginUiMock"));

function Wrapper({ children }: { children: ReactNode }) {
  return (
    <IssuancePermissionsContext.Provider
      value={{
        ...resolveIssuancePermissions(["invoice-issuance.create"], true),
        loading: false,
        error: null,
        userId: "u1",
        userName: "User",
        refresh: () => undefined,
      }}
    >
      {children}
    </IssuancePermissionsContext.Provider>
  );
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("IssuanceWizardPage", () => {
  it("não avança da etapa de destinatário sem seleção", () => {
    render(
      <Wrapper>
        <IssuanceWizardPage
          mode="create"
          lockedBranch="01"
          onCancel={() => undefined}
          onSuccess={() => undefined}
        />
      </Wrapper>,
    );
    const continueBtn = screen.getByText("Continuar");
    expect((continueBtn as HTMLButtonElement).disabled).toBe(true);
    fireEvent.click(screen.getByText("Cliente"));
    expect(screen.getByTestId("wizard-page")).toBeTruthy();
  });

  it("mostra as seis etapas", () => {
    render(
      <Wrapper>
        <IssuanceWizardPage
          mode="create"
          lockedBranch="01"
          onCancel={() => undefined}
          onSuccess={() => undefined}
        />
      </Wrapper>,
    );
    expect(screen.getByText("Destinatário")).toBeTruthy();
    expect(screen.getByLabelText("Etapas da solicitação").textContent).toMatch(
      /Destinatário.*Tipo de NF.*Itens/,
    );
    expect(screen.getByText("Conferência")).toBeTruthy();
  });
});

describe("wizard wait", () => {
  it("mantém título de nova solicitação", async () => {
    render(
      <Wrapper>
        <IssuanceWizardPage
          mode="create"
          lockedBranch="01"
          onCancel={() => undefined}
          onSuccess={() => undefined}
        />
      </Wrapper>,
    );
    await waitFor(() =>
      expect(screen.getByText(/Nova solicitação de emissão/)).toBeTruthy(),
    );
  });
});

function customerRequest(): IssuanceRequest {
  return {
    id: "req-1",
    branch_code: "01",
    party_type: "customer",
    party_code: "000001",
    party_store: "01",
    party_name: "ACME LTDA",
    tax_id: "12345678000199",
    invoice_type: "sale",
    invoice_type_other: null,
        freight_mode: "cif",
        carrier_code: null,
        carrier_name: null,
    weight_kg: 10,
    volume_count: 1,
    purchase_order_number: null,
    observation: null,
    status: "returned",
    return_reason: null,
    checklist: {
      recipient: true,
      item_codes: true,
      quantity_price: true,
      stock_write_off: true,
      invoice_type: true,
      freight_mode: true,
      weight_volumes: true,
    },
    created_by_user_id: "u1",
    created_by_name: "User",
    assignee_user_id: null,
    assignee_name: null,
    cancelled_at: null,
    cancelled_by_name: null,
    cancel_justification: null,
    issued_at: null,
    created_at: "2026-08-14T10:00:00+00:00",
    updated_at: "2026-08-14T10:00:00+00:00",
    items: [
      {
        product_code: "90260001",
        product_description: "Conector",
        quantity: 1,
        unit_price: 10,
        stock_write_off: true,
      },
    ],
    attachments: [],
  };
}

describe("wizard itens", () => {
  it("mostra origem do pedido de venda para cliente depois do tipo de NF", async () => {
    const api = await import("../../data/api/invoiceIssuanceApi");
    vi.mocked(api.listOpenSalesOrders).mockResolvedValue({
      orders: [],
      orders_count: 0,
      lines_count: 0,
    });
    vi.mocked(api.getWarehouse01Balance).mockResolvedValue({
      product_code: "90260001",
      branch_code: "01",
      warehouse: "01",
      quantity: 12,
    });
    render(
      <Wrapper>
        <IssuanceWizardPage
          mode="edit"
          lockedBranch="01"
          requestId="req-1"
          initial={customerRequest()}
          onCancel={() => undefined}
          onSuccess={() => undefined}
        />
      </Wrapper>,
    );
    fireEvent.click(screen.getByText("Continuar"));
    expect(screen.getByText("Tipo de nota fiscal")).toBeTruthy();
    fireEvent.click(screen.getByText("Continuar"));
    expect(screen.getByTestId("item-source-toggle")).toBeTruthy();
    expect(screen.getByText("Do pedido de venda")).toBeTruthy();
    await waitFor(() => expect(screen.getByTestId("open-sales-order-picker")).toBeTruthy());
    await waitFor(() =>
      expect(screen.getByText("Saldo no almoxarifado 01: 12,000")).toBeTruthy(),
    );
  });
});
