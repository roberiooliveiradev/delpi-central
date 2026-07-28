import { cleanup, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { LinkedPurchaseOrderReceipt } from "./LinkedPurchaseOrderReceipt";
import * as api from "../../data/api/invoicePostingApi";
import type { InvoicePostingRequest } from "../../domain/types";

vi.mock("../../data/api/invoicePostingApi");

function baseRequest(
  overrides: Partial<InvoicePostingRequest> = {},
): InvoicePostingRequest {
  return {
    id: "req-1",
    branch_code: "01",
    document_number: "00123456",
    document_match_key: "000123456",
    series: "",
    supplier_code: "000001",
    supplier_store: "01",
    supplier_name: "Alpha Transportes",
    supplier_short_name: null,
    issue_date: "2026-07-01",
    amount: 50,
    received_at: "2026-07-02T10:00:00+00:00",
    observation: null,
    status: "pending",
    block_reason: null,
    block_description: null,
    created_by_user_id: "u1",
    created_by_name: "Criador",
    assignee_user_id: null,
    assignee_name: null,
    cancelled_at: null,
    cancelled_by_user_id: null,
    cancelled_by_name: null,
    cancel_justification: null,
    completion_source: null,
    sf1_recno: null,
    erp_entry_date: null,
    reconciled_at: null,
    divergence_alert: false,
    divergence_detected_at: null,
    divergence_detail: null,
    linked_po_number: "000123",
    linked_po_delivery_date: "2026-07-20",
    linked_po_issue_date: "2026-07-10",
    linked_po_open_value: 150.5,
    linked_po_product_count: 2,
    linked_po_linked_at: "2026-07-12T11:00:00+00:00",
    linked_po_linked_by_user_id: "u2",
    linked_po_linked_by_name: "Processador",
    linked_purchase_orders: [
      {
        order_number: "000123",
        delivery_date: "2026-07-20",
        issue_date: "2026-07-10",
        open_value: 150.5,
        product_count: 2,
        linked_at: "2026-07-12T11:00:00+00:00",
        linked_by_user_id: "u2",
        linked_by_name: "Processador",
      },
    ],
    created_at: "2026-07-02T10:00:00+00:00",
    updated_at: "2026-07-02T10:00:00+00:00",
    ...overrides,
  };
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("LinkedPurchaseOrderReceipt", () => {
  it("não renderiza sem pedido amarrado", () => {
    render(
      <LinkedPurchaseOrderReceipt
        requestId="req-1"
        request={baseRequest({
          linked_po_number: null,
          linked_purchase_orders: [],
        })}
      />,
    );
    expect(screen.queryByTestId("linked-po-receipt")).toBeNull();
    expect(api.listRequestPurchaseOrders).not.toHaveBeenCalled();
  });

  it("lista itens do PC amarrado no estilo cupom", async () => {
    vi.mocked(api.listRequestPurchaseOrders).mockResolvedValue({
      request_id: "req-1",
      branch_code: "01",
      supplier_code: "000001",
      supplier_store: "01",
      supplier_name: "Alpha Transportes",
      order_count: 1,
      group_count: 1,
      item_count: 2,
      linked: [
        {
          order_number: "000123",
          delivery_date: "2026-07-20",
          issue_date: "2026-07-10",
          open_value: 150.5,
          product_count: 2,
          linked_at: "2026-07-12T11:00:00+00:00",
          linked_by_user_id: "u2",
          linked_by_name: "Processador",
        },
      ],
      can_link: true,
      groups: [
        {
          order_number: "000123",
          delivery_date: "2026-07-20",
          issue_date: "2026-07-10",
          product_count: 2,
          open_value: 150.5,
          item_count: 2,
          items: [
            {
              branch: "01",
              order_number: "000123",
              order_item: "0001",
              product_code: "900100",
              product_description: "Parafuso M8",
              warehouse: "01",
              unit: "UN",
              ordered_quantity: 10,
              delivered_quantity: 0,
              open_quantity: 10,
              pre_invoice_quantity: 0,
              issue_date: "2026-07-10",
              expected_delivery_date: "2026-07-20",
              supplier_code: "000001",
              supplier_store: "01",
              supplier_name: "Alpha",
              unit_price: 10,
              open_value: 100,
            },
            {
              branch: "01",
              order_number: "000123",
              order_item: "0002",
              product_code: "900200",
              product_description: "Porca M8",
              warehouse: "01",
              unit: "UN",
              ordered_quantity: 5,
              delivered_quantity: 0,
              open_quantity: 5,
              pre_invoice_quantity: 0,
              issue_date: "2026-07-10",
              expected_delivery_date: "2026-07-20",
              supplier_code: "000001",
              supplier_store: "01",
              supplier_name: "Alpha",
              unit_price: 10.1,
              open_value: 50.5,
            },
          ],
        },
      ],
    });

    render(
      <LinkedPurchaseOrderReceipt
        requestId="req-1"
        request={baseRequest()}
      />,
    );

    await waitFor(() =>
      expect(screen.getByTestId("linked-po-receipt-total")).toBeTruthy(),
    );
    expect(screen.getByText("Cupom do pedido de compra")).toBeTruthy();
    expect(screen.getByText("Parafuso M8")).toBeTruthy();
    expect(screen.getByText("Porca M8")).toBeTruthy();
    expect(screen.getByText("900100")).toBeTruthy();
    expect(screen.getByTestId("linked-po-receipt-total").textContent).toMatch(
      /150[,.]50/,
    );
  });

  it("mostra fallback quando o PC amarrado não tem itens abertos", async () => {
    vi.mocked(api.listRequestPurchaseOrders).mockResolvedValue({
      request_id: "req-1",
      branch_code: "01",
      supplier_code: "000001",
      supplier_store: "01",
      supplier_name: "Alpha",
      order_count: 0,
      group_count: 0,
      item_count: 0,
      groups: [],
      linked: [
        {
          order_number: "000123",
          delivery_date: "2026-07-20",
          issue_date: "2026-07-10",
          open_value: 150.5,
          product_count: 2,
          linked_at: null,
          linked_by_user_id: null,
          linked_by_name: null,
        },
      ],
      can_link: false,
    });

    render(
      <LinkedPurchaseOrderReceipt
        requestId="req-1"
        request={baseRequest()}
      />,
    );

    await waitFor(() =>
      expect(screen.getByTestId("linked-po-receipt-empty")).toBeTruthy(),
    );
    expect(screen.getByText(/não estão disponíveis/i)).toBeTruthy();
  });
});
