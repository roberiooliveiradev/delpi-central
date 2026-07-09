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

type SetorDisplayRef = Pick<ProcessoInstanciaSetor, "nome_setor">;

type FilialDisplayRef = {
  nome_filial?: string;
};

export function formatSetorDisplayName(setor: SetorDisplayRef | null | undefined): string {
  const name = (setor?.nome_setor ?? "").trim();
  return name || "—";
}

export function formatFilialDisplayName(filial: FilialDisplayRef | null | undefined): string {
  const name = (filial?.nome_filial ?? "").trim();
  return name || "—";
}

export function formatInstanciaSetoresDisplay(
  instancia: Pick<ProcessoInstanciaSetor, "nome_setor"> & {
    setores?: ProcessoInstanciaSetor[];
    codigo_setor?: string;
    setor_id?: string;
    nome_setor?: string;
  }
): string {
  if (instancia.setores?.length) {
    const names = instancia.setores
      .map((setor) => formatSetorDisplayName(setor))
      .filter((name) => name !== "—");
    return names.length ? names.join("; ") : "—";
  }
  return formatSetorDisplayName(instancia);
}

export function formatInstanciaUnidadeDisplay(
  instancia: FilialDisplayRef & {
    todas_filiais_ativas?: boolean;
    codigo_filial?: string;
    filial_id?: string | null;
  },
  activeFilialCount = 1
): string {
  if (instancia.todas_filiais_ativas) {
    const suffix =
      activeFilialCount > 1 ? ` (${activeFilialCount} unidades ativas)` : "";
    return `Todas as unidades ativas${suffix}`;
  }
  return formatFilialDisplayName(instancia);
}

export function formatProcessoEscopoRead(
  processo: Processo,
  activeFilialCount: number
): { unidades: string; departamentos: string } {
  const setores = processo.setores ?? [];
  const departamentos =
    setores.length > 0
      ? setores.map((setor) => formatSetorDisplayName(setor)).join("; ")
      : "—";

  if (processo.todas_filiais_ativas) {
    return {
      unidades: formatInstanciaUnidadeDisplay(
        { todas_filiais_ativas: true },
        activeFilialCount
      ),
      departamentos,
    };
  }

  const filiais = processo.filiais ?? [];
  const unidades =
    filiais.length > 0
      ? filiais.map((filial) => formatFilialDisplayName(filial)).join("; ")
      : "—";

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
