export const MELHORIA_FASE_OPTIONS = [
  { value: "planejado", label: "Planejado" },
  { value: "piloto", label: "Em piloto" },
  { value: "implantado", label: "Implantado" },
  { value: "encerrado", label: "Encerrado" },
] as const;

export const MELHORIA_PRIORIDADE_OPTIONS = [
  { value: "baixa", label: "Baixa" },
  { value: "media", label: "Média" },
  { value: "alta", label: "Alta" },
] as const;

export type MelhoriaFormFields = {
  resumo_melhoria?: string;
  responsavel_local?: string;
  fase_melhoria?: string;
  data_alvo_go_live?: string;
  prioridade?: string;
};

export function melhoriaFieldsFromInstancia(row: {
  resumo_melhoria?: string | null;
  responsavel_local?: string | null;
  fase_melhoria?: string | null;
  data_alvo_go_live?: string | null;
  prioridade?: string | null;
}): MelhoriaFormFields {
  return {
    resumo_melhoria: row.resumo_melhoria ?? "",
    responsavel_local: row.responsavel_local ?? "",
    fase_melhoria: row.fase_melhoria ?? "planejado",
    data_alvo_go_live: row.data_alvo_go_live?.slice(0, 10) ?? "",
    prioridade: row.prioridade ?? "media",
  };
}

export function melhoriaPayloadFromForm(fields: MelhoriaFormFields) {
  return {
    resumo_melhoria: fields.resumo_melhoria?.trim() || undefined,
    responsavel_local: fields.responsavel_local?.trim() || undefined,
    fase_melhoria: fields.fase_melhoria || "planejado",
    data_alvo_go_live: fields.data_alvo_go_live?.trim() || undefined,
    prioridade: fields.prioridade || "media",
  };
}

export function labelMelhoriaFase(value?: string | null): string {
  return MELHORIA_FASE_OPTIONS.find((item) => item.value === value)?.label ?? value ?? "—";
}

export function labelMelhoriaPrioridade(value?: string | null): string {
  return MELHORIA_PRIORIDADE_OPTIONS.find((item) => item.value === value)?.label ?? value ?? "—";
}
