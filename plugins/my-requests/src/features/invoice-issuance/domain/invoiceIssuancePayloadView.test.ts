import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import type { IssuanceItem, Party } from "./types";
import { buildInvoiceIssuancePayload } from "./invoiceWizardPayload";
import {
  INVOICE_PAYLOAD_DISPLAY_KEYS,
  invoicePayloadFieldIds,
  projectInvoiceIssuancePayload,
} from "./invoiceIssuancePayloadView";

const party: Party = {
  party_type: "customer",
  party_code: "C001",
  party_store: "01",
  party_name: "Cliente Teste",
  tax_id: "12345678000199",
  blocked: false,
};

function item(overrides: Partial<IssuanceItem> = {}): IssuanceItem {
  return {
    product_code: "P001",
    product_description: "Parafuso",
    quantity: 2,
    unit_price: 10.125,
    stock_write_off: true,
    sales_order: "PV100",
    sales_order_item: "01",
    ...overrides,
  };
}

function fullPayload(overrides: Record<string, unknown> = {}) {
  return {
    ...buildInvoiceIssuancePayload({
      party,
      invoiceType: "other",
      invoiceTypeOther: "Remessa simbólica",
      freightMode: "fob",
      carrier: {
        carrier_code: "T01",
        carrier_name: "Rapidão",
        legal_name: null,
        tax_id: null,
        blocked: false,
      },
      weightKg: "1.5",
      volumeCount: "2",
      observation: "Entregar na portaria",
      items: [item(), item({ product_code: "P002", product_description: "Porca", quantity: 0, unit_price: 0, stock_write_off: false, sales_order: null, sales_order_item: null })],
    }),
    ...overrides,
  };
}

function valuesOf(view: ReturnType<typeof projectInvoiceIssuancePayload>): string[] {
  return [
    ...view.recipient,
    ...view.invoice,
    ...view.freight,
    ...view.extras,
    ...view.items.flatMap((row) => row.fields),
  ].map((field) => `${field.label}=${field.value}`);
}

describe("projectInvoiceIssuancePayload", () => {
  it("mostra todos os campos de negócio preenchidos pelo wizard", () => {
    const payload = fullPayload();
    for (const key of Object.keys(payload)) {
      if (key === "items") continue;
      expect(INVOICE_PAYLOAD_DISPLAY_KEYS.root).toContain(key);
    }
    const first = (payload.items as Record<string, unknown>[])[0];
    for (const key of Object.keys(first)) {
      expect(INVOICE_PAYLOAD_DISPLAY_KEYS.item).toContain(key);
    }

    const lines = valuesOf(projectInvoiceIssuancePayload(payload));
    expect(lines).toEqual(expect.arrayContaining([
      "Nome=Cliente Teste",
      "Tipo=Cliente",
      "Código / loja=C001 / 01",
      "CPF/CNPJ=12.345.678/0001-99",
      "Tipo de nota fiscal=Outros",
      "Descrição do tipo=Remessa simbólica",
      "Frete=FOB",
      "Transportadora=T01 — Rapidão",
      "Peso (kg)=1,5",
      "Volumes=2",
      "Observação=Entregar na portaria",
      "Código=P001",
      "Descrição=Parafuso",
      "Quantidade=2",
      "Preço unitário=R$ 10,125",
      "Pedido de venda=PV100 / 01",
      "Baixa de estoque=Sim",
      "Código=P002",
      "Quantidade=0",
      "Preço unitário=R$ 0",
      "Baixa de estoque=Não",
    ]));
    expect(lines.some((line) => line.startsWith("Pedido de venda=") && line.includes("P002"))).toBe(false);
  });

  it("omite opcionais vazios e não inventa traço", () => {
    const view = projectInvoiceIssuancePayload({
      party_name: "ACME",
      party_code: "C9",
      party_store: "01",
      party_type: "supplier",
      invoice_type: "sale",
      freight_mode: "cif",
      tax_id: null,
      invoice_type_other: "",
      carrier_code: null,
      carrier_name: null,
      observation: "   ",
      weight_kg: 3,
      volume_count: 1,
      items: [{ product_code: "P9", quantity: "1.250", unit_price: "10.50" }],
    });
    const lines = valuesOf(view);
    expect(lines).toContain("Tipo=Fornecedor");
    expect(lines).toContain("Quantidade=1,250");
    expect(lines).toContain("Preço unitário=R$ 10,50");
    expect(lines.join("\n")).not.toMatch(/CPF\/CNPJ|Transportadora|Observação|Descrição do tipo|Pedido de venda|Baixa de estoque|—/);
  });

  it("não exibe baixa de estoque quando o item não traz a chave, nem o default da raiz", () => {
    const view = projectInvoiceIssuancePayload({
      party_name: "ACME",
      stock_write_off: false,
      checklist: { recipient: true },
      _migration: { source: "invoice_issuance" },
      items: [{ product_code: "P1", quantity: 1, unit_price: 1 }],
    });
    const lines = valuesOf(view).join("\n");
    expect(lines).not.toMatch(/Baixa de estoque|checklist|migration|invoice_issuance/);
  });

  it("mostra baixa de estoque gravada no item, inclusive false", () => {
    const view = projectInvoiceIssuancePayload({
      items: [{ product_code: "P1", quantity: 1, unit_price: 1, stock_write_off: false }],
    });
    expect(valuesOf(view)).toContain("Baixa de estoque=Não");
  });

  it("apresenta cada item e campos legados persistidos", () => {
    const view = projectInvoiceIssuancePayload({
      carrier_code: "T02",
      carrier_legal_name: "Transporte Ltda",
      carrier_tax_id: "52998224725",
      purchase_order_number: "PC-9",
      items: [
        {
          line_number: 4,
          product_code: "PA",
          product_description: "Eixo",
          quantity: 1,
          unit_price: 2,
          sales_order: "PV1",
          customer_order_number: "OC-7",
          stock_write_off: true,
        },
        { product_code: "PB", quantity: 3, unit_price: 4 },
      ],
    });
    expect(view.items.map((row) => row.title)).toEqual(["Item 4 · PA", "Item 2 · PB"]);
    const lines = valuesOf(view);
    expect(lines).toEqual(expect.arrayContaining([
      "Transportadora=T02",
      "Razão social da transportadora=Transporte Ltda",
      "CPF/CNPJ da transportadora=529.982.247-25",
      "Pedido de compra=PC-9",
      "Pedido de venda=PV1",
      "Pedido do cliente=OC-7",
    ]));
    expect(view.items).toHaveLength(2);
  });

  it("reflete o payload atualizado depois da correção", () => {
    const before = projectInvoiceIssuancePayload(fullPayload());
    const after = projectInvoiceIssuancePayload(
      fullPayload({ observation: "Nova observação do reenvio", weight_kg: "9.25" }),
    );
    expect(valuesOf(before)).toContain("Observação=Entregar na portaria");
    expect(valuesOf(after)).toContain("Observação=Nova observação do reenvio");
    expect(valuesOf(after)).toContain("Peso (kg)=9,25");
    expect(valuesOf(after)).not.toContain("Observação=Entregar na portaria");
  });

  it("tolera payload antigo parcial sem derrubar os campos presentes", () => {
    const view = projectInvoiceIssuancePayload({
      party_name: "Legado",
      party_code: "L1",
      items: [{ product_code: "OLD", quantity: 1, unit_price: 8 }],
    });
    expect(invoicePayloadFieldIds(view)).toEqual([
      "recipient.name",
      "recipient.codeStore",
      "item.productCode",
      "item.quantity",
      "item.unitPrice",
    ]);
    expect(projectInvoiceIssuancePayload(null).items).toEqual([]);
    expect(projectInvoiceIssuancePayload({}).recipient).toEqual([]);
  });

  it("não depende de perfil: a mesma entrada produz a mesma visão", () => {
    const payload = fullPayload();
    expect(projectInvoiceIssuancePayload(payload)).toEqual(
      projectInvoiceIssuancePayload(payload),
    );
  });
});

const root = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "..");

describe("InvoiceIssuancePayloadPanel structural", () => {
  it("renderiza a projeção no detalhe, sem filtro por perfil", () => {
    const panel = readFileSync(
      join(root, "features/invoice-issuance/ui/InvoiceIssuancePayloadPanel.tsx"),
      "utf8",
    );
    const page = readFileSync(join(root, "pages/RequestDetailPage.tsx"), "utf8");
    expect(panel).toContain("projectInvoiceIssuancePayload");
    expect(panel).toContain('title: "Destinatário"');
    expect(panel).toContain('title="Itens"');
    expect(panel).not.toMatch(/created_by|allowed_actions|role/);
    expect(page).toContain("<InvoiceIssuancePayloadPanel payload={request.payload} />");
    expect(page).not.toMatch(/InvoiceIssuancePayloadPanel[\s\S]{0,80}created_by/);
  });
});
