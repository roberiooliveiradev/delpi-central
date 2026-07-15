import { describe, expect, it } from "vitest";

import type { InadimplenciaClienteItem } from "../types/inadimplencia";
import { buildClientesExportPayload, clienteToExportRow } from "./exportClientesExcel";

const sample: InadimplenciaClienteItem = {
  cliente_codigo: "000001",
  loja: "09",
  nome_cliente: "WEG SA",
  nome_reduzido: "WEG",
  total_titulos: 10,
  titulos_em_dia: 8,
  titulos_atraso: 2,
  valor_total: 1000.5,
  valor_atraso: 200.25,
  percentual_em_dia_qtd: 80.1234,
  percentual_em_dia_valor: 79.9876,
};

describe("exportClientesExcel", () => {
  it("mapeia linha com percentuais arredondados", () => {
    expect(clienteToExportRow(sample)).toMatchObject({
      cliente_codigo: "000001",
      loja: "09",
      percentual_em_dia_qtd: 80.12,
      percentual_em_dia_valor: 79.99,
      valor_atraso: 200.25,
    });
  });

  it("monta payload tabular para Excel", () => {
    const payload = buildClientesExportPayload([sample]);
    expect(payload.columns.map((column) => column.key)).toContain("valor_atraso");
    expect(payload.rows).toHaveLength(1);
  });
});
