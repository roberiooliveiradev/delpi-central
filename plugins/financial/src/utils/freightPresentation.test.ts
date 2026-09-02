import { describe, expect, it } from "vitest";

import { copy } from "../content/copy";
import type { FreightAllocation, FreightInvoice } from "../types";
import {
  formatDecimalCurrency,
  formatFreightLimit,
  formatFreightPercent,
  freightReasonLabels,
  freightRowClassName,
  freightSituationLabel,
  freightSituationTone,
  hasPartialBase,
} from "./freightPresentation";

function allocation(overrides: Partial<FreightAllocation> = {}): FreightAllocation {
  return {
    freightDocument: "000000010",
    freightSeries: "1",
    carrierCode: "000099",
    carrierStore: "01",
    carrierName: "TRANSPORTADORA",
    freightIssueDate: "20260310",
    freightAccessKey: "4326".padEnd(44, "0"),
    freightGrossValue: "100.00",
    allocationBase: "1000.00",
    allocatedValue: "100.00",
    linkedInvoiceCount: 1,
    ...overrides,
  };
}

function invoice(overrides: Partial<FreightInvoice> = {}): FreightInvoice {
  return {
    branch: "01",
    invoiceDocument: "000000001",
    invoiceSeries: "1",
    supplierCode: "000045",
    supplierStore: "01",
    supplierName: "FORNECEDOR",
    issueDate: "20260305",
    entryDate: "20260306",
    goodsValue: "1000.00",
    freightTotal: "32.50",
    freightPercent: "3.25",
    freightLimit: "3.25",
    situation: "normal",
    reasonCodes: [],
    freightDocumentCount: 1,
    allocations: [allocation()],
    ...overrides,
  };
}

describe("formatFreightPercent", () => {
  it("keeps the two decimals used to compare against the branch limit", () => {
    expect(formatFreightPercent("3.25")).toBe("3,25%");
    expect(formatFreightPercent("12.5")).toBe("12,50%");
  });

  it("renders a dash when the percentage could not be calculated", () => {
    expect(formatFreightPercent(null)).toBe("—");
    expect(formatFreightPercent("")).toBe("—");
  });
});

describe("formatFreightLimit", () => {
  it("labels a branch without a configured limit instead of showing zero", () => {
    expect(formatFreightLimit(null)).toBe(copy.freight.noLimitBadge);
    expect(formatFreightLimit("4.25")).toBe("4,25%");
  });
});

describe("formatDecimalCurrency", () => {
  it("formats the decimal string sent by the BFF", () => {
    expect(formatDecimalCurrency("1234.56")).toBe(
      new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(1234.56),
    );
    expect(formatDecimalCurrency(null)).toBe("—");
  });
});

describe("freightSituationTone", () => {
  it("separates above limit from inconsistent", () => {
    expect(freightSituationTone("normal")).toBe("success");
    expect(freightSituationTone("above_limit")).toBe("danger");
    expect(freightSituationTone("inconsistent")).toBe("warning");
  });

  it("exposes a distinct kit row tone for each highlighted situation", () => {
    expect(freightRowClassName("normal")).toBeUndefined();
    expect(freightRowClassName("above_limit")).toBe("delpi-ui-table__row--tone-danger");
    expect(freightRowClassName("inconsistent")).toBe("delpi-ui-table__row--tone-warning");
  });

  it("labels the situation with the plugin copy", () => {
    expect(freightSituationLabel("above_limit")).toBe(copy.freight.situations.above_limit);
  });
});

describe("hasPartialBase", () => {
  it("flags a CT-e shared with other invoices", () => {
    expect(hasPartialBase(invoice(), allocation({ linkedInvoiceCount: 2 }))).toBe(true);
  });

  it("flags a base larger than this invoice even with a single linked invoice", () => {
    expect(
      hasPartialBase(invoice({ goodsValue: "400.00" }), allocation({ allocationBase: "1000.00" })),
    ).toBe(true);
  });

  it("does not flag a CT-e fully allocated to this invoice", () => {
    expect(hasPartialBase(invoice(), allocation())).toBe(false);
  });
});

describe("freightReasonLabels", () => {
  it("translates reason codes and falls back to the raw code", () => {
    const labels = new Map([["nf_not_found", "NF não localizada"]]);
    expect(freightReasonLabels(["nf_not_found", "outro"], labels)).toBe(
      "NF não localizada · outro",
    );
    expect(freightReasonLabels([], labels)).toBe("—");
  });
});
