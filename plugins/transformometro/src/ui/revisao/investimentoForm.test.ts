import { describe, expect, it } from "vitest";

import {
  emptyInvestimentoForm,
  investimentoFormFromEntity,
  investimentoFormTotal,
  parseInvestimentoNumber,
  payloadFromInvestimentoForm,
} from "./investimentoForm";
import type { Investimento, OptionsData } from "../../data/api/transformometroApi";

const options: OptionsData = {
  tipo_investimento: ["fixo", "variavel"],
  recorrencias: ["unico", "mensal"],
  categorias: ["software", "horas_internas"],
} as OptionsData;

describe("investimentoForm", () => {
  it("aceita valor unitário decimal no payload", () => {
    const form = {
      ...emptyInvestimentoForm(options),
      descricao_item: "Horas internas",
      quantidade: "120",
      valor_unitario: "38.61",
    };
    const payload = payloadFromInvestimentoForm(form);
    expect(payload.quantidade).toBe(120);
    expect(payload.valor_unitario).toBeCloseTo(38.61);
    expect(investimentoFormTotal(form)).toBeCloseTo(4633.2);
  });

  it("aceita vírgula como separador decimal na digitação", () => {
    expect(parseInvestimentoNumber("38,61")).toBeCloseTo(38.61);
  });

  it("hidrata formulário a partir da entidade sem perder casas decimais", () => {
    const inv = {
      investimento_id: "1",
      revisao_id: "r1",
      tipo_investimento: "fixo",
      descricao_item: "Horas",
      quantidade: 120,
      valor_unitario: 38.61,
      valor_total: 4633.2,
      recorrencia: "unico",
      categoria_investimento: "horas_internas",
      data_investimento: null,
      meses_vigencia: null,
    } as Investimento;
    const form = investimentoFormFromEntity(inv);
    expect(form.valor_unitario).toBe("38.61");
    expect(form.quantidade).toBe("120");
  });

  it("rejeita valor unitário inválido", () => {
    expect(() =>
      payloadFromInvestimentoForm({
        ...emptyInvestimentoForm(options),
        descricao_item: "x",
        valor_unitario: "abc",
      })
    ).toThrow(/valor unitário/i);
  });
});
