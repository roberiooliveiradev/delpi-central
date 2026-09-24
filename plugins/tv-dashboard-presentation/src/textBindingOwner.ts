/**
 * Owner canônico do binding textual = o mesmo do paint
 * (`resolveTextBlockDisplayRuns`: contentRuns.dataRef vence textProjection).
 *
 * O painel «Campo dinâmico» deve ler/escrever esse owner. Ao escrever um campo
 * único, consolida dataRefs → textProjection e remove dataRefs contraditórios.
 */

import type {
  ComunicadoContentRun,
  ComunicadoTextDataRef,
  ComunicadoTextProjection,
} from "./comunicadoTypes";
import { plainTextFromContentRuns } from "./comunicadoContentRuns";

function prefixFromStaticLabel(label: string | undefined | null): string | undefined {
  const trimmedEnd = String(label ?? "").replace(/\s+$/u, "");
  if (!trimmedEnd) return undefined;
  if (/[\s:：\-–—(/[{]$/u.test(trimmedEnd)) return trimmedEnd;
  return `${trimmedEnd} `;
}

export type TextBindingOwnerKind = "contentRuns" | "textProjection" | "none";

export type TextBoundBlockSlice = {
  content?: string;
  contentRuns?: ComunicadoContentRun[];
  textProjection?: ComunicadoTextProjection;
};

export function listBoundDataRefs(
  block: Pick<TextBoundBlockSlice, "contentRuns">,
): Array<{ runIndex: number; dataRef: ComunicadoTextDataRef }> {
  const out: Array<{ runIndex: number; dataRef: ComunicadoTextDataRef }> = [];
  (block.contentRuns ?? []).forEach((run, runIndex) => {
    const field = run.dataRef?.field?.trim();
    if (!field || !run.dataRef) return;
    out.push({ runIndex, dataRef: run.dataRef });
  });
  return out;
}

export function resolveTextBindingOwner(block: TextBoundBlockSlice): TextBindingOwnerKind {
  if (listBoundDataRefs(block).length > 0) return "contentRuns";
  if (block.textProjection?.field?.trim()) return "textProjection";
  return "none";
}

/** Texto estático leading (antes do 1º dataRef) — vira prefixo na consolidação. */
export function staticPrefixFromContentRuns(
  contentRuns: ComunicadoContentRun[] | undefined,
): string | undefined {
  if (!contentRuns?.length) return undefined;
  const leading: ComunicadoContentRun[] = [];
  for (const run of contentRuns) {
    if (run.dataRef?.field?.trim()) break;
    leading.push(run);
  }
  if (leading.length === 0) return undefined;
  const joined = plainTextFromContentRuns(leading);
  return prefixFromStaticLabel(joined) ?? (joined || undefined);
}

function dataRefToProjectionStub(ref: ComunicadoTextDataRef): ComunicadoTextProjection {
  const projection: ComunicadoTextProjection = { field: ref.field.trim() };
  if (ref.aggregation) projection.aggregation = ref.aggregation;
  if (ref.format) projection.format = ref.format;
  if (ref.displayFormat) projection.displayFormat = ref.displayFormat;
  if (ref.decimalPlaces != null) projection.decimalPlaces = ref.decimalPlaces;
  if (ref.colorRules?.length) projection.colorRules = [...ref.colorRules];
  return projection;
}

/**
 * Projeção efetiva para o painel Campo — espelha o que o paint usa.
 * Com vários dataRefs distintos, usa o primeiro (UI single-field); escrever consolida.
 */
export function readEffectiveTextProjection(block: TextBoundBlockSlice): ComunicadoTextProjection {
  const bound = listBoundDataRefs(block);
  if (bound.length > 0) {
    const first = dataRefToProjectionStub(bound[0]!.dataRef);
    const prefix = staticPrefixFromContentRuns(block.contentRuns);
    if (prefix) first.prefix = prefix;
    if (block.textProjection?.suffix) first.suffix = block.textProjection.suffix;
    if (block.textProjection?.fallback) first.fallback = block.textProjection.fallback;
    return first;
  }
  return block.textProjection ?? { field: "" };
}

export type ConsolidateTextBindingResult = {
  textProjection: ComunicadoTextProjection | undefined;
  contentRuns: ComunicadoContentRun[] | undefined;
  content?: string;
};

/**
 * Grava binding single-field: sempre materializa `textProjection` e remove dataRefs
 * dos runs (owner único = paint passa a usar textProjection).
 */
export function consolidateTextBindingToProjection(
  block: TextBoundBlockSlice,
  patch: Partial<ComunicadoTextProjection>,
): ConsolidateTextBindingResult {
  const current = readEffectiveTextProjection(block);
  const next: ComunicadoTextProjection = {
    field: current.field,
    ...current,
    ...patch,
  };
  if ("decimalPlaces" in patch && patch.decimalPlaces == null) {
    delete next.decimalPlaces;
  }
  if (!next.field?.trim()) {
    return {
      textProjection: undefined,
      contentRuns: stripDataRefsFromRuns(block.contentRuns),
      content: block.content,
    };
  }

  /* Prefixo já veio de runs estáticos via readEffective; patch.prefix sobrescreve. */
  if (!("prefix" in patch) && next.prefix == null) {
    const fromRuns = staticPrefixFromContentRuns(block.contentRuns);
    if (fromRuns) next.prefix = fromRuns;
  }

  return {
    textProjection: next,
    contentRuns: undefined,
    content: next.prefix?.trim() ? undefined : block.content,
  };
}

function stripDataRefsFromRuns(
  contentRuns: ComunicadoContentRun[] | undefined,
): ComunicadoContentRun[] | undefined {
  if (!contentRuns?.length) return undefined;
  const staticOnly = contentRuns
    .filter((run) => !run.dataRef?.field?.trim())
    .map((run) => {
      const { dataRef: _drop, ...rest } = run;
      return rest;
    });
  return staticOnly.length > 0 ? staticOnly : undefined;
}

/** True se o bloco tem textProjection e dataRefs ao mesmo tempo (estado dual ilegítimo). */
export function hasContradictoryTextBinding(block: TextBoundBlockSlice): boolean {
  return Boolean(
    block.textProjection?.field?.trim() && listBoundDataRefs(block).length > 0,
  );
}
