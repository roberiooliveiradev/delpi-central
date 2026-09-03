import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import * as api from "./data/api/invoiceIssuanceApi";
import * as meApi from "./data/api/meApi";

vi.mock("./data/api/invoiceIssuanceApi");
vi.mock("./data/api/meApi");
vi.mock("@delpi/plugin-ui/index", async () => await import("./test/pluginUiMock"));

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  window.history.replaceState({}, "", "/");
});

describe("App deep link", () => {
  it("abre o detalhe quando a URL traz requestId", async () => {
    window.history.replaceState(
      {},
      "",
      "/apps/invoice-issuance/filial-01?requestId=req-deep",
    );
    vi.mocked(meApi.fetchMeProfile).mockResolvedValue({
      id: "u1",
      name: "User",
      email: "u@delpi.com.br",
      permissions: ["invoice-issuance.view", "invoice-issuance.view.filial-01"],
    });
    vi.mocked(api.getRequest).mockResolvedValue({
      request: {
        id: "req-deep",
        branch_code: "01",
        party_type: "customer",
        party_code: "000001",
        party_store: "01",
        party_name: "ACME",
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
          purchase_order: true,
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
            stock_write_off: false,
          },
        ],
        attachments: [],
      },
      history: [
        {
          id: "h1",
          event_type: "created",
          actor_name: "User",
          from_status: null,
          to_status: "pending",
          justification: null,
          created_at: "2026-08-14T10:00:00+00:00",
        },
      ],
      allowed_actions: ["view"],
    });

    render(
      <App pathname="/apps/invoice-issuance/filial-01" getAccessToken={() => "t"} />,
    );

    await waitFor(() => expect(screen.getByTestId("detail-page")).toBeTruthy());
    expect(screen.getByText("Solicitação criada")).toBeTruthy();
    expect(api.getRequest).toHaveBeenCalledWith("req-deep");
    expect(screen.getByTestId("deprecation-banner")).toBeTruthy();
    expect(
      screen.getByRole("link", { name: "Abrir Minhas Solicitações" }).getAttribute("href"),
    ).toBe("/apps/my-requests");
    expect(
      screen.getByRole("link", { name: "Nova solicitação de NF" }).getAttribute("href"),
    ).toBe("/apps/my-requests/new?type=invoice-issuance");
  });
});
