import type { RecursoCompartilhado } from "../../data/api/transformometroApi";
import { optionalDateField, toDateInputValue } from "../../utils/dateInputs";

export type RecursoCatalogFormState = {
  nome_recurso: string;
  categoria_recurso: string;
  fornecedor: string;
  tipo_custo: string;
  recorrencia: string;
  criterio_rateio: string;
  status_recurso: string;
  centro_custo: string;
  data_inicio_vigencia: string;
  data_fim_vigencia: string;
  observacoes: string;
};

export function emptyRecursoForm(): RecursoCatalogFormState {
  return {
    nome_recurso: "",
    categoria_recurso: "",
    fornecedor: "",
    tipo_custo: "assinatura",
    recorrencia: "mensal",
    criterio_rateio: "igualitario",
    status_recurso: "ativo",
    centro_custo: "",
    data_inicio_vigencia: "",
    data_fim_vigencia: "",
    observacoes: "",
  };
}

export function recursoFormFromEntity(r: RecursoCompartilhado): RecursoCatalogFormState {
  return {
    nome_recurso: r.nome_recurso,
    categoria_recurso: r.categoria_recurso ?? "",
    fornecedor: r.fornecedor ?? "",
    tipo_custo: r.tipo_custo,
    recorrencia: r.recorrencia,
    criterio_rateio: r.criterio_rateio,
    status_recurso: r.status_recurso,
    centro_custo: r.centro_custo ?? "",
    data_inicio_vigencia: toDateInputValue(r.data_inicio_vigencia),
    data_fim_vigencia: toDateInputValue(r.data_fim_vigencia),
    observacoes: r.observacoes ?? "",
  };
}

export function payloadFromRecursoForm(form: RecursoCatalogFormState) {
  return {
    nome_recurso: form.nome_recurso.trim(),
    tipo_custo: form.tipo_custo,
    recorrencia: form.recorrencia,
    criterio_rateio: form.criterio_rateio,
    status_recurso: form.status_recurso,
    categoria_recurso: form.categoria_recurso.trim() || undefined,
    fornecedor: form.fornecedor.trim() || undefined,
    centro_custo: form.centro_custo.trim() || undefined,
    observacoes: form.observacoes.trim() || undefined,
    data_inicio_vigencia: optionalDateField(form.data_inicio_vigencia),
    data_fim_vigencia: optionalDateField(form.data_fim_vigencia),
  };
}
