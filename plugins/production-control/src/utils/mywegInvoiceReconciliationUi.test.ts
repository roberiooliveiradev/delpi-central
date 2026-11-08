import { describe, expect, it } from "vitest";

import {
  canShowPostedAsFact,
  completeCoverageDetailLabel,
  coverageStatusLabel,
  formatNullableDecimal,
  invoiceMatchStatusLabel,
  managerialBadgeClass,
  managerialStatusLabel,
  nullableDeltaToneClass,
  observedDeltaToneClass,
  remessaContextLabel,
} from "./mywegInvoiceReconciliationUi";

describe("mywegInvoiceReconciliationUi", () => {
  it("não converte null em zero", () => {
    expect(formatNullableDecimal(null)).toBe("Não disponível");
    expect(formatNullableDecimal(undefined)).toBe("Não disponível");
    expect(formatNullableDecimal("0")).toBe("0");
  });

  it("só trata NF como fato com cobertura completa", () => {
    expect(canShowPostedAsFact("complete", "0")).toBe(true);
    expect(canShowPostedAsFact("partial", "10")).toBe(false);
    expect(canShowPostedAsFact("pending_invoice_ingestion", "0")).toBe(false);
    expect(canShowPostedAsFact("unavailable", null)).toBe(false);
  });

  it("distingue cobertura completa com e sem NF", () => {
    expect(completeCoverageDetailLabel("12")).toBe("Com NF");
    expect(completeCoverageDetailLabel("0")).toBe("Sem NF confirmado");
    expect(completeCoverageDetailLabel(null)).toBe("Sem NF confirmado");
  });

  it("rotula status de cobertura e conciliação", () => {
    expect(coverageStatusLabel("complete")).toBe("Cobertura completa");
    expect(coverageStatusLabel("pending_invoice_ingestion")).toBe(
      "Aguardando importação fiscal",
    );
    expect(invoiceMatchStatusLabel("attributed_elsewhere")).toBe(
      "NF em outra identidade",
    );
    expect(invoiceMatchStatusLabel("multi_material_key")).toBe(
      "Múltiplos materiais",
    );
  });

  it("não colore ajuste indisponível como alta/baixa", () => {
    expect(nullableDeltaToneClass(null)).toBe("ppc-myweg-needs__delta");
    expect(nullableDeltaToneClass("-5")).toContain("delta--down");
    expect(nullableDeltaToneClass("5")).toContain("delta--up");
  });

  it("rotula classificação gerencial e evita vermelho em faturado", () => {
    expect(managerialStatusLabel("invoiced")).toBe("Faturado");
    expect(managerialStatusLabel("invoicing_with_difference")).toBe(
      "Faturamento com diferença",
    );
    expect(managerialStatusLabel("partial_invoicing")).toBe("Faturamento parcial");
    expect(managerialStatusLabel("reduction_to_investigate")).toBe(
      "Redução a investigar",
    );
    expect(managerialBadgeClass("invoiced")).toContain("mgr-badge--invoiced");
    expect(managerialBadgeClass("invoicing_with_difference")).toContain(
      "mgr-badge--difference",
    );
    expect(
      observedDeltaToneClass({
        managerialStatus: "invoiced",
        situationOrMovement: "decreased",
      }),
    ).toContain("delta--invoiced");
    expect(
      observedDeltaToneClass({
        managerialStatus: "invoicing_with_difference",
        situationOrMovement: "decreased",
      }),
    ).toContain("delta--invoiced");
    expect(remessaContextLabel("compatible_with_invoicing")).toBe(
      "Compatível com faturamento",
    );
  });
});
