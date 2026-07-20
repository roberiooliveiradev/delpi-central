import type { Investimento, OptionsData } from "../../data/api/transformometroApi";
import { optionalDateField, toDateInputValue } from "../../utils/dateInputs";

export type InvestimentoFormState = {
  tipo_investimento: string;
  descricao_item: string;
  /** Texto do input number (ponto decimal). */
  quantidade: string;
  /** Texto do input number (ponto decimal). */
  valor_unitario: string;
  recorrencia: string;
  categoria_investimento: string;
  data_investimento: string;
  meses_vigencia: string;
};

function numberToInputValue(value: number | null | undefined, fallback = "0"): string {
  if (value == null || Number.isNaN(value)) return fallback;
  return String(value);
}

export function emptyInvestimentoForm(options?: OptionsData): InvestimentoFormState {
  return {
    tipo_investimento: options?.tipo_investimento[0] ?? "fixo",
    descricao_item: "",
    quantidade: "1",
    valor_unitario: "0",
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
    quantidade: numberToInputValue(inv.quantidade, "1"),
    valor_unitario: numberToInputValue(inv.valor_unitario, "0"),
    recorrencia: inv.recorrencia,
    categoria_investimento: inv.categoria_investimento ?? "",
    data_investimento: toDateInputValue(inv.data_investimento),
    meses_vigencia: inv.meses_vigencia != null ? String(inv.meses_vigencia) : "",
  };
}

export function parseInvestimentoNumber(raw: string): number | null {
  const normalized = raw.trim().replace(",", ".");
  if (!normalized) return null;
  const value = Number.parseFloat(normalized);
  return Number.isFinite(value) ? value : null;
}

export function investimentoFormTotal(form: InvestimentoFormState): number | null {
  const quantidade = parseInvestimentoNumber(form.quantidade);
  const unitario = parseInvestimentoNumber(form.valor_unitario);
  if (quantidade == null || unitario == null) return null;
  return quantidade * unitario;
}

export function payloadFromInvestimentoForm(form: InvestimentoFormState) {
  const quantidade = parseInvestimentoNumber(form.quantidade);
  const valor_unitario = parseInvestimentoNumber(form.valor_unitario);
  if (quantidade == null || quantidade < 0) {
    throw new Error("Informe uma quantidade válida.");
  }
  if (valor_unitario == null || valor_unitario < 0) {
    throw new Error("Informe um valor unitário válido.");
  }
  const mesesRaw = form.meses_vigencia.trim();
  let meses_vigencia: number | undefined;
  if (mesesRaw) {
    const meses = Number.parseInt(mesesRaw, 10);
    if (!Number.isFinite(meses) || meses < 1) {
      throw new Error("Meses de vigência deve ser um inteiro ≥ 1.");
    }
    meses_vigencia = meses;
  }
  return {
    tipo_investimento: form.tipo_investimento,
    descricao_item: form.descricao_item.trim(),
    quantidade,
    valor_unitario,
    recorrencia: form.recorrencia,
    categoria_investimento: form.categoria_investimento.trim() || undefined,
    data_investimento: optionalDateField(form.data_investimento),
    meses_vigencia,
  };
}
