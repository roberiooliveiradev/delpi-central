import { describe, expect, it } from "vitest";

import {
  approvalBadgeVariant,
  collectLinkedOrders,
  collectReceipts,
  countLinkedOrders,
  formatQuantityWithUnit,
  hasCompleteOrderIdentity,
  labelApprovalStatus,
  labelLinkedOrderDeliveryStatus,
  linkedOrderDeliveryVariant,
  timelineEventTone,
  timelineReferenceLabel,
  uniqueApproverNames,
} from "./query";

const LABELS = {
  approved: "Aprovada",
  rejected: "Rejeitada",
  blocked: "Bloqueada",
  unknown: "Não informada",
};

describe("EN.A2 — helpers do hero da ficha SC", () => {
  it("countLinkedOrders conta pedidos distintos por (filial, número)", () => {
    const orders = [
      { branch: "01", order_number: "057175", order_item: "01" },
      { branch: "01", order_number: "057175", order_item: "02" },
      { branch: "01", order_number: "057190", order_item: "03" },
    ];
    expect(countLinkedOrders(orders)).toBe(2);
    expect(countLinkedOrders([])).toBe(0);
    expect(countLinkedOrders(null)).toBe(0);
    expect(countLinkedOrders(undefined)).toBe(0);
  });

  it("countLinkedOrders distingue mesmo número em filiais diferentes", () => {
    const orders = [
      { branch: "01", order_number: "057175" },
      { branch: "02", order_number: "057175" },
    ];
    expect(countLinkedOrders(orders)).toBe(2);
  });

  it("uniqueApproverNames deduplica e preserva granularidade por item", () => {
    const lines = [
      { approval: { approver_name: "J. Pereira" } },
      { approval: { approver_name: "J. Pereira" } },
      { approval: { approver_name: "  M. Souza  " } },
      { approval: { approver_name: null } },
      { approval: null },
      {},
    ];
    expect(uniqueApproverNames(lines)).toEqual(["J. Pereira", "M. Souza"]);
    expect(uniqueApproverNames([])).toEqual([]);
    expect(uniqueApproverNames(undefined)).toEqual([]);
    expect(uniqueApproverNames([{ approval: {} }])).toEqual([]);
  });

  it("labelApprovalStatus usa somente estados canônicos — sem inventar", () => {
    expect(labelApprovalStatus("approved", LABELS)).toBe("Aprovada");
    expect(labelApprovalStatus("rejected", LABELS)).toBe("Rejeitada");
    expect(labelApprovalStatus("blocked", LABELS)).toBe("Bloqueada");
    expect(labelApprovalStatus("unknown", LABELS)).toBe("Não informada");
    expect(labelApprovalStatus(null, LABELS)).toBe("Não informada");
    expect(labelApprovalStatus("  ", LABELS)).toBe("Não informada");
  });

  it("approvalBadgeVariant mapeia aprovação para tom correto", () => {
    expect(approvalBadgeVariant("approved")).toBe("success");
    expect(approvalBadgeVariant("rejected")).toBe("danger");
    expect(approvalBadgeVariant("blocked")).toBe("warning");
    expect(approvalBadgeVariant("unknown")).toBe("neutral");
    expect(approvalBadgeVariant(undefined)).toBe("neutral");
  });
});

describe("EN.A3–A5 — itens, pedidos vinculados e navegação", () => {
  it("countLinkedOrders ignora identidade incompleta (residual EN.A2)", () => {
    const orders = [
      { branch: "01", order_number: "057175" },
      { branch: "", order_number: "057190" },
      { branch: "01", order_number: "   " },
      { branch: null, order_number: "057200" },
      { branch: "02", order_number: null },
    ];
    expect(countLinkedOrders(orders)).toBe(1);
    // Uma coleção não vazia só de referências incompletas nunca vira "1".
    expect(
      countLinkedOrders([{ branch: "", order_number: "" }, {}]),
    ).toBe(0);
  });

  it("hasCompleteOrderIdentity exige filial e número", () => {
    expect(
      hasCompleteOrderIdentity({ branch: "01", order_number: "057175" }),
    ).toBe(true);
    expect(hasCompleteOrderIdentity({ branch: "01", order_number: " " })).toBe(
      false,
    );
    expect(hasCompleteOrderIdentity({ branch: null, order_number: "1" })).toBe(
      false,
    );
    expect(hasCompleteOrderIdentity(undefined)).toBe(false);
  });

  it("collectLinkedOrders deduplica por filial+número+item", () => {
    const order = { branch: "01", order_number: "057175", order_item: "01" };
    const sibling = { branch: "01", order_number: "057175", order_item: "02" };
    const lines = [
      { purchase_orders: [order, sibling] },
      { purchase_orders: [order] },
      {},
    ];
    const collected = collectLinkedOrders(lines);
    expect(collected).toHaveLength(2);
    expect(collectLinkedOrders(undefined)).toEqual([]);
    expect(collectLinkedOrders([{}])).toEqual([]);
  });

  it("collectReceipts achata recebimentos dos pedidos vinculados", () => {
    const orders = [
      {
        order_number: "057175",
        receipts: [{ invoice_number: "001" }, { invoice_number: "002" }],
      },
      { order_number: "057190" },
      { order_number: "057200", receipts: [] },
    ];
    const receipts = collectReceipts(orders);
    expect(receipts).toHaveLength(2);
    expect(collectReceipts(undefined)).toEqual([]);
    expect(collectReceipts([])).toEqual([]);
  });

  it("formatQuantityWithUnit sempre acompanha a UM da linha", () => {
    expect(formatQuantityWithUnit(10, "UN")).toBe("10 UN");
    expect(formatQuantityWithUnit(0, "KG")).toBe("0 KG");
    expect(formatQuantityWithUnit(1.5, "MT")).toBe("1,5 MT");
    expect(formatQuantityWithUnit(10, null)).toBe("10");
    expect(formatQuantityWithUnit(null, "UN")).toBe("—");
  });

  it("labelLinkedOrderDeliveryStatus usa o vocabulário do produtor", () => {
    expect(labelLinkedOrderDeliveryStatus("received")).toBe("Recebido");
    expect(labelLinkedOrderDeliveryStatus("overdue")).toBe("Em atraso");
    expect(labelLinkedOrderDeliveryStatus("on_time")).toBe("No prazo");
    expect(labelLinkedOrderDeliveryStatus("not_applicable")).toBe(
      "Não aplicável",
    );
    expect(labelLinkedOrderDeliveryStatus(null)).toBe("—");
    expect(linkedOrderDeliveryVariant("overdue")).toBe("danger");
    expect(linkedOrderDeliveryVariant("received")).toBe("success");
    expect(linkedOrderDeliveryVariant("on_time")).toBe("info");
    expect(linkedOrderDeliveryVariant("not_applicable")).toBe("neutral");
  });

  it("timeline: previsão é marcada como planejada, eventos como neutros", () => {
    expect(timelineEventTone("expected_delivery")).toBe("info");
    expect(timelineEventTone("request_created")).toBe("neutral");
    expect(timelineEventTone("purchase_order_created")).toBe("neutral");
    expect(timelineEventTone("receipt")).toBe("neutral");
  });

  it("timelineReferenceLabel monta contexto PC/NF/item sem inventar", () => {
    const fmt = {
      order: (n: string) => `PC ${n}`,
      invoice: (n: string) => `NF ${n}`,
      item: (i: string) => `Item ${i}`,
    };
    expect(
      timelineReferenceLabel(
        { type: "receipt", reference: { invoice_number: "123", order_number: "057175" } },
        fmt,
      ),
    ).toBe("PC 057175 · NF 123");
    expect(
      timelineReferenceLabel(
        { type: "request_created", reference: { request_item: "002" } },
        fmt,
      ),
    ).toBe("Item 002");
    expect(
      timelineReferenceLabel({ type: "receipt", reference: null }, fmt),
    ).toBe("");
  });
});
