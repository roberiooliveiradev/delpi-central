import { describe, expect, it } from "vitest";
import { buildIssuanceSheet } from "./issuanceSheet";
import type { IssuanceRequest } from "./types";

function request(overrides: Partial<IssuanceRequest> = {}): IssuanceRequest {
  return {
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
    status: "issued",
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
    assignee_user_id: "u2",
    assignee_name: "Ana Faturamento",
    cancelled_at: null,
    cancelled_by_name: null,
    cancel_justification: null,
    issued_at: "2026-08-14T12:00:00+00:00",
    created_at: "2026-08-14T10:00:00+00:00",
    updated_at: "2026-08-14T12:00:00+00:00",
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
  };
}

describe("buildIssuanceSheet", () => {
  it("expõe código e loja do destinatário para lançar na nota", () => {
    const party = buildIssuanceSheet(request()).find((section) => section.id === "party");
    const byLabel = Object.fromEntries((party?.fields ?? []).map((field) => [field.label, field]));
    expect(byLabel.Código.value).toBe("000256");
    expect(byLabel.Código.copyable).toBe(true);
    expect(byLabel.Loja.value).toBe("01");
    expect(byLabel.Tipo.value).toBe("Cliente");
  });

  it("agrupa pedidos de venda dos itens", () => {
    const invoice = buildIssuanceSheet(request()).find((section) => section.id === "invoice");
    const pv = invoice?.fields.find((field) => field.label === "Pedido de venda");
    expect(pv?.value).toBe("000111");
  });

  it("copia o código da transportadora, não o nome", () => {
    const freight = buildIssuanceSheet(request()).find((section) => section.id === "freight");
    const carrier = freight?.fields.find((field) => field.label === "Transportadora");
    expect(carrier?.value).toBe("000001 — JADLOG");
    expect(carrier?.copyValue).toBe("000001");
    expect(carrier?.copyable).toBe(true);
  });

  it("inclui razão, CNPJ, endereço e telefone da transportadora", () => {
    const freight = buildIssuanceSheet(
      request({
        carrier_legal_name: "Mir Transp. Logistica LTDA",
        carrier_tax_id: "03565095000189",
        carrier_address: "Rodovia BR-470, 8220, Canta Galo, Rio do Sul-SC, CEP 89163-020",
        carrier_phone: "(47) 3522-6972",
      }),
    ).find((section) => section.id === "freight");
    const byLabel = Object.fromEntries((freight?.fields ?? []).map((field) => [field.label, field]));
    expect(byLabel["Razão social"].value).toContain("Mir Transp");
    expect(byLabel["CNPJ transportadora"].value).toBe("03565095000189");
    expect(byLabel.Endereço.value).toContain("Rio do Sul-SC");
    expect(byLabel.Telefone.value).toBe("(47) 3522-6972");
  });

  it("omite complemento quando não há observação", () => {
    const sections = buildIssuanceSheet(request({ observation: null }));
    expect(sections.some((section) => section.id === "extras")).toBe(false);
  });

  it("não inclui situação na ficha (status fica no cabeçalho)", () => {
    const sections = buildIssuanceSheet(request());
    expect(sections.some((section) => section.id === "situation")).toBe(false);
    expect(
      sections.flatMap((section) => section.fields).some((field) => field.label === "Status"),
    ).toBe(false);
  });
});
