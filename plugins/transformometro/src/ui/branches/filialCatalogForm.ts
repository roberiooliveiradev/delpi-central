import type { Filial } from "../../data/api/transformometroApi";

export type FilialFormState = {
  codigo_filial: string;
  nome_filial: string;
  status_filial: string;
};

export function emptyFilialForm(): FilialFormState {
  return {
    codigo_filial: "",
    nome_filial: "",
    status_filial: "ativo",
  };
}

export function filialFormFromEntity(filial: Filial): FilialFormState {
  return {
    codigo_filial: filial.codigo_filial ?? "",
    nome_filial: filial.nome_filial,
    status_filial: filial.status_filial ?? "ativo",
  };
}

export function payloadFromFilialForm(form: FilialFormState, editing: boolean) {
  const base = {
    nome_filial: form.nome_filial.trim(),
    status_filial: form.status_filial,
  };
  if (editing) {
    return base;
  }
  return {
    ...base,
    codigo_filial: form.codigo_filial.trim(),
  };
}
