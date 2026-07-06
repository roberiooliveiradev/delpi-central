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

/** Campos mestre disponíveis na listagem (sem instâncias, diagrama ou revisões). */
export function computeProcessoMasterCompletion(processo: Processo): FormCompletion {
  const items: CompletionItem[] = [
    { id: "gestor", label: "Gestor", done: filled(processo.gestor_responsavel) },
    { id: "objetivo", label: "Objetivo", done: filled(processo.objetivo_processo) },
    { id: "descricao", label: "Descrição", done: filled(processo.descricao_processo) },
    { id: "familia", label: "Família", done: filled(processo.familia_processo) },
  ];
  return buildCompletion(items);
}

export type ProcessoSetupCompletionInput = {
  processo: Processo;
  instanciaCount: number;
  diagramNodeCount: number;
  decompositionNodeCount: number;
  revisoes: Revisao[];
  comparativoItems?: ProcessoComparativoItem[];
};

function hasCenario(revisoes: Revisao[], cenario: string): boolean {
  const needle = cenario.toLowerCase();
  return revisoes.some((row) => (row.cenario_tipo ?? "").toLowerCase() === needle);
}

function hasMedicao(comparativoItems: ProcessoComparativoItem[] | undefined): boolean {
  if (!comparativoItems?.length) return false;
  return comparativoItems.some((row) => (row.meses_com_dados ?? 0) > 0);
}

/** Checklist completo do processo-mestre (padrão quality-action-plans / Kaizen). */
export function computeProcessoSetupCompletion(input: ProcessoSetupCompletionInput): FormCompletion {
  const { processo, instanciaCount, diagramNodeCount, decompositionNodeCount, revisoes, comparativoItems } = input;
  const items: CompletionItem[] = [
    { id: "gestor", label: "Gestor", done: filled(processo.gestor_responsavel) },
    { id: "objetivo", label: "Objetivo", done: filled(processo.objetivo_processo) },
    { id: "descricao", label: "Descrição", done: filled(processo.descricao_processo) },
    { id: "familia", label: "Família", done: filled(processo.familia_processo) },
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
      done: hasCenario(revisoes, "baseline"),
    },
    {
      id: "melhoria",
      label: "Melhoria",
      done: hasCenario(revisoes, "melhoria"),
    },
    {
      id: "medicao",
      label: "Medição",
      done: hasMedicao(comparativoItems),
    },
  ];
  return buildCompletion(items);
}
