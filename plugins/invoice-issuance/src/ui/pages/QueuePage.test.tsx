import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { QueuePage } from "./QueuePage";
import { IssuancePermissionsContext } from "../../application/issuancePermissionsContextValue";
import { resolveIssuancePermissions } from "../../domain/permissions";
import type { ReactNode } from "react";
import * as api from "../../data/api/invoiceIssuanceApi";

vi.mock("../../data/api/invoiceIssuanceApi");

function Wrapper({ children }: { children: ReactNode }) {
  return (
    <IssuancePermissionsContext.Provider
      value={{
        ...resolveIssuancePermissions(
          ["invoice-issuance.create", "invoice-issuance.view.filial-01"],
          true,
        ),
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

describe("QueuePage", () => {
  it("lista solicitações da filial e abre o detalhe", async () => {
    vi.mocked(api.listRequests).mockResolvedValue({
      items: [
        {
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
          created_by_name: "Maria da Silva",
          assignee_user_id: null,
          assignee_name: null,
          cancelled_at: null,
          cancelled_by_name: null,
          cancel_justification: null,
          issued_at: null,
          created_at: "2026-08-14T10:00:00+00:00",
          updated_at: "2026-08-14T10:00:00+00:00",
          items: [],
          attachments: [],
          items_count: 1,
          total_amount: 10,
        },
      ],
      total: 1,
      page: 1,
      page_size: 20,
      total_pages: 1,
    });
    const onOpen = vi.fn();
    render(
      <Wrapper>
        <QueuePage branch="01" onCreate={() => undefined} onOpen={onOpen} />
      </Wrapper>,
    );
    await waitFor(() => expect(screen.getByText("ACME LTDA")).toBeTruthy());
    expect(screen.getByTestId("queue-requester").textContent).toBe("Maria");
    fireEvent.click(screen.getByText("ACME LTDA"));
    expect(onOpen).toHaveBeenCalledWith("req-1");
  });
});
