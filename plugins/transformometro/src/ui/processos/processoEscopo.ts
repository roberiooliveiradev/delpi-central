import type { OptionsData, Processo, ProcessoInstanciaSetor } from "../../data/api/transformometroApi";
import { filterSetoresByFilial } from "../../utils/setores";

export type ProcessoEscopoState = {
  todas_filiais_ativas: boolean;
  filial_ids: string[];
  setor_ids: string[];
};

export function emptyProcessoEscopo(_defaultFilialId = "01"): ProcessoEscopoState {
  return {
    todas_filiais_ativas: false,
    filial_ids: [],
    setor_ids: [],
  };
}

export function processoEscopoFromEntity(processo: Processo): ProcessoEscopoState {
  return {
    todas_filiais_ativas: Boolean(processo.todas_filiais_ativas),
    filial_ids: processo.filial_ids?.length
      ? [...processo.filial_ids]
      : processo.filial_id
        ? [processo.filial_id]
        : [],
    setor_ids: processo.setor_ids?.length
      ? [...processo.setor_ids]
      : processo.setor_id
        ? [processo.setor_id]
        : [],
  };
}

export function hasProcessoEscopo(escopo: ProcessoEscopoState | null | undefined): boolean {
  if (!escopo) return false;
  if (!escopo.setor_ids.length) return false;
  return escopo.todas_filiais_ativas || escopo.filial_ids.length > 0;
}

export function processoEscopoPayload(escopo: ProcessoEscopoState): Partial<Processo> {
  return {
    todas_filiais_ativas: escopo.todas_filiais_ativas,
    filial_ids: escopo.todas_filiais_ativas ? [] : escopo.filial_ids,
    setor_ids: escopo.setor_ids,
  };
}

export function defaultSetorIdsForFilial(
  setores: OptionsData["setores"],
  filialId: string
): string[] {
  const first = filterSetoresByFilial(setores, filialId)[0];
  return first ? [first.id] : [];
}

export function formatProcessoEscopoRead(
  processo: Processo,
  activeFilialCount: number
): { unidades: string; departamentos: string } {
  const setores = processo.setores ?? [];
  const departamentos =
    setores.length > 0
      ? setores
          .map((setor: ProcessoInstanciaSetor) =>
            `${setor.codigo_setor ?? setor.setor_id} — ${setor.nome_setor ?? ""}`.trim()
          )
          .join("; ")
      : processo.setor_ids?.join(", ") ?? "—";

  if (processo.todas_filiais_ativas) {
    const suffix =
      activeFilialCount > 1 ? ` (${activeFilialCount} unidades ativas)` : "";
    return {
      unidades: `Todas as unidades ativas${suffix}`,
      departamentos,
    };
  }

  const filiais = processo.filiais ?? [];
  const unidades =
    filiais.length > 0
      ? filiais
          .map((filial) => `${filial.codigo_filial ?? filial.filial_id} — ${filial.nome_filial ?? ""}`.trim())
          .join("; ")
      : processo.filial_ids?.join(", ") ?? "—";

  return { unidades, departamentos };
}

export function setoresDisponiveisForEscopo(
  options: OptionsData,
  escopo: ProcessoEscopoState
): OptionsData["setores"] {
  if (escopo.todas_filiais_ativas) return options.setores;
  if (escopo.filial_ids.length === 0) return [];
  const seen = new Set<string>();
  const out: OptionsData["setores"] = [];
  for (const filialId of escopo.filial_ids) {
    for (const setor of filterSetoresByFilial(options.setores, filialId)) {
      const key = setor.id.toLowerCase();
      if (!seen.has(key)) {
        seen.add(key);
        out.push(setor);
      }
    }
  }
  return out;
}
