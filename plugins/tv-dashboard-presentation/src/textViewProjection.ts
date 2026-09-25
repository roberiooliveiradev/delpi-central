import {
  formatDisplayValue,
  isDisplayFormatSpec,
  parseKpiNumericValue,
  resolveDelpiKpiTone,
  resolveDisplayFormatSpec,
  specFromTextProjectionFormat,
} from "@delpi/plugin-ui/index";
import { normalizeDecimalPlaces } from "./nativeFormat";
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
import {
  preferServerDisplayRunText,
  preferServerTextDisplayRuns,
} from "./serverDisplayPaint";
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

/** Fonte de dados ligada — sem isso, projeção/dataRef órfãos não devem pintar «—». */
export function textBlockHasLinkedDataSource(block: { dataSourceId?: string }): boolean {
  return Boolean(block.dataSourceId?.trim());
}

/**
 * Fallback do trecho dinâmico: ligado sem valor → «—»; sem modelo → string vazia
 * (mantém prefixo/rótulo estático, sem travessão fantasma).
 */
export function dynamicTextEmptyFallback(
  block: { dataSourceId?: string },
  explicitFallback?: string | null,
): string {
  if (!textBlockHasLinkedDataSource(block)) return "";
  const custom = explicitFallback?.trim();
  return custom || "—";
}

export function normalizeTextProjection(raw: unknown): ComunicadoTextProjection | undefined {
  if (!raw || typeof raw !== "object") return undefined;
  const item = raw as ComunicadoTextProjection;
  const field = String(item.field ?? "").trim();
  if (!field) return undefined;
  const projection: ComunicadoTextProjection = { field };
  if (item.aggregation) projection.aggregation = item.aggregation;
  if (item.format) projection.format = item.format;
  if (isDisplayFormatSpec(item.displayFormat)) projection.displayFormat = item.displayFormat;
  const decimalPlaces = normalizeDecimalPlaces(item.decimalPlaces);
  if (decimalPlaces != null) projection.decimalPlaces = decimalPlaces;
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
  if (isDisplayFormatSpec(item.displayFormat)) ref.displayFormat = item.displayFormat;
  const decimalPlaces = normalizeDecimalPlaces(item.decimalPlaces);
  if (decimalPlaces != null) ref.decimalPlaces = decimalPlaces;
  if (typeof item.label === "string" && item.label.trim()) ref.label = item.label.trim();
  if (Array.isArray(item.colorRules) && item.colorRules.length > 0) {
    ref.colorRules = [...item.colorRules];
  }
  return ref;
}

export type FormatTextProjectionOptions = {
  decimalPlaces?: number | null;
  displayFormat?: import("@delpi/plugin-ui/index").DisplayFormatSpec | null;
};

export function formatTextProjectionValue(
  value: unknown,
  format: TextProjectionFormat | undefined,
  options?: FormatTextProjectionOptions,
): string {
  if (value == null || value === "") return "—";
  const spec = resolveDisplayFormatSpec(
    options?.displayFormat,
    specFromTextProjectionFormat(format, options?.decimalPlaces),
  );
  return formatDisplayValue(value, spec);
}

export function resolveTextDataRefValue(
  resolved: ComunicadoDataResolved | undefined,
  ref: ComunicadoTextDataRef,
  fallback = "—",
): { text: string; color?: string } {
  const serverText = preferServerDisplayRunText(resolved, ref.field);
  if (serverText == null) {
    // FE-BE-002: enrich owns display* — no client format on TV paint path.
    return { text: fallback };
  }
  const projected = resolveProjectedField(resolved, ref.field, ref.aggregation ?? "first");
  const rawForTone =
    projected.kind === "list"
      ? projected.values[0]
      : projected.kind === "scalar"
        ? projected.scalar
        : undefined;
  const numeric = parseKpiNumericValue(rawForTone);
  const tone = resolveDelpiKpiTone(numeric, ref.colorRules, "default");
  return { text: serverText, color: tone.valueColor };
}

export function resolveTextDisplayValue(
  resolved: ComunicadoDataResolved | undefined,
  projection: ComunicadoTextProjection | undefined,
  options?: { linkedDataSource?: boolean },
): { text: string; color?: string } {
  if (!projection?.field?.trim()) return { text: "" };
  if (resolved?.presentationStale === true) {
    const linked = options?.linkedDataSource !== false;
    return { text: linked ? projection.fallback?.trim() || "—" : "" };
  }
  // Enrich já compôs prefixo + valor + sufixo em displayText — paint-only.
  if (typeof resolved?.displayText === "string") {
    const projected = resolveProjectedField(
      resolved,
      projection.field,
      projection.aggregation ?? "first",
    );
    const rawForTone =
      projected.kind === "list"
        ? projected.values[0]
        : projected.kind === "scalar"
          ? projected.scalar
          : undefined;
    const numeric = parseKpiNumericValue(rawForTone);
    const tone = resolveDelpiKpiTone(numeric, projection.colorRules, "default");
    return { text: resolved.displayText, color: tone.valueColor };
  }
  const linked = options?.linkedDataSource !== false;
  const fallback = linked ? projection.fallback?.trim() || "—" : "";
  const { text, color } = resolveTextDataRefValue(
    resolved,
    {
      field: projection.field,
      aggregation: projection.aggregation,
      format: projection.format,
      displayFormat: projection.displayFormat,
      decimalPlaces: projection.decimalPlaces,
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
  // Prefer server-materialized core (FE-BE-002); strip known affixes from displayText.
  let coreText = preferServerDisplayRunText(resolved, projection.field);
  if (coreText == null && typeof resolved?.displayText === "string") {
    let baked = resolved.displayText;
    const prefix = projection.prefix ?? "";
    const suffix = projection.suffix ?? "";
    if (prefix && baked.startsWith(prefix)) baked = baked.slice(prefix.length);
    if (suffix && baked.endsWith(suffix)) baked = baked.slice(0, baked.length - suffix.length);
    coreText = baked;
  }
  if (coreText == null || coreText.length === 0) {
    coreText = resolveTextDataRefValue(
      resolved,
      {
        field: projection.field,
        aggregation: projection.aggregation,
        format: projection.format,
        displayFormat: projection.displayFormat,
        decimalPlaces: projection.decimalPlaces,
        colorRules: projection.colorRules,
      },
      fallback,
    ).text;
  }
  const { prefix, suffix } = splitEditedDisplayAroundCoreValue(editedDisplay, coreText);
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
    displayFormat: { category: "general", presetId: "general" },
    format: "raw",
  };
}

export function resolveTextBlockDisplayRuns(
  block: Pick<ComunicadoTextBlock, "content" | "contentRuns" | "textProjection"> & {
    dataSourceId?: string;
    resolved?: ComunicadoDataResolved;
  },
  resolved?: ComunicadoDataResolved,
): ComunicadoContentRun[] {
  const data = resolved ?? block.resolved;
  const serverRuns = preferServerTextDisplayRuns(data);
  if (serverRuns) return serverRuns;
  const emptyFallback = dynamicTextEmptyFallback(block);
  const hasDataRuns = block.contentRuns?.some((run) => run.dataRef?.field?.trim());
  if (hasDataRuns && block.contentRuns) {
    return block.contentRuns.map((run) => {
      if (!run.dataRef?.field?.trim()) return run;
      const { text, color } = resolveTextDataRefValue(data, run.dataRef, emptyFallback);
      const style = color
        ? { ...(run.style ?? {}), color }
        : run.style;
      return { ...run, text, style };
    });
  }
  if (block.textProjection?.field?.trim()) {
    const { text, color } = resolveTextDisplayValue(data, block.textProjection, {
      linkedDataSource: textBlockHasLinkedDataSource(block),
    });
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
  const data = resolved ?? ("resolved" in block ? block.resolved : undefined);
  // Server-owned display* wins even for unbound static text/heading (textCase).
  const serverRuns = preferServerTextDisplayRuns(data);
  if (serverRuns) {
    return {
      content: plainTextFromContentRuns(serverRuns),
      contentRuns: serverRuns,
    };
  }
  if (!textBlockHasDataBinding(block)) {
    if (block.type === "shape") {
      return {
        content: block.content ?? "",
        contentRuns: block.contentRuns,
      };
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
          dataSourceId: block.dataSourceId,
        }
      : block,
    data,
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

/**
 * Texto estático do bloco (content / runs sem dataRef) — usado como rótulo ao ligar dado.
 */
export function staticLabelFromTextBoundBlock(
  block: Pick<TextDataBoundBlock, "content" | "contentRuns">,
): string {
  if (block.contentRuns?.length && !block.contentRuns.some((run) => run.dataRef?.field?.trim())) {
    return plainTextFromContentRuns(block.contentRuns);
  }
  return typeof block.content === "string" ? block.content : "";
}

/**
 * Rótulo estático vira `prefix` da projeção: valor dinâmico no final, sem substituir o texto.
 * Acrescenta espaço (ou preserva `:` / quebra) entre rótulo e valor.
 */
export function textProjectionPrefixFromStaticLabel(
  label: string | undefined | null,
): string | undefined {
  const trimmedEnd = String(label ?? "").replace(/\s+$/u, "");
  if (!trimmedEnd) return undefined;
  if (/[\s:：\-–—(/[{]$/u.test(trimmedEnd)) return trimmedEnd;
  return `${trimmedEnd} `;
}

export type BuildTextDataLinkPatchInput = {
  dataSourceId: string;
  resolved?: ComunicadoDataResolved;
  existing?: ComunicadoTextProjection;
  /** Campos do catálogo da rota — fallback quando o resolved ainda não listou fields. */
  catalogFields?: Array<{ field: string; label: string }>;
  /**
   * Conteúdo estático atual (ex.: «Realizado»). Vira `textProjection.prefix`
   * na 1ª ligação — o valor dinâmico é acrescentado no final, não substitui.
   */
  staticContent?: string;
};

export function buildTextDataLinkPatch(
  input: BuildTextDataLinkPatchInput,
): Partial<TextDataBoundBlock> {
  const { dataSourceId, resolved, existing, catalogFields, staticContent } = input;
  const patch: Partial<TextDataBoundBlock> = { dataSourceId };
  if (!textProjectionHasField(existing)) {
    const suggested = suggestDefaultTextProjection(resolved, catalogFields);
    if (suggested) {
      const next: ComunicadoTextProjection = { ...suggested };
      if (existing?.prefix) next.prefix = existing.prefix;
      else {
        const fromLabel = textProjectionPrefixFromStaticLabel(staticContent);
        if (fromLabel) next.prefix = fromLabel;
      }
      if (existing?.suffix) next.suffix = existing.suffix;
      if (existing?.fallback) next.fallback = existing.fallback;
      if (existing?.colorRules?.length) next.colorRules = [...existing.colorRules];
      patch.textProjection = next;
    }
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
      const fromLabel = textProjectionPrefixFromStaticLabel(staticLabelFromTextBoundBlock(block));
      const textProjection: ComunicadoTextProjection = fromLabel
        ? { ...suggested, prefix: fromLabel }
        : suggested;
      changedIds.push(block.id);
      return { ...block, textProjection } as ComunicadoBlock;
    }
    return block;
  });
  return { next, changedIds };
}
