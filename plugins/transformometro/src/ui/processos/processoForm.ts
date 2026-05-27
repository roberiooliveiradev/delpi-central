import type { Processo } from "../../data/api/transformometroApi";

export type ProcessoFormState = {
  nome_processo: string;
  filial_id: string;
  setor_id: string;
  status_processo: string;
  descricao_processo: string;
  gestor_responsavel: string;
  objetivo_processo: string;
  familia_processo: string;
  agrupador_ferramenta: string;
};

export function emptyProcessoForm(): ProcessoFormState {
  return {
    nome_processo: "",
    filial_id: "01",
    setor_id: "engenharia",
    status_processo: "ativo",
    descricao_processo: "",
    gestor_responsavel: "",
    objetivo_processo: "",
    familia_processo: "",
    agrupador_ferramenta: "",
  };
}

export function processoFormFromEntity(processo: Processo): ProcessoFormState {
  return {
    nome_processo: processo.nome_processo ?? "",
    filial_id: processo.filial_id ?? "01",
    setor_id: processo.setor_id ?? "",
    status_processo: processo.status_processo ?? "ativo",
    descricao_processo: processo.descricao_processo ?? "",
    gestor_responsavel: processo.gestor_responsavel ?? "",
    objetivo_processo: processo.objetivo_processo ?? "",
    familia_processo: processo.familia_processo ?? "",
    agrupador_ferramenta: processo.agrupador_ferramenta ?? "",
  };
}

export function payloadFromProcessoForm(form: ProcessoFormState): Partial<Processo> {
  return {
    nome_processo: form.nome_processo.trim(),
    filial_id: form.filial_id,
    setor_id: form.setor_id,
    status_processo: form.status_processo,
    descricao_processo: form.descricao_processo.trim() || undefined,
    gestor_responsavel: form.gestor_responsavel.trim() || undefined,
    objetivo_processo: form.objetivo_processo.trim() || undefined,
    familia_processo: form.familia_processo.trim() || undefined,
    agrupador_ferramenta: form.agrupador_ferramenta.trim() || undefined,
  };
}
