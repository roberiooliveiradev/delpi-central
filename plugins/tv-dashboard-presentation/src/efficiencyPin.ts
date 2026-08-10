/**
 * Pin de CT na planta (TV Dashboard) — status/cor a partir da eficiência por centro.
 * Alinhado às faixas do plugin eficiência-fabril (KPI warning 95%, baixa 50%, válida ≤199%).
 */

import type {
  ComunicadoBlock,
  ComunicadoDataResolved,
  ComunicadoDataSourceBlock,
  ComunicadoEfficiencyPinBands,
  ComunicadoEfficiencyPinBinding,
  ComunicadoEfficiencyPinInfoMode,
  ComunicadoEfficiencyPinRole,
  ComunicadoFrame,
  ComunicadoShapeBlock,
  ComunicadoShapeKind,
} from "./comunicadoTypes";

export type EfficiencyPinStatus = "good" | "warn" | "bad" | "verify" | "unknown";

export type EfficiencyPinResolvedState = {
  status: EfficiencyPinStatus;
  color: string;
  efficiencyPct: number | null;
  workCenter: string;
  appointmentCount: number | null;
  label: string;
};

export const EFFICIENCY_PIN_DEFAULT_GOOD_MIN_PCT = 95;
export const EFFICIENCY_PIN_DEFAULT_WARN_MIN_PCT = 50;
export const EFFICIENCY_PIN_DEFAULT_VALID_MAX_PCT = 199;
export const EFFICIENCY_PIN_DEFAULT_MATCH_FIELD = "work_center";
export const EFFICIENCY_PIN_DEFAULT_VALUE_FIELD = "efficiency_pct";
/** Raio visual maior que o ponto simples — anéis do radar. */
export const EFFICIENCY_PIN_MARKER_RADIUS_DEFAULT = 32;
/** Alvo de seleção / bbox no palco (% do slide) — cabe radar + rótulo. */
export const EFFICIENCY_PIN_HIT_SIZE_PCT = 12;

export const EFFICIENCY_PIN_STATUS_COLORS: Record<EfficiencyPinStatus, string> = {
  good: "#22c55e",
  warn: "#eab308",
  bad: "#ef4444",
  verify: "#f97316",
  unknown: "#94a3b8",
};

export const EFFICIENCY_PIN_OPERATION_ID = "get_eficiencia_fabril_efficiency_by_work_center";

export function isEfficiencyPinShapeKind(kind: ComunicadoShapeKind | undefined | null): boolean {
  return kind === "efficiency-pin";
}

/** Frame mínimo usável para handles de resize (~% do slide). */
export const EFFICIENCY_PIN_MIN_FRAME_PCT = 4;

/**
 * Pins legados (ponto w/h≈0) ou corrompidos → quadrado redimensionável.
 * Remove `vertices` de ponto (1 vértice) que confundem a geometria de área.
 * Expande a partir do **centro** do ponto legado para não deslocar o pin na planta.
 */
export function ensureEfficiencyPinResizableFrame(
  block: ComunicadoShapeBlock,
  defaultPinFrame: ComunicadoFrame,
): ComunicadoShapeBlock {
  if (!isEfficiencyPinShapeKind(block.shape)) return block;
  const tooSmall = block.frame.w < EFFICIENCY_PIN_MIN_FRAME_PCT || block.frame.h < EFFICIENCY_PIN_MIN_FRAME_PCT;
  const badVertices = Array.isArray(block.vertices) && block.vertices.length > 0 && block.vertices.length < 3;
  if (!tooSmall && !badVertices) return block;
  const w = Math.max(defaultPinFrame.w, EFFICIENCY_PIN_MIN_FRAME_PCT);
  const h = Math.max(defaultPinFrame.h, EFFICIENCY_PIN_MIN_FRAME_PCT);
  const frame = tooSmall
    ? {
        x: block.frame.x + block.frame.w / 2 - w / 2,
        y: block.frame.y + block.frame.h / 2 - h / 2,
        w,
        h,
      }
    : block.frame;
  return {
    ...block,
    frame,
    ...(badVertices ? { vertices: undefined } : {}),
  };
}

/** Migra todos os pins CT do slide (load / sync editor). */
export function migrateEfficiencyPinBlocks<T extends { type?: string; shape?: ComunicadoShapeKind }>(
  blocks: readonly T[],
  defaultPinFrame: ComunicadoFrame,
): T[] {
  return blocks.map((block) => {
    if (!isEfficiencyPinBlock(block)) return block;
    return ensureEfficiencyPinResizableFrame(block, defaultPinFrame) as T;
  });
}

export function isEfficiencyPinBlock(
  block: { type?: string; shape?: ComunicadoShapeKind } | null | undefined,
): block is ComunicadoShapeBlock {
  return Boolean(block && block.type === "shape" && isEfficiencyPinShapeKind(block.shape));
}

/**
 * Fonte compartilhada para pins CT no slide: prioriza a rota de eficiência por CT,
 * depois qualquer fonte já ligada a um pin. Um slide tipicamente tem **uma** fonte
 * e vários pins (cada um só escolhe o work_center).
 */
export function findSharedEfficiencyPinDataSourceId(
  blocks: readonly ComunicadoBlock[],
): string | undefined {
  const efficiencySources = blocks.filter(
    (block): block is ComunicadoDataSourceBlock =>
      block.type === "data_source" &&
      String(block.dataBinding?.operationId ?? "").trim() === EFFICIENCY_PIN_OPERATION_ID,
  );
  if (efficiencySources.length === 1) return efficiencySources[0]!.id;
  if (efficiencySources.length > 1) {
    const linkedByPin = new Set(
      blocks
        .filter(isEfficiencyPinBlock)
        .map((block) => block.dataSourceId?.trim())
        .filter((id): id is string => Boolean(id)),
    );
    const preferred = efficiencySources.find((source) => linkedByPin.has(source.id));
    return preferred?.id ?? efficiencySources[0]!.id;
  }
  for (const block of blocks) {
    if (isEfficiencyPinBlock(block)) {
      const sourceId = block.dataSourceId?.trim();
      if (sourceId) return sourceId;
    }
  }
  return undefined;
}

/**
 * Liga `dataSourceId` em todos os pins CT (e infos) sem fonte — mantém CT de cada um.
 */
export function applySharedDataSourceToUnlinkedEfficiencyPins(
  blocks: readonly ComunicadoBlock[],
  sourceId: string,
): ComunicadoBlock[] {
  const trimmed = sourceId.trim();
  if (!trimmed) return [...blocks];
  return blocks.map((block) => {
    if (!isEfficiencyPinBlock(block)) return block;
    if (block.dataSourceId?.trim()) return block;
    return { ...block, dataSourceId: trimmed };
  });
}

/**
 * Propaga faixas de cor para todos os pins CT da mesma fonte (mapa da planta).
 * Sem `sourceId`, aplica a todos os pins do slide.
 */
export function applyEfficiencyPinBandsToSharedPins(
  blocks: readonly ComunicadoBlock[],
  bands: ComunicadoEfficiencyPinBands,
  options?: { sourceId?: string | null; excludeBlockId?: string | null },
): ComunicadoBlock[] {
  const sourceId = options?.sourceId?.trim() || "";
  const excludeId = options?.excludeBlockId?.trim() || "";
  return blocks.map((block) => {
    if (!isEfficiencyPinBlock(block)) return block;
    if (excludeId && block.id === excludeId) return block;
    if (sourceId && block.dataSourceId?.trim() !== sourceId) return block;
    return {
      ...block,
      efficiencyPin: {
        ...(block.efficiencyPin ?? {}),
        bands: { ...bands },
      },
    };
  });
}

/** Faixas já gravadas em algum pin da mesma fonte (para herdar ao vincular). */
export function findSharedEfficiencyPinBands(
  blocks: readonly ComunicadoBlock[],
  sourceId: string | null | undefined,
): ComunicadoEfficiencyPinBands | undefined {
  const trimmed = sourceId?.trim();
  if (!trimmed) return undefined;
  for (const block of blocks) {
    if (!isEfficiencyPinBlock(block)) continue;
    if (block.dataSourceId?.trim() !== trimmed) continue;
    const bands = block.efficiencyPin?.bands;
    if (bands && (bands.goodMinPct != null || bands.warnMinPct != null || bands.validMaxPct != null)) {
      return { ...bands };
    }
  }
  return undefined;
}

function finiteNumber(value: unknown): number | null {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string" && value.trim()) {
    const parsed = Number(value.replace(",", "."));
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

export function resolveEfficiencyPinBands(
  bands: ComunicadoEfficiencyPinBands | undefined | null,
): Required<ComunicadoEfficiencyPinBands> {
  const goodMinPct = finiteNumber(bands?.goodMinPct) ?? EFFICIENCY_PIN_DEFAULT_GOOD_MIN_PCT;
  const warnMinPct = finiteNumber(bands?.warnMinPct) ?? EFFICIENCY_PIN_DEFAULT_WARN_MIN_PCT;
  const validMaxPct = finiteNumber(bands?.validMaxPct) ?? EFFICIENCY_PIN_DEFAULT_VALID_MAX_PCT;
  return { goodMinPct, warnMinPct, validMaxPct };
}

export function classifyEfficiencyPinPct(
  pct: number | null,
  bands?: ComunicadoEfficiencyPinBands | null,
): EfficiencyPinStatus {
  if (pct == null || Number.isNaN(pct)) return "unknown";
  const { goodMinPct, warnMinPct, validMaxPct } = resolveEfficiencyPinBands(bands);
  if (pct < 0 || pct > validMaxPct) return "verify";
  if (pct >= goodMinPct) return "good";
  if (pct >= warnMinPct) return "warn";
  return "bad";
}

export function colorForEfficiencyPinStatus(status: EfficiencyPinStatus): string {
  return EFFICIENCY_PIN_STATUS_COLORS[status];
}

function rowsFromResolved(resolved: ComunicadoDataResolved | undefined | null): Array<Record<string, unknown>> {
  if (!resolved) return [];
  const tableRows = resolved.table?.rows;
  if (Array.isArray(tableRows) && tableRows.length > 0) {
    return tableRows.filter((row): row is Record<string, unknown> => Boolean(row) && typeof row === "object");
  }
  const previewRows = resolved.preview?.rows;
  if (Array.isArray(previewRows) && previewRows.length > 0) {
    return previewRows.filter((row): row is Record<string, unknown> => Boolean(row) && typeof row === "object");
  }
  const data = resolved.data;
  if (Array.isArray(data)) {
    return data.filter((row): row is Record<string, unknown> => Boolean(row) && typeof row === "object");
  }
  if (data && typeof data === "object") {
    const items = (data as { items?: unknown }).items;
    if (Array.isArray(items)) {
      return items.filter((row): row is Record<string, unknown> => Boolean(row) && typeof row === "object");
    }
  }
  return [];
}

export function listWorkCentersFromResolved(
  resolved: ComunicadoDataResolved | undefined | null,
  matchField = EFFICIENCY_PIN_DEFAULT_MATCH_FIELD,
): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const row of rowsFromResolved(resolved)) {
    const raw = row[matchField];
    const value = typeof raw === "string" ? raw.trim() : raw != null ? String(raw).trim() : "";
    if (!value || seen.has(value)) continue;
    seen.add(value);
    out.push(value);
  }
  return out.sort((a, b) => a.localeCompare(b, "pt-BR", { sensitivity: "base" }));
}

function findWorkCenterRow(
  resolved: ComunicadoDataResolved | undefined | null,
  workCenter: string,
  matchField: string,
): Record<string, unknown> | null {
  const target = workCenter.trim().toLocaleLowerCase("pt-BR");
  if (!target) return null;
  for (const row of rowsFromResolved(resolved)) {
    const raw = row[matchField];
    const value = typeof raw === "string" ? raw.trim() : raw != null ? String(raw).trim() : "";
    if (value.toLocaleLowerCase("pt-BR") === target) return row;
  }
  return null;
}

export function isEfficiencyPinInfoRole(
  binding: ComunicadoEfficiencyPinBinding | undefined | null,
): boolean {
  return binding?.role === "info";
}

export function resolveEfficiencyPinInfoMode(
  binding: ComunicadoEfficiencyPinBinding | undefined | null,
): ComunicadoEfficiencyPinInfoMode {
  if (binding?.infoMode === "attached" || binding?.infoMode === "detached" || binding?.infoMode === "hidden") {
    return binding.infoMode;
  }
  if (binding?.showLabel === false) return "hidden";
  return "attached";
}

export function resolveEfficiencyPinRole(
  binding: ComunicadoEfficiencyPinBinding | undefined | null,
): ComunicadoEfficiencyPinRole {
  return binding?.role === "info" ? "info" : "pin";
}

/**
 * Cartão de informação destacado do radar — mesmo CT/fonte, frame ao lado do pin.
 */
export function buildEfficiencyPinInfoBlock(
  pin: ComunicadoShapeBlock,
  options?: { frame?: ComunicadoFrame; id?: string },
): ComunicadoShapeBlock {
  const pinFrame = pin.frame;
  const w = Math.max(8, pinFrame.w * 1.1);
  const h = Math.max(5, pinFrame.h * 0.55);
  const frame =
    options?.frame ??
    ({
      x: Math.min(92, pinFrame.x + pinFrame.w + 1.5),
      y: pinFrame.y + Math.max(0, (pinFrame.h - h) / 2),
      w,
      h,
    } satisfies ComunicadoFrame);
  return {
    id: options?.id ?? `blk_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`,
    type: "shape",
    shape: "efficiency-pin",
    frame,
    style: {
      zIndex: (pin.style?.zIndex ?? 1) + 1,
      fill: "transparent",
      stroke: "transparent",
      strokeWidth: 0,
      opacity: 1,
    },
    dataSourceId: pin.dataSourceId,
    content: pin.efficiencyPin?.workCenter?.trim() || pin.content || "",
    efficiencyPin: {
      ...(pin.efficiencyPin ?? {}),
      role: "info",
      infoMode: "detached",
      showLabel: true,
      linkedBlockId: pin.id,
    },
    resolved: pin.resolved,
  };
}

export function normalizeEfficiencyPinBinding(
  value: unknown,
): ComunicadoEfficiencyPinBinding | undefined {
  if (!value || typeof value !== "object") return undefined;
  const raw = value as Record<string, unknown>;
  const workCenter =
    typeof raw.workCenter === "string" && raw.workCenter.trim() ? raw.workCenter.trim() : undefined;
  const matchField =
    typeof raw.matchField === "string" && raw.matchField.trim() ? raw.matchField.trim() : undefined;
  const valueField =
    typeof raw.valueField === "string" && raw.valueField.trim() ? raw.valueField.trim() : undefined;
  const showLabel = typeof raw.showLabel === "boolean" ? raw.showLabel : undefined;
  const infoMode =
    raw.infoMode === "attached" || raw.infoMode === "detached" || raw.infoMode === "hidden"
      ? raw.infoMode
      : undefined;
  const role = raw.role === "info" || raw.role === "pin" ? raw.role : undefined;
  const linkedBlockId =
    typeof raw.linkedBlockId === "string" && raw.linkedBlockId.trim()
      ? raw.linkedBlockId.trim()
      : undefined;
  const bandsRaw = raw.bands && typeof raw.bands === "object" ? (raw.bands as Record<string, unknown>) : null;
  const bands: ComunicadoEfficiencyPinBands | undefined = bandsRaw
    ? (() => {
        const goodMinPct = finiteNumber(bandsRaw.goodMinPct);
        const warnMinPct = finiteNumber(bandsRaw.warnMinPct);
        const validMaxPct = finiteNumber(bandsRaw.validMaxPct);
        const next: ComunicadoEfficiencyPinBands = {
          ...(goodMinPct != null ? { goodMinPct } : {}),
          ...(warnMinPct != null ? { warnMinPct } : {}),
          ...(validMaxPct != null ? { validMaxPct } : {}),
        };
        return next;
      })()
    : undefined;
  const hasBands = bands && Object.keys(bands).length > 0;
  if (
    !workCenter &&
    !matchField &&
    !valueField &&
    showLabel === undefined &&
    !infoMode &&
    !role &&
    !linkedBlockId &&
    !hasBands
  ) {
    return {};
  }
  return {
    ...(workCenter ? { workCenter } : {}),
    ...(matchField ? { matchField } : {}),
    ...(valueField ? { valueField } : {}),
    ...(showLabel !== undefined ? { showLabel } : {}),
    ...(infoMode ? { infoMode } : {}),
    ...(role ? { role } : {}),
    ...(linkedBlockId ? { linkedBlockId } : {}),
    ...(hasBands ? { bands } : {}),
  };
}

export function resolveEfficiencyPinState(
  block: Pick<ComunicadoShapeBlock, "efficiencyPin" | "resolved" | "content">,
  resolvedOverride?: ComunicadoDataResolved | null,
): EfficiencyPinResolvedState {
  const binding = block.efficiencyPin ?? {};
  const workCenter = (binding.workCenter ?? "").trim();
  const matchField = (binding.matchField ?? EFFICIENCY_PIN_DEFAULT_MATCH_FIELD).trim() || EFFICIENCY_PIN_DEFAULT_MATCH_FIELD;
  const valueField = (binding.valueField ?? EFFICIENCY_PIN_DEFAULT_VALUE_FIELD).trim() || EFFICIENCY_PIN_DEFAULT_VALUE_FIELD;
  const resolved = resolvedOverride ?? block.resolved;
  const row = workCenter ? findWorkCenterRow(resolved, workCenter, matchField) : null;
  const efficiencyPct = row ? finiteNumber(row[valueField]) : null;
  const appointmentCount = row ? finiteNumber(row.appointment_count) : null;
  const status = workCenter
    ? classifyEfficiencyPinPct(efficiencyPct, binding.bands)
    : "unknown";
  const label =
    workCenter ||
    (typeof block.content === "string" && block.content.trim() ? block.content.trim() : "CT");
  return {
    status: workCenter && !row && resolved ? "unknown" : status,
    color: colorForEfficiencyPinStatus(
      workCenter && !row && resolved ? "unknown" : status,
    ),
    efficiencyPct,
    workCenter,
    appointmentCount,
    label,
  };
}
