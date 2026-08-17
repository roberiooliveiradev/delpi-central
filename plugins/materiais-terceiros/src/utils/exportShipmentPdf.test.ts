import { describe, expect, it } from "vitest";

import type { Shipment } from "../types/thirdPartyMaterials";
import { buildShipmentDelpiDocumentSpec } from "./shipmentPdfSpec";

function sampleShipment(overrides: Partial<Shipment> = {}): Shipment {
  return {
    shipment_recno: 1,
    branch: "01",
    shipment_id: "UCSTCQ",
    product: {
      code: "10211413",
      customer_reference: "10018137",
      description: "VENTILADOR AXIAL",
      unit: "PC",
      type: "MP",
      group: "1021",
      blocked: false,
    },
    partner: {
      type: "C",
      code: "000001",
      store: "11",
      name: "WEG DRIVES & CONTROLS - AUTOMAÇÃO LTDA",
      short_name: "WEG",
      blocked: false,
    },
    receipt_invoice: {
      number: "004320183",
      series: "1",
      issued_on: "2026-03-10",
      posted_on: "2026-03-12",
      tes: "085",
    },
    received_quantity: 1600,
    returned_quantity: 1600,
    pending_balance: 0,
    status: "completed",
    has_balance: false,
    attended_indicator: null,
    summed_return_quantity: 1600,
    control_difference: 0,
    returns: [
      {
        return_recno: 11,
        number: "102188",
        series: "1",
        issued_on: "2026-04-01",
        posted_on: "2026-04-02",
        tes: "090",
        quantity: 800,
        accumulated_returned_quantity: 800,
        balance_after_return: 800,
        partner_type: "C",
        partner_code: null,
        partner_store: null,
      },
      {
        return_recno: 12,
        number: "102189",
        series: "1",
        issued_on: "2026-04-15",
        posted_on: "2026-04-16",
        tes: "090",
        quantity: 800,
        accumulated_returned_quantity: 1600,
        balance_after_return: 0,
        partner_type: "F",
        partner_code: null,
        partner_store: null,
      },
    ],
    ...overrides,
  };
}

describe("buildShipmentDelpiDocumentSpec", () => {
  it("monta cabeçalho, recebimento e tabela de devoluções", () => {
    const spec = buildShipmentDelpiDocumentSpec(sampleShipment());

    expect(spec.documentTitle).toBe("Materiais de Terceiros");
    expect(spec.subtitle).toContain("004320183");
    expect(spec.subtitle).toContain("10211413");
    expect(spec.badge).toBe("Concluído");
    expect(spec.badgeTone).toBe("approved");
    expect(spec.summaryLines?.map((line) => line.label)).toEqual(
      expect.arrayContaining([
        "Filial",
        "Identidade",
        "Ref. cliente",
        "NF recebimento",
        "TES entrada",
        "Qtd. recebida",
        "Saldo pendente",
        "Devoluções",
      ]),
    );
    expect(spec.summaryLines?.find((line) => line.label === "Ref. cliente")?.value).toBe("10018137");
    expect(spec.summaryLines?.find((line) => line.label === "Qtd. recebida")?.value).toContain("1.600");
    expect(spec.summaryLines?.find((line) => line.label === "Devoluções")?.value).toBe("2");
    expect(spec.tables).toHaveLength(1);
    expect(spec.tables?.[0].title).toBe("Devoluções");
    expect(spec.tables?.[0].rows).toHaveLength(2);
    expect(spec.tables?.[0].rows[1].partnerType).toBe("Fornecedor");
    expect(spec.footerNote).toBe("Relatório gerado pelo Minha DELPI.");
  });

  it("omite tabela quando não há devoluções", () => {
    const spec = buildShipmentDelpiDocumentSpec(sampleShipment({ returns: [], status: "no_return" }));
    expect(spec.badge).toBe("Sem retorno");
    expect(spec.tables).toBeUndefined();
    expect(spec.summaryLines?.find((line) => line.label === "Devoluções")?.value).toBe("Nenhuma");
  });
});
