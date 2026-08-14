import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { IssuancePermissionsContext } from "../../application/issuancePermissionsContextValue";
import { resolveIssuancePermissions } from "../../domain/permissions";
import type { RequestDetail } from "../../domain/types";
import { RequestDetailPage } from "./RequestDetailPage";
import * as api from "../../data/api/invoiceIssuanceApi";

vi.mock("../../data/api/invoiceIssuanceApi");
vi.mock("@delpi/plugin-ui/index", async () => await import("../../test/pluginUiMock"));

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

function detail(overrides: Partial<RequestDetail["request"]> = {}): RequestDetail {
  return {
    request: {
      id: "req-1",
      branch_code: "01",
      party_type: "customer",
      party_code: "000256",
      party_store: "01",
      party_name: "TRACTIAN TECNOLOGIA LTDA",
      tax_id: "35755699000184",
      invoice_type: "sale",
      invoice_type_other: null,
      freight_mode: "cif",
      carrier_code: "000001",
      carrier_name: "JADLOG",
      weight_kg: 1,
      volume_count: 1,
      purchase_order_number: null,
      observation: "Precisa emitir hoje",
      status: "pending",
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
      created_by_name: "Maria da Silva",
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
          quantity: 2,
          unit_price: 10,
          stock_write_off: true,
          sales_order: "000111",
          sales_order_item: "01",
        },
      ],
      attachments: [],
      ...overrides,
    },
    history: [
      {
        id: "h1",
        event_type: "created",
        actor_name: "Maria da Silva",
        from_status: null,
        to_status: "pending",
        justification: null,
        created_at: "2026-08-14T10:00:00+00:00",
      },
    ],
    allowed_actions: ["view", "start"],
  };
}

function renderPage(payload: RequestDetail = detail()) {
  vi.mocked(api.getRequest).mockResolvedValue(payload);
  const flags = resolveIssuancePermissions([
    "invoice-issuance.view",
    "invoice-issuance.process",
  ]);
  return render(
    <IssuancePermissionsContext.Provider
      value={{
        ...flags,
        loading: false,
        error: null,
        userId: "u2",
        userName: "Ana",
        refresh: () => undefined,
      }}
    >
      <RequestDetailPage requestId="req-1" onBack={() => undefined} onEdit={() => undefined} />
    </IssuancePermissionsContext.Provider>,
  );
}

describe("RequestDetailPage", () => {
  it("mostra ficha com código e loja do cliente para lançar no Protheus", async () => {
    renderPage();

    await waitFor(() => expect(screen.getByTestId("issuance-sheet")).toBeTruthy());
    expect(screen.getByText("Código")).toBeTruthy();
    expect(screen.getAllByText("000256").length).toBeGreaterThan(0);
    expect(screen.getByText("Loja")).toBeTruthy();
    expect(screen.getByText("Cliente")).toBeTruthy();
    expect(screen.getByText("35.755.699/0001-84")).toBeTruthy();
    expect(screen.queryByText("Destinatário e transporte")).toBeNull();
    expect(screen.queryByText("Destinatário identificado ou cadastrado.")).toBeNull();
    expect(screen.getAllByText("000111").length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Iniciar atendimento" })).toBeTruthy();
  });

  it("mostra contato da transportadora na ficha", async () => {
    renderPage(
      detail({
        carrier_legal_name: "Mir Transp. Logistica LTDA",
        carrier_tax_id: "03565095000189",
        carrier_address: "Rodovia BR-470, 8220, Canta Galo, Rio do Sul-SC, CEP 89163-020",
        carrier_phone: "(47) 3522-6972",
      }),
    );
    await waitFor(() => expect(screen.getByTestId("issuance-sheet")).toBeTruthy());
    expect(screen.getByText("Razão social")).toBeTruthy();
    expect(screen.getByText("Mir Transp. Logistica LTDA")).toBeTruthy();
    expect(screen.getByText("(47) 3522-6972")).toBeTruthy();
    expect(screen.getByText(/Rio do Sul-SC/)).toBeTruthy();
  });
});
