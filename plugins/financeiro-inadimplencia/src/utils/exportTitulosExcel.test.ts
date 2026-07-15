import { describe, expect, it } from "vitest";

import type { InadimplenciaTituloItem } from "../types/inadimplencia";
import { buildTitulosExportPayload, tituloToExportRow } from "./exportTitulosExcel";

const sample: InadimplenciaTituloItem = {
  filial: "01",
  prefixo: "NF",
  numero: "123",
  parcela: "001",
  tipo: "NF",
  cliente_codigo: "000001",
  loja: "09",
  nome_cliente: "WEG SA",
  nome_reduzido: "WEG",
  data_emissao: "2026-01-10",
  data_vencimento_real: "2026-02-10",
  data_baixa: "2026-02-20",
  valor_titulo: 1500.5,
  pago_em_dia: false,
  dias_atraso: 10,
  faixa_atraso: { codigo: "ATRASO_6_A_15_DIAS", rotulo: "6 a 15 dias" },
};

describe("exportTitulosExcel", () => {
  it("mapeia linha do título", () => {
    expect(tituloToExportRow(sample)).toMatchObject({
      numero: "123",
      pago_em_dia: "Não",
      dias_atraso: 10,
      faixa_atraso: "6 a 15 dias",
      valor_titulo: 1500.5,
    });
  });

  it("monta payload tabular", () => {
    const payload = buildTitulosExportPayload([sample]);
    expect(payload.rows).toHaveLength(1);
    expect(payload.columns.map((column) => column.key)).toContain("data_baixa");
  });
});
