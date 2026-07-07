import type { Processo, ProcessoComparativoItem, Revisao } from "../data/api/transformometroApi";

export type CompletionItem = { id: string; label: string; done: boolean };

export type FormCompletion = {
  percent: number;
  done: number;
  total: number;
  items: CompletionItem[];
};

function filled(value: string | null | undefined): boolean {
  return typeof value === "string" && value.trim().length > 0;
}

function buildCompletion(items: CompletionItem[]): FormCompletion {
  const done = items.filter((item) => item.done).length;
  const percent = items.length === 0 ? 0 : Math.round((done / items.length) * 100);
  return { percent, done, total: items.length, items };
}

export type ProcessoSetupCompletionInput = {
  processo: Processo;
  instanciaCount: number;
  diagramNodeCount: number;
  decompositionNodeCount: number;
  revisoes: Revisao[];
  comparativoItems?: ProcessoComparativoItem[];
  /** Quando informados (ex.: listagem via setup_stats), substituem inferência por revisões/comparativo. */
  hasBaseline?: boolean;
  hasMelhoria?: boolean;
  hasMedicao?: boolean;
};

function hasCenario(revisoes: Revisao[], cenario: string): boolean {
  const needle = cenario.toLowerCase();
  return revisoes.some((row) => (row.cenario_tipo ?? "").toLowerCase() === needle);
}

function hasMedicao(comparativoItems: ProcessoComparativoItem[] | undefined): boolean {
  if (!comparativoItems?.length) return false;
  return comparativoItems.some((row) => (row.meses_com_dados ?? 0) > 0);
}

function resolveCenarioDone(
  input: ProcessoSetupCompletionInput,
  cenario: "baseline" | "melhoria"
): boolean {
  if (cenario === "baseline" && input.hasBaseline !== undefined) {
    return input.hasBaseline;
  }
  if (cenario === "melhoria" && input.hasMelhoria !== undefined) {
    return input.hasMelhoria;
  }
  return hasCenario(input.revisoes, cenario);
}

function resolveMedicaoDone(input: ProcessoSetupCompletionInput): boolean {
  if (input.hasMedicao !== undefined) {
    return input.hasMedicao;
  }
  return hasMedicao(input.comparativoItems);
}

/** Checklist completo do processo-mestre (padrão quality-action-plans / Kaizen). */
export function computeProcessoSetupCompletion(input: ProcessoSetupCompletionInput): FormCompletion {
  const { processo, instanciaCount, diagramNodeCount, decompositionNodeCount } = input;
  const items: CompletionItem[] = [
    { id: "gestor", label: "Gestor", done: filled(processo.gestor_responsavel) },
    { id: "objetivo", label: "Objetivo", done: filled(processo.objetivo_processo) },
    { id: "descricao", label: "Descrição", done: filled(processo.descricao_processo) },
    { id: "familia", label: "Família", done: filled(processo.familia_processo) },
    {
      id: "escopo",
      label: "Unidades e deptos.",
      done:
        Boolean(processo.todas_filiais_ativas && (processo.setor_ids?.length ?? 0) > 0) ||
        Boolean((processo.filial_ids?.length ?? 0) > 0 && (processo.setor_ids?.length ?? 0) > 0),
    },
    {
      id: "instancias",
      label: "Melhorias",
      done: instanciaCount > 0,
    },
    {
      id: "mapeamento",
      label: "Mapeamento",
      done: decompositionNodeCount > 0,
    },
    {
      id: "diagrama",
      label: "Diagrama macro",
      done: diagramNodeCount > 0,
    },
    {
      id: "baseline",
      label: "Baseline",
      done: resolveCenarioDone(input, "baseline"),
    },
    {
      id: "melhoria",
      label: "Melhoria",
      done: resolveCenarioDone(input, "melhoria"),
    },
    {
      id: "medicao",
      label: "Medição",
      done: resolveMedicaoDone(input),
    },
  ];
  return buildCompletion(items);
}

/** Listagem — usa setup_stats retornado pela API (mesmo checklist do detalhe). */
export function computeProcessoListCompletion(processo: Processo): FormCompletion {
  const stats = processo.setup_stats;
  return computeProcessoSetupCompletion({
    processo,
    instanciaCount: stats?.instancia_count ?? 0,
    diagramNodeCount: stats?.diagram_node_count ?? 0,
    decompositionNodeCount: stats?.decomposition_node_count ?? 0,
    revisoes: [],
    hasBaseline: stats?.has_baseline,
    hasMelhoria: stats?.has_melhoria,
    hasMedicao: stats?.has_medicao,
  });
}
