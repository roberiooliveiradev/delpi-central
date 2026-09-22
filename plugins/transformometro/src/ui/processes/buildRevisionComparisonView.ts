/**
 * Frontend view-model for Redesign & Compare in Process Results.
 * Presentation-only — not a domain entity, DTO, or persistence authority.
 *
 * Reference resolution is domain data (`revisao_referencia_id`). Never invent a fallback.
 */

import type { Medicao, ProcessoComparativoItem, ProcessoInstancia, Revisao } from "../../data/api/transformometroApi";

export type ProvenanceLabel = "INFORMADO" | "CALCULADO" | "PROPOSTO" | "DADO_REVISAO";

export type ComparisonMode =
  | "no_instance"
  | "needs_instance_selection"
  | "no_revision"
  | "needs_revision_selection"
  | "baseline_only"
  | "pair"
  | "legacy_reference_missing"
  | "reference_not_in_scope";

export type RevisionComparisonContext = {
  mode: ComparisonMode;
  processId: string;
  instanceId: string | null;
  instance: ProcessoInstancia | null;
  selectedRevisionId: string | null;
  toBe: Revisao | null;
  asIs: Revisao | null;
  referenceRevisionId: string | null;
  scopedRevisoes: Revisao[];
};

export type MeasurementCompareRow = {
  id: string;
  label: string;
  asIsValue: number | null;
  toBeValue: number | null;
  delta: number | null;
  /** Presentation-only arithmetic when both sides exist with identical unit. */
  deltaKind: "CALCULATED_PRESENTATION" | null;
  unitHint: string;
};

const MEASUREMENT_FIELDS: Array<{
  id: keyof Medicao;
  label: string;
  unitHint: string;
}> = [
  { id: "volume_mensal", label: "Volume mensal", unitHint: "unid./mês" },
  { id: "tempo_medio_execucao_min", label: "Tempo médio de execução", unitHint: "min" },
  { id: "tempo_retrabalho_min", label: "Tempo de retrabalho", unitHint: "min" },
  { id: "percentual_retrabalho", label: "% retrabalho", unitHint: "%" },
  { id: "percentual_erro", label: "% erro", unitHint: "%" },
  { id: "quantidade_erros_mes", label: "Erros / mês", unitHint: "qtd" },
  { id: "custo_hora_mao_obra", label: "Custo hora mão de obra", unitHint: "R$/h" },
  { id: "custo_unitario_erro", label: "Custo unitário erro", unitHint: "R$" },
  { id: "custo_unitario_retrabalho", label: "Custo unitário retrabalho", unitHint: "R$" },
  { id: "custo_outros_desperdicios", label: "Outros desperdícios", unitHint: "R$" },
];

export function isBaselineCenario(cenarioTipo?: string | null): boolean {
  return String(cenarioTipo ?? "").trim().toLowerCase() === "baseline";
}

export function resolveContextInstanciaId(
  instancias: ProcessoInstancia[],
  selectedInstanciaId: string | null,
): { instanceId: string | null; requiresSelection: boolean } {
  if (instancias.length === 0) return { instanceId: null, requiresSelection: false };
  if (instancias.length === 1) return { instanceId: instancias[0]!.instancia_id, requiresSelection: false };
  return { instanceId: selectedInstanciaId, requiresSelection: true };
}

export function filterRevisoesByInstancia(
  revisoes: Revisao[],
  instanciaId: string | null,
): Revisao[] {
  if (!instanciaId) return [];
  const needle = instanciaId.toLowerCase();
  return revisoes.filter((row) => String(row.instancia_id ?? "").toLowerCase() === needle);
}

export function resolveContextRevisaoId(
  scopedRevisoes: Revisao[],
  selectedRevisaoId: string | null,
): { revisionId: string | null; requiresSelection: boolean } {
  if (scopedRevisoes.length === 0) return { revisionId: null, requiresSelection: false };
  if (scopedRevisoes.length === 1) return { revisionId: scopedRevisoes[0]!.revisao_id, requiresSelection: false };
  return { revisionId: selectedRevisaoId, requiresSelection: true };
}

/**
 * Resolve AS-IS / TO-BE from domain reference — never silent fallback.
 */
export function buildRevisionComparisonView(input: {
  processId: string;
  instancias: ProcessoInstancia[];
  revisoes: Revisao[];
  selectedInstanciaId: string | null;
  selectedRevisaoId: string | null;
}): RevisionComparisonContext {
  const { processId, instancias, revisoes, selectedInstanciaId, selectedRevisaoId } = input;

  if (instancias.length === 0) {
    return emptyContext(processId, "no_instance");
  }

  const { instanceId, requiresSelection: needsInstance } = resolveContextInstanciaId(
    instancias,
    selectedInstanciaId,
  );
  if (needsInstance && !instanceId) {
    return emptyContext(processId, "needs_instance_selection");
  }

  const instance = instancias.find((row) => row.instancia_id === instanceId) ?? null;
  const scopedRevisoes = filterRevisoesByInstancia(revisoes, instanceId);

  if (scopedRevisoes.length === 0) {
    return {
      mode: "no_revision",
      processId,
      instanceId,
      instance,
      selectedRevisionId: null,
      toBe: null,
      asIs: null,
      referenceRevisionId: null,
      scopedRevisoes,
    };
  }

  const { revisionId, requiresSelection: needsRevision } = resolveContextRevisaoId(
    scopedRevisoes,
    selectedRevisaoId,
  );
  if (needsRevision && !revisionId) {
    return {
      mode: "needs_revision_selection",
      processId,
      instanceId,
      instance,
      selectedRevisionId: null,
      toBe: null,
      asIs: null,
      referenceRevisionId: null,
      scopedRevisoes,
    };
  }

  const toBe = scopedRevisoes.find((row) => row.revisao_id === revisionId) ?? null;
  if (!toBe) {
    return {
      mode: "needs_revision_selection",
      processId,
      instanceId,
      instance,
      selectedRevisionId: null,
      toBe: null,
      asIs: null,
      referenceRevisionId: null,
      scopedRevisoes,
    };
  }

  const rawRef = toBe.revisao_referencia_id;
  const referenceRevisionId =
    typeof rawRef === "string" && rawRef.trim() ? rawRef.trim() : null;

  if (!referenceRevisionId) {
    if (isBaselineCenario(toBe.cenario_tipo)) {
      return {
        mode: "baseline_only",
        processId,
        instanceId,
        instance,
        selectedRevisionId: toBe.revisao_id,
        toBe,
        asIs: toBe,
        referenceRevisionId: null,
        scopedRevisoes,
      };
    }
    return {
      mode: "legacy_reference_missing",
      processId,
      instanceId,
      instance,
      selectedRevisionId: toBe.revisao_id,
      toBe,
      asIs: null,
      referenceRevisionId: null,
      scopedRevisoes,
    };
  }

  const asIs =
    scopedRevisoes.find((row) => row.revisao_id === referenceRevisionId) ?? null;
  if (!asIs) {
    return {
      mode: "reference_not_in_scope",
      processId,
      instanceId,
      instance,
      selectedRevisionId: toBe.revisao_id,
      toBe,
      asIs: null,
      referenceRevisionId,
      scopedRevisoes,
    };
  }

  return {
    mode: "pair",
    processId,
    instanceId,
    instance,
    selectedRevisionId: toBe.revisao_id,
    toBe,
    asIs,
    referenceRevisionId,
    scopedRevisoes,
  };
}

function emptyContext(processId: string, mode: ComparisonMode): RevisionComparisonContext {
  return {
    mode,
    processId,
    instanceId: null,
    instance: null,
    selectedRevisionId: null,
    toBe: null,
    asIs: null,
    referenceRevisionId: null,
    scopedRevisoes: [],
  };
}

export function provenanceForRevisionRole(
  role: "as_is" | "to_be",
  revisao: Revisao | null,
): ProvenanceLabel {
  if (!revisao) return "DADO_REVISAO";
  if (role === "to_be" && !isBaselineCenario(revisao.cenario_tipo)) return "PROPOSTO";
  return "INFORMADO";
}

export function provenanceLabelText(kind: ProvenanceLabel): string {
  switch (kind) {
    case "INFORMADO":
      return "INFORMADO";
    case "CALCULADO":
      return "CALCULADO";
    case "PROPOSTO":
      return "PROPOSTO";
    default:
      return "Dado da revisão";
  }
}

export function buildMeasurementComparisonRows(
  asIs: Medicao | null,
  toBe: Medicao | null,
): MeasurementCompareRow[] {
  return MEASUREMENT_FIELDS.map((field) => {
    const asIsValue = readNumber(asIs, field.id);
    const toBeValue = readNumber(toBe, field.id);
    const both = asIsValue != null && toBeValue != null;
    return {
      id: String(field.id),
      label: field.label,
      asIsValue,
      toBeValue,
      delta: both ? roundDelta(toBeValue - asIsValue) : null,
      deltaKind: both ? "CALCULATED_PRESENTATION" : null,
      unitHint: field.unitHint,
    };
  });
}

function readNumber(medicao: Medicao | null, key: keyof Medicao): number | null {
  if (!medicao) return null;
  const raw = medicao[key];
  if (typeof raw === "number" && Number.isFinite(raw)) return raw;
  return null;
}

function roundDelta(value: number): number {
  return Math.round(value * 10000) / 10000;
}

export function findComparativoItem(
  items: ProcessoComparativoItem[],
  revisaoId: string | null,
): ProcessoComparativoItem | null {
  if (!revisaoId) return null;
  return items.find((row) => row.revisao_id === revisaoId) ?? null;
}

export function filterComparativoByRevisoes(
  items: ProcessoComparativoItem[],
  scopedRevisoes: Revisao[],
): ProcessoComparativoItem[] {
  const allowed = new Set(scopedRevisoes.map((row) => row.revisao_id));
  return items.filter((row) => allowed.has(row.revisao_id));
}

/** Benefit totals shown as CALCULADO — from comparison contract, not field observation. */
export const CALCULATED_BENEFIT_KEYS = [
  "economia_bruta",
  "economia_liquida_mes",
  "horas_economizadas_mes",
  "ganho_capacidade",
  "investimento_total_mes",
  "delta_volume",
] as const;
