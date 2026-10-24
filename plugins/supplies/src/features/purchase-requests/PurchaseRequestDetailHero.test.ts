import { describe, expect, it } from "vitest";

import {
  approvalBadgeVariant,
  countLinkedOrders,
  labelApprovalStatus,
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
