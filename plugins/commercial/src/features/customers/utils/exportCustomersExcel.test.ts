import { describe, expect, it } from "vitest";

import type { CustomerSummary } from "../types/customerSummary";
import { buildCustomersExportPayload } from "./customerExportPayload";
import {
  CUSTOMER_COLUMN_CATALOG,
  type CustomerColumnKey,
} from "./customerTableColumns";

const CUSTOMER: CustomerSummary = {
  key: "000123|01",
  codigo: "000123",
  loja: "01",
  nome: "Cliente Exemplo",
  quantidadePedidosAbertos: 2,
  quantidadeLinhasAbertas: 3,
  valorTotalAberto: 1250.5,
  quantidadePedidosAtrasados: 1,
  maiorAtrasoDias: 4,
  proximaEntrega: "2026-08-15",
  quantidadePedidosParciais: 0,
  temAtraso: true,
  temPedidoParcial: false,
  lines: [],
  sellerName: "Maria",
  city: "Joinville",
  state: "SC",
  lastPurchaseDate: "2026-08-01",
  billed12m: 98_765.43,
  billingTrend: "up",
  billingTrendPct: 12.5,
  coverageKnown: true,
  enrichmentAvailable: true,
  status: "atencao",
};

function column(key: CustomerColumnKey) {
  const found = CUSTOMER_COLUMN_CATALOG.find((item) => item.key === key);
  if (!found) throw new Error(`coluna ausente: ${key}`);
  return found;
}

describe("buildCustomersExportPayload", () => {
  it("exporta somente as colunas visíveis, na mesma ordem e com os mesmos rótulos", () => {
    const columns = [column("valorTotalAberto"), column("nome"), column("status")];

    const payload = buildCustomersExportPayload([CUSTOMER], columns);

    expect(payload.columns).toEqual([
      { key: "valorTotalAberto", label: "Em aberto" },
      { key: "nome", label: "Cliente" },
      { key: "status", label: "Status" },
    ]);
    expect(payload.rows).toEqual([
      {
        valorTotalAberto: 1250.5,
        nome: "Cliente Exemplo (000123-01)",
        status: "Atenção",
      },
    ]);
  });

  it("mantém formatos legíveis para campos derivados", () => {
    const payload = buildCustomersExportPayload(
      [CUSTOMER],
      [column("city"), column("billed12m"), column("billingTrend")],
    );

    expect(payload.rows[0]).toEqual({
      city: "Joinville / SC",
      billed12m: 98_765.43,
      billingTrend: "Alta (12,5%)",
    });
  });

  it("deixa enrichment sem cobertura vazio sem inventar zero", () => {
    const payload = buildCustomersExportPayload(
      [
        {
          ...CUSTOMER,
          coverageKnown: false,
          enrichmentAvailable: false,
        },
      ],
      [
        column("city"),
        column("lastPurchaseDate"),
        column("billed12m"),
        column("billingTrend"),
      ],
    );

    expect(payload.rows[0]).toEqual({
      city: "",
      lastPurchaseDate: "",
      billed12m: "",
      billingTrend: "",
    });
  });
});
