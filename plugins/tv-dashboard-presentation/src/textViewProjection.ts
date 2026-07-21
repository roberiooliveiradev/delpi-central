import {
  parseKpiNumericValue,
  resolveDelpiKpiTone,
} from "@delpi/plugin-ui/index";

import { formatNumber, formatPct } from "./nativeFormat";
import type {
  ComunicadoBlock,
  ComunicadoContentRun,
  ComunicadoDataResolved,
  ComunicadoShapeBlock,
  ComunicadoTextBlock,
  ComunicadoTextDataRef,
  ComunicadoTextProjection,
  TextProjectionFormat,
} from "./comunicadoTypes";
import { isComunicadoVisualBoxBlock } from "./comunicadoVisualBox";
import { plainTextFromContentRuns } from "./comunicadoContentRuns";
import {
  FIELD_LIST_JOIN,
  parseProjectionNumber,
  resolveProjectedField,
  suggestDefaultAggregationForField,
  suggestPreferredProjectionField,
} from "./fieldValueProjection";
import { discoverResolvedFieldOptions } from "./viewProjection";

export type TextDataBoundBlock = ComunicadoTextBlock | ComunicadoShapeBlock;

export function isTextDataBoundBlock(block: { type: string }): block is TextDataBoundBlock {
  return block.type === "heading" || block.type === "text" || block.type === "shape";
}

export function textBlockHasDataBinding(
  block: { dataSourceId?: string; textProjection?: ComunicadoTextProjection; contentRuns?: ComunicadoContentRun[] },
): boolean {
  if (block.dataSourceId?.trim()) return true;
  if (block.textProjection?.field?.trim()) return true;
  return Boolean(block.contentRuns?.some((run) => run.dataRef?.field?.trim()));
}

export function normalizeTextProjection(raw: unknown): ComunicadoTextProjection | undefined {
  if (!raw || typeof raw !== "object") return undefined;
  const item = raw as ComunicadoTextProjection;
  const field = String(item.field ?? "").trim();
  if (!field) return undefined;
  const projection: ComunicadoTextProjection = { field };
  if (item.aggregation) projection.aggregation = item.aggregation;
  if (item.format) projection.format = item.format;
  if (typeof item.prefix === "string" && item.prefix) projection.prefix = item.prefix;
  if (typeof item.suffix === "string" && item.suffix) projection.suffix = item.suffix;
  if (typeof item.fallback === "string" && item.fallback) projection.fallback = item.fallback;
  if (Array.isArray(item.colorRules) && item.colorRules.length > 0) {
    projection.colorRules = [...item.colorRules];
  }
  return projection;
}

export function normalizeTextDataRef(raw: unknown): ComunicadoTextDataRef | undefined {
  if (!raw || typeof raw !== "object") return undefined;
  const item = raw as ComunicadoTextDataRef;
  const field = String(item.field ?? "").trim();
  if (!field) return undefined;
  const ref: ComunicadoTextDataRef = { field };
  if (item.aggregation) ref.aggregation = item.aggregation;
  if (item.format) ref.format = item.format;
  if (typeof item.label === "string" && item.label.trim()) ref.label = item.label.trim();
  if (Array.isArray(item.colorRules) && item.colorRules.length > 0) {
    ref.colorRules = [...item.colorRules];
  }
  return ref;
}

export function formatTextProjectionValue(
  value: unknown,
  format: TextProjectionFormat | undefined,
): string {
  if (value == null || value === "") return "—";
  if (format === "raw" || format == null) return String(value);
  if (format === "date") {
    const text = String(value).trim();
    if (!text) return "—";
    const parsed = Date.parse(text);
    if (!Number.isNaN(parsed)) {
      return new Date(parsed).toLocaleDateString("pt-BR");
    }
    return text;
  }
  const numeric = parseProjectionNumber(value);
  if (numeric == null) return String(value);
  if (format === "percent") return formatPct(numeric);
  if (format === "compact") {
    return numeric.toLocaleString("pt-BR", { notation: "compact", maximumFractionDigits: 1 });
  }
  return formatNumber(numeric);
}

export function resolveTextDataRefValue(
  resolved: ComunicadoDataResolved | undefined,
  ref: ComunicadoTextDataRef,
  fallback = "—",
): { text: string; color?: string } {
  const projected = resolveProjectedField(resolved, ref.field, ref.aggregation ?? "first");
  if (projected.kind === "empty") {
    return { text: fallback };
  }
  if (projected.kind === "list") {
    const parts = projected.values.map((value) => formatTextProjectionValue(value, ref.format));
    const text = parts.join(FIELD_LIST_JOIN);
    const numeric = parseKpiNumericValue(projected.values[0]);
    const tone = resolveDelpiKpiTone(numeric, ref.colorRules, "default");
    return { text, color: tone.valueColor };
  }
  const raw = projected.scalar;
  if (raw == null || raw === "") {
    return { text: fallback };
  }
  const text = formatTextProjectionValue(raw, ref.format);
  const numeric = parseKpiNumericValue(raw);
  const tone = resolveDelpiKpiTone(numeric, ref.colorRules, "default");
  return { text, color: tone.valueColor };
}

export function resolveTextDisplayValue(
  resolved: ComunicadoDataResolved | undefined,
  projection: ComunicadoTextProjection | undefined,
): { text: string; color?: string } {
  if (!projection?.field?.trim()) return { text: "" };
  const fallback = projection.fallback?.trim() || "—";
  const { text, color } = resolveTextDataRefValue(
    resolved,
    {
      field: projection.field,
      aggregation: projection.aggregation,
      format: projection.format,
      colorRules: projection.colorRules,
    },
    fallback,
  );
  const prefix = projection.prefix ?? "";
  const suffix = projection.suffix ?? "";
  return { text: `${prefix}${text}${suffix}`, color };
}

/**
 * Separa o texto editado no palco (prefixo + valor dinâmico + sufixo) em affixes.
 * O valor core formatado é âncora — não deve ser gravado em `content`.
 */
export function splitEditedDisplayAroundCoreValue(
  editedDisplay: string,
  coreValue: string,
): { prefix?: string; suffix?: string } {
  const edited = editedDisplay;
  if (!coreValue) {
    return { prefix: edited || undefined, suffix: undefined };
  }
  const idx = edited.indexOf(coreValue);
  if (idx < 0) {
    // Valor dinâmico sumiu da edição — guarda o texto como prefixo.
    return { prefix: edited || undefined, suffix: undefined };
  }
  const prefix = edited.slice(0, idx);
  const suffix = edited.slice(idx + coreValue.length);
  return {
    prefix: prefix || undefined,
    suffix: suffix || undefined,
  };
}

/**
 * Atualiza prefixo/sufixo da projeção a partir do texto composto editado no palco.
 * Sidebar e edição inline compartilham a mesma fonte (`textProjection`).
 */
export function patchTextProjectionFromEditedDisplay(
  projection: ComunicadoTextProjection,
  editedDisplay: string,
  resolved?: ComunicadoDataResolved,
): ComunicadoTextProjection {
  const fallback = projection.fallback?.trim() || "—";
  const core = resolveTextDataRefValue(
    resolved,
    {
      field: projection.field,
      aggregation: projection.aggregation,
      format: projection.format,
      colorRules: projection.colorRules,
    },
    fallback,
  );
  const { prefix, suffix } = splitEditedDisplayAroundCoreValue(editedDisplay, core.text);
  const next: ComunicadoTextProjection = { ...projection };
  if (prefix) next.prefix = prefix;
  else delete next.prefix;
  if (suffix) next.suffix = suffix;
  else delete next.suffix;
  return next;
}

export function suggestDefaultTextProjection(
  resolved: ComunicadoDataResolved | undefined,
  catalogFields?: Array<{ field: string; label: string }>,
): ComunicadoTextProjection | undefined {
  const fields = discoverResolvedFieldOptions(resolved, catalogFields);
  if (fields.length === 0) return undefined;
  const field = suggestPreferredProjectionField(resolved, fields) ?? fields[0]?.field;
  if (!field) return undefined;
  return {
    field,
    aggregation: suggestDefaultAggregationForField(resolved, field),
    format: "number",
  };
}

export function resolveTextBlockDisplayRuns(
  block: Pick<ComunicadoTextBlock, "content" | "contentRuns" | "textProjection"> & {
    resolved?: ComunicadoDataResolved;
  },
  resolved?: ComunicadoDataResolved,
): ComunicadoContentRun[] {
  const data = resolved ?? block.resolved;
  const hasDataRuns = block.contentRuns?.some((run) => run.dataRef?.field?.trim());
  if (hasDataRuns && block.contentRuns) {
    return block.contentRuns.map((run) => {
      if (!run.dataRef?.field?.trim()) return run;
      const { text, color } = resolveTextDataRefValue(data, run.dataRef, run.text || "—");
      const style = color
        ? { ...(run.style ?? {}), color }
        : run.style;
      return { ...run, text, style };
    });
  }
  if (block.textProjection?.field?.trim()) {
    const { text, color } = resolveTextDisplayValue(data, block.textProjection);
    const baseStyle = color ? { color } : undefined;
    return [{ text, style: baseStyle }];
  }
  if (block.contentRuns && block.contentRuns.length > 0) return block.contentRuns;
  return [{ text: block.content }];
}

export function resolveVisualBoxDisplayText(
  block: ComunicadoTextBlock | ComunicadoShapeBlock,
  resolved?: ComunicadoDataResolved,
): Pick<ComunicadoTextBlock, "content" | "contentRuns"> {
  if (!textBlockHasDataBinding(block)) {
    if (block.type === "shape") {
      return { content: block.content ?? "" };
    }
    return {
      content: block.content,
      contentRuns: block.contentRuns,
    };
  }
  const runs = resolveTextBlockDisplayRuns(
    block.type === "shape"
      ? {
          content: block.content ?? "",
          contentRuns: block.contentRuns,
          textProjection: block.textProjection,
        }
      : block,
    resolved ?? ("resolved" in block ? block.resolved : undefined),
  );
  return {
    content: plainTextFromContentRuns(runs),
    contentRuns: runs,
  };
}

export function textProjectionHasField(projection: ComunicadoTextProjection | undefined): boolean {
  return Boolean(projection?.field?.trim());
}

export function viewHasTextProjectionConfigured(
  block: Pick<TextDataBoundBlock, "textProjection" | "contentRuns">,
): boolean {
  if (textProjectionHasField(block.textProjection)) return true;
  return Boolean(block.contentRuns?.some((run) => run.dataRef?.field?.trim()));
}

export type BuildTextDataLinkPatchInput = {
  dataSourceId: string;
  resolved?: ComunicadoDataResolved;
  existing?: ComunicadoTextProjection;
  /** Campos do catálogo da rota — fallback quando o resolved ainda não listou fields. */
  catalogFields?: Array<{ field: string; label: string }>;
};

export function buildTextDataLinkPatch(
  input: BuildTextDataLinkPatchInput,
): Partial<TextDataBoundBlock> {
  const { dataSourceId, resolved, existing, catalogFields } = input;
  const patch: Partial<TextDataBoundBlock> = { dataSourceId };
  if (!textProjectionHasField(existing)) {
    const suggested = suggestDefaultTextProjection(resolved, catalogFields);
    if (suggested) patch.textProjection = suggested;
  }
  return patch;
}

export function syncTextBlocksWithResolved(
  blocks: ComunicadoBlock[],
  resolvedBySourceId: Record<string, ComunicadoDataResolved | undefined>,
): { next: ComunicadoBlock[]; changedIds: string[] } {
  const changedIds: string[] = [];
  const next = blocks.map((block) => {
    if (!isComunicadoVisualBoxBlock(block)) return block;
    if (!textBlockHasDataBinding(block)) return block;
    const sourceId = block.dataSourceId?.trim();
    if (!sourceId) return block;
    const resolved = resolvedBySourceId[sourceId];
    if (!resolved) return block;
    if (!textProjectionHasField(block.textProjection) && !block.contentRuns?.some((r) => r.dataRef)) {
      const suggested = suggestDefaultTextProjection(resolved);
      if (!suggested) return block;
      changedIds.push(block.id);
      return { ...block, textProjection: suggested } as ComunicadoBlock;
    }
    return block;
  });
  return { next, changedIds };
}
