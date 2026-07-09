import type { Setor } from "../../data/api/transformometroApi";

export type SetorFormState = {
  codigo_setor: string;
  nome_setor: string;
  filiais: string[];
  status_setor: string;
};

export function emptySetorForm(defaultFilialId = "01"): SetorFormState {
  return {
    codigo_setor: "",
    nome_setor: "",
    filiais: [defaultFilialId],
    status_setor: "ativo",
  };
}

export function setorFormFromEntity(setor: Setor): SetorFormState {
  return {
    codigo_setor: setor.codigo_setor ?? "",
    nome_setor: setor.nome_setor,
    filiais: [...(setor.filiais ?? [])],
    status_setor: setor.status_setor ?? "ativo",
  };
}

export function payloadFromSetorForm(form: SetorFormState) {
  return {
    codigo_setor: form.codigo_setor.trim(),
    nome_setor: form.nome_setor.trim(),
    filiais: form.filiais,
    status_setor: form.status_setor,
  };
}

export function createPayloadFromSetorForm(form: SetorFormState) {
  const payload = payloadFromSetorForm(form);
  return {
    setor_id: payload.codigo_setor,
    nome_setor: payload.nome_setor,
    filiais: payload.filiais,
    status_setor: payload.status_setor,
  };
}
