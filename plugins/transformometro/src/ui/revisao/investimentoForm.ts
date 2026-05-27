import type { Investimento, OptionsData } from "../../data/api/transformometroApi";
import { optionalDateField, toDateInputValue } from "../../utils/dateInputs";

export type InvestimentoFormState = {
  tipo_investimento: string;
  descricao_item: string;
  quantidade: number;
  valor_unitario: number;
  recorrencia: string;
  categoria_investimento: string;
  data_investimento: string;
  meses_vigencia: string;
};

export function emptyInvestimentoForm(options?: OptionsData): InvestimentoFormState {
  return {
    tipo_investimento: options?.tipo_investimento[0] ?? "unico",
    descricao_item: "",
    quantidade: 1,
    valor_unitario: 0,
    recorrencia: options?.recorrencias[0] ?? "unico",
    categoria_investimento: "",
    data_investimento: "",
    meses_vigencia: "",
  };
}

export function investimentoFormFromEntity(inv: Investimento): InvestimentoFormState {
  return {
    tipo_investimento: inv.tipo_investimento,
    descricao_item: inv.descricao_item,
    quantidade: inv.quantidade,
    valor_unitario: inv.valor_unitario,
    recorrencia: inv.recorrencia,
    categoria_investimento: inv.categoria_investimento ?? "",
    data_investimento: toDateInputValue(inv.data_investimento),
    meses_vigencia: inv.meses_vigencia != null ? String(inv.meses_vigencia) : "",
  };
}

export function payloadFromInvestimentoForm(form: InvestimentoFormState) {
  return {
    tipo_investimento: form.tipo_investimento,
    descricao_item: form.descricao_item.trim(),
    quantidade: form.quantidade,
    valor_unitario: form.valor_unitario,
    recorrencia: form.recorrencia,
    categoria_investimento: form.categoria_investimento.trim() || undefined,
    data_investimento: optionalDateField(form.data_investimento),
    meses_vigencia: form.meses_vigencia
      ? Number.parseInt(form.meses_vigencia, 10)
      : undefined,
  };
}
