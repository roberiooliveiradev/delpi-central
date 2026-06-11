import type { Setor } from "../../data/api/transformometroApi";

export type SetorFormState = {
  setor_id: string;
  nome_setor: string;
  filiais: string[];
  status_setor: string;
};

export function emptySetorForm(defaultFilialId = "01"): SetorFormState {
  return {
    setor_id: "",
    nome_setor: "",
    filiais: [defaultFilialId],
    status_setor: "ativo",
  };
}

export function setorFormFromEntity(setor: Setor): SetorFormState {
  return {
    setor_id: setor.setor_id,
    nome_setor: setor.nome_setor,
    filiais: [...(setor.filiais ?? [])],
    status_setor: setor.status_setor ?? "ativo",
  };
}

export function payloadFromSetorForm(form: SetorFormState, editing: boolean) {
  const base = {
    nome_setor: form.nome_setor.trim(),
    filiais: form.filiais,
    status_setor: form.status_setor,
  };
  if (editing) {
    return base;
  }
  return {
    ...base,
    setor_id: form.setor_id.trim(),
  };
}
