import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import type { PurchaseRequestDetail } from "./types";

const dir = dirname(fileURLToPath(import.meta.url));

/**
 * EN.A1 contract fixture — mirrors the producer payload
 * (api-delpi purchase_request_lines_sql → purchase-requests-api aggregation →
 * supplies-api passthrough + requester identity enrich).
 * Two lines with different units, two linked orders, one partial receipt.
 */
const fullPayload: PurchaseRequestDetail = {
  header: {
    branch: "01",
    request_number: "178764",
    issue_date: "2026-05-12",
    requester: {
      protheus_user_id: "000123",
      code: "USR01",
      name: "Maria Silva",
      display_name: "Maria Silva",
      photo_url: "/users/u-1/photo",
      user_id: "u-1",
    },
    approval_summary: { status: "approved" },
    visible_items_count: 2,
    cost_centers: [{ code: "4101", description: "Suprimentos" }],
    purchase_orders: [
      {
        branch: "01",
        order_number: "057175",
        order_item: "01",
        source_request_number: "178764",
        source_request_item: "0001",
        ordered_quantity: 150,
        received_quantity: 120,
        open_quantity: 30,
        issue_date: "2026-05-14",
        expected_delivery_date: "2026-06-30",
        supplier_code: "000111",
        supplier_store: "01",
        supplier_name: "Eletro S.A.",
        buyer_code: "C001",
        derived: {
          delivery_status: "overdue",
          days_until_due: null,
          days_overdue: 6,
          receipt_status: "partially_received",
        },
        receipts: [
          {
            branch: "01",
            invoice_number: "1042",
            invoice_series: "3",
            invoice_item: "001",
            purchase_order_number: "057175",
            purchase_order_item: "01",
            product_code: "CAB035",
            quantity: 60,
            unit_price: 140,
            total_value: 8400,
            invoice_issue_date: "2026-06-10",
            entry_date: "2026-06-12",
          },
        ],
      },
    ],
    suppliers: [{ code: "000111", store: "01", name: "Eletro S.A." }],
    first_order_date: "2026-05-14",
    last_order_date: "2026-05-14",
    first_receipt_date: "2026-06-12",
    last_receipt_date: "2026-06-12",
    // Present in the contract but unsafe as a single-UM KPI (P0.R1).
    requested_quantity: 300,
    ordered_quantity: 250,
    received_quantity: 120,
    has_overdue_order: true,
    max_days_overdue: 6,
  },
  lines: [
    {
      request_item: "0001",
      product_code: "CAB035",
      product_description: "CABO 35mm",
      requested_quantity: 200,
      cost_center_code: "4101",
      unit: "MT",
      request_required_date: "2026-06-20",
      ordered_quantity: 150,
      request_open_quantity: 50,
      request_issue_date: "2026-05-12",
      cost_center: { code: "4101", description: "Suprimentos" },
      account_code: "0010203",
      approval: { status: "approved", approver_name: "J. Pereira" },
      suggested_supplier: { code: "000111", store: "01", name: "Eletro S.A." },
      residual: 0,
      purchase_orders: [],
      derived: {
        overall_stage: "partially_received",
        order_status: "partially_ordered",
        receipt_status: "partially_received",
      },
    },
    {
      request_item: "0002",
      product_code: "TRAFO15",
      product_description: "TRAFO 15kVA",
      requested_quantity: 100,
      cost_center_code: "4200",
      unit: "UN",
      request_required_date: "2026-06-20",
      ordered_quantity: 100,
      request_open_quantity: 0,
      account_code: "0099",
      approval: { status: "approved" },
      residual: 0,
      derived: { overall_stage: "awaiting_receipt" },
    },
  ],
  timeline: [
    {
      type: "request_created",
      date: "2026-05-12",
      label: "Solicitação criada",
      reference: { request_number: "178764", request_item: "0001" },
      metadata: {},
    },
    {
      type: "purchase_order_created",
      date: "2026-05-14",
      label: "Pedido de compra criado",
      reference: { order_number: "057175", order_item: "01" },
      metadata: {},
    },
    {
      type: "expected_delivery",
      date: "2026-06-30",
      label: "Previsão de entrega",
      reference: { order_number: "057175" },
      metadata: {},
    },
    {
      type: "receipt",
      date: "2026-06-12",
      label: "Entrada NF",
      reference: { invoice_number: "1042", order_number: "057175" },
      metadata: {},
    },
  ],
};

describe("PurchaseRequestDetail contract (EN.A1)", () => {
  it("fixture espelha o payload real do produtor", () => {
    expect(fullPayload.header.request_number).toBe("178764");
    expect(fullPayload.lines).toHaveLength(2);
    expect(fullPayload.timeline).toHaveLength(4);
  });

  it("account_code preserva zeros à esquerda como string por item", () => {
    expect(fullPayload.lines[0].account_code).toBe("0010203");
    expect(fullPayload.lines[1].account_code).toBe("0099");
    expect(typeof fullPayload.lines[0].account_code).toBe("string");
  });

  it("aprovação por linha com nome do aprovador (D2)", () => {
    expect(fullPayload.lines[0].approval?.approver_name).toBe("J. Pereira");
    expect(fullPayload.lines[1].approval?.approver_name).toBeUndefined();
  });

  it("fornecedor sugerido tipado por item (D2) e ausente quando não há", () => {
    expect(fullPayload.lines[0].suggested_supplier?.name).toBe("Eletro S.A.");
    expect(fullPayload.lines[1].suggested_supplier).toBeUndefined();
  });

  it("pedidos vinculados com recebimentos aninhados e status derivado", () => {
    const order = fullPayload.header.purchase_orders?.[0];
    expect(order?.order_number).toBe("057175");
    expect(order?.derived?.days_overdue).toBe(6);
    expect(order?.receipts?.[0].invoice_number).toBe("1042");
  });

  it("UMs heterogêneas por item — nunca somadas", () => {
    const units = fullPayload.lines.map((l) => l.unit);
    expect(units).toEqual(["MT", "UN"]);
  });

  it("expected_delivery é marco planejado, não ocorrência", () => {
    const planned = fullPayload.timeline?.find(
      (e) => e.type === "expected_delivery",
    );
    expect(planned?.label).toBe("Previsão de entrega");
  });

  it("payload parcial legítimo: só estrutura mínima obrigatória", () => {
    const minimal: PurchaseRequestDetail = {
      header: { branch: "02", request_number: "000001" },
      lines: [{ request_item: "0001", product_code: "X" }],
    };
    expect(minimal.header.cost_centers).toBeUndefined();
    expect(minimal.timeline).toBeUndefined();
    expect(minimal.lines[0].account_code).toBeUndefined();
  });

  it("types.ts documenta o caveat semântico dos totais de quantidade", () => {
    const types = readFileSync(join(dir, "types.ts"), "utf8");
    expect(types).toContain("SEMANTIC CAVEAT");
    expect(types).toContain("PurchaseRequestLinkedOrder");
    expect(types).toContain("PurchaseRequestReceipt");
    expect(types).toContain("PurchaseRequestTimelineEvent");
    expect(types).toContain("account_code");
    expect(types).toContain("suggested_supplier");
    expect(types).toContain("approver_name");
  });
});
