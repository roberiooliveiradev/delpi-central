/**
 * Fluxo universal: ao ligar fonte ↔ visual (ou quando o resolved chega),
 * materializa *Projection e dimensiona o frame do bloco.
 *
 * Único ponto de verdade — não espalhar suggestDefaultProjections + resize
 * só no inspector.
 */

import { isDataViewBlockType } from "./comunicadoDataArchitecture";
import type {
  ComunicadoBlock,
  ComunicadoChartViewBlock,
  ComunicadoDataResolved,
  ComunicadoFrame,
  ComunicadoKpiViewBlock,
  ComunicadoTableViewBlock,
} from "./comunicadoTypes";
import {
  suggestDefaultProjections,
  type ChartViewProjection,
  type KpiViewProjection,
  type TableViewProjection,
} from "./viewProjection";

export type DataViewBlockType = "kpi_view" | "chart_view" | "table_view";

export type ViewFieldTypes = Record<string, "number" | "string" | "date"> | null | undefined;

/** Espelha DECK_KPI_DEFAULTS.frame — evita acoplar theme no módulo de sync. */
const KPI_DEFAULT_FRAME = { w: 12, h: 7 } as const;
const KPI_CELL = { w: 14, h: 10 };
const KPI_GAP = 1;
const KPI_MAX_COLS = 4;
const FRAME_EPS = 2.5;

export function viewHasProjectionConfigured(block: ComunicadoBlock): boolean {
  if (block.type === "kpi_view") {
    return Boolean(block.kpiProjection?.metrics?.some((m) => m.visible !== false));
  }
  if (block.type === "chart_view") {
    return Boolean(block.chartProjection?.series?.length);
  }
  if (block.type === "table_view") {
    return Boolean(block.tableProjection?.columns?.some((c) => c.visible !== false));
  }
  return true;
}

/** Contagem de itens que influenciam o layout do frame. */
export function countViewLayoutItems(
  block: Pick<ComunicadoBlock, "type"> & {
    kpiProjection?: KpiViewProjection;
    chartProjection?: ChartViewProjection;
    tableProjection?: TableViewProjection;
  },
): number {
  if (block.type === "kpi_view") {
    const metrics = block.kpiProjection?.metrics?.filter((m) => m.visible !== false) ?? [];
    return Math.max(1, metrics.length);
  }
  if (block.type === "chart_view") {
    return Math.max(1, block.chartProjection?.series?.length ?? 1);
  }
  if (block.type === "table_view") {
    const cols = block.tableProjection?.columns?.filter((c) => c.visible !== false) ?? [];
    return Math.max(1, cols.length);
  }
  return 1;
}

function nearSize(a: number, b: number, eps = FRAME_EPS): boolean {
  return Math.abs(a - b) <= eps;
}

export function isNearDefaultKpiFrame(frame: ComunicadoFrame): boolean {
  return nearSize(frame.w, KPI_DEFAULT_FRAME.w) && nearSize(frame.h, KPI_DEFAULT_FRAME.h);
}

/**
 * Sugere w/h do frame (% do slide) para caber o visual.
 * Política: default compacto → substitui; senão grow-only.
 */
export function suggestViewFrameSize(
  viewType: DataViewBlockType,
  itemCount: number,
  current: ComunicadoFrame,
): ComunicadoFrame {
  const count = Math.max(1, Math.round(itemCount));

  if (viewType === "kpi_view") {
    if (count <= 1) return { ...current };
    const cols = Math.min(KPI_MAX_COLS, count);
    const rows = Math.ceil(count / cols);
    const targetW = Math.min(92, cols * KPI_CELL.w + Math.max(0, cols - 1) * KPI_GAP);
    const targetH = Math.min(72, rows * KPI_CELL.h + Math.max(0, rows - 1) * KPI_GAP);
    if (isNearDefaultKpiFrame(current)) {
      return {
        ...current,
        w: targetW,
        h: targetH,
        x: Math.min(current.x, Math.max(0, 100 - targetW)),
        y: Math.min(current.y, Math.max(0, 100 - targetH)),
      };
    }
    return {
      ...current,
      w: Math.max(current.w, targetW),
      h: Math.max(current.h, targetH),
    };
  }

  if (viewType === "chart_view") {
    const targetW = count > 1 ? 80 : current.w;
    const targetH = count > 1 ? Math.max(current.h, 45) : current.h;
    return {
      ...current,
      w: Math.max(current.w, Math.min(92, targetW)),
      h: Math.max(current.h, Math.min(70, targetH)),
    };
  }

  const targetW = Math.min(92, Math.max(36, 16 + count * 7));
  const targetH = Math.max(current.h, 28);
  return {
    ...current,
    w: Math.max(current.w, targetW),
    h: Math.max(current.h, targetH),
  };
}

export function framesDiffer(a: ComunicadoFrame, b: ComunicadoFrame): boolean {
  return (
    !nearSize(a.w, b.w, 0.51) ||
    !nearSize(a.h, b.h, 0.51) ||
    !nearSize(a.x, b.x, 0.51) ||
    !nearSize(a.y, b.y, 0.51)
  );
}

export type BuildViewDataLinkPatchInput = {
  viewType: DataViewBlockType;
  dataSourceId: string;
  resolved?: ComunicadoDataResolved;
  fieldTypes?: ViewFieldTypes;
  currentFrame: ComunicadoFrame;
  existing?: {
    kpiProjection?: KpiViewProjection;
    chartProjection?: ChartViewProjection;
    tableProjection?: TableViewProjection;
  };
  fitFrame?: boolean;
};

/**
 * Patch canônico ao conectar fonte a um visual (ou quando resolved chega).
 */
export function buildViewDataLinkPatch(
  input: BuildViewDataLinkPatchInput,
): Partial<ComunicadoKpiViewBlock & ComunicadoChartViewBlock & ComunicadoTableViewBlock> {
  const {
    viewType,
    dataSourceId,
    resolved,
    fieldTypes,
    currentFrame,
    existing,
    fitFrame = true,
  } = input;

  const suggested = suggestDefaultProjections(resolved, fieldTypes);
  const patch: Partial<ComunicadoKpiViewBlock & ComunicadoChartViewBlock & ComunicadoTableViewBlock> =
    {
      dataSourceId,
    };

  let kpiProjection = existing?.kpiProjection;
  let chartProjection = existing?.chartProjection;
  let tableProjection = existing?.tableProjection;

  if (viewType === "kpi_view") {
    if (!kpiProjection?.metrics?.length && suggested.kpiProjection) {
      kpiProjection = suggested.kpiProjection;
      patch.kpiProjection = kpiProjection;
    }
  } else if (viewType === "chart_view") {
    if (!chartProjection?.series?.length && suggested.chartProjection) {
      chartProjection = suggested.chartProjection;
      patch.chartProjection = chartProjection;
    }
  } else if (viewType === "table_view") {
    if (!tableProjection?.columns?.length && suggested.tableProjection) {
      tableProjection = suggested.tableProjection;
      patch.tableProjection = tableProjection;
    }
  }

  if (fitFrame) {
    const layoutBlock = {
      type: viewType,
      kpiProjection,
      chartProjection,
      tableProjection,
    };
    const count = countViewLayoutItems(layoutBlock);
    const nextFrame = suggestViewFrameSize(viewType, count, currentFrame);
    if (framesDiffer(currentFrame, nextFrame)) {
      patch.frame = nextFrame;
    }
  }

  return patch;
}

/** Só redimensiona o frame a partir da projection atual (ex.: editor de métricas). */
export function buildViewFrameFitPatch(
  block: ComunicadoBlock,
): Partial<Pick<ComunicadoBlock, "frame">> | null {
  if (!isDataViewBlockType(block.type)) return null;
  const count = countViewLayoutItems(block);
  const nextFrame = suggestViewFrameSize(block.type, count, block.frame);
  if (!framesDiffer(block.frame, nextFrame)) return null;
  return { frame: nextFrame };
}

/**
 * Percorre o deck e aplica projection + frame quando a fonte já tem resolved
 * e o visual ainda não materializou a projection (ou o frame ficou apertado).
 */
export function syncDataViewBlocksWithResolved(
  blocks: ComunicadoBlock[],
  resolvedBySourceId: Record<string, ComunicadoDataResolved | undefined>,
  fieldTypesBySourceId?: Record<string, ViewFieldTypes>,
): { next: ComunicadoBlock[]; changedIds: string[] } {
  const changedIds: string[] = [];
  const next = blocks.map((block) => {
    if (!isDataViewBlockType(block.type)) return block;
    const sourceId =
      "dataSourceId" in block && typeof block.dataSourceId === "string"
        ? block.dataSourceId.trim()
        : "";
    if (!sourceId) return block;

    const resolved = resolvedBySourceId[sourceId];
    const fieldTypes = fieldTypesBySourceId?.[sourceId];
    const hasProjection = viewHasProjectionConfigured(block);

    if (!hasProjection) {
      if (!resolved) return block;
      const patch = buildViewDataLinkPatch({
        viewType: block.type,
        dataSourceId: sourceId,
        resolved,
        fieldTypes,
        currentFrame: block.frame,
        existing: {
          kpiProjection: "kpiProjection" in block ? block.kpiProjection : undefined,
          chartProjection: "chartProjection" in block ? block.chartProjection : undefined,
          tableProjection: "tableProjection" in block ? block.tableProjection : undefined,
        },
      });
      const wroteProjection =
        Boolean(patch.kpiProjection) ||
        Boolean(patch.chartProjection) ||
        Boolean(patch.tableProjection);
      if (!wroteProjection && !patch.frame) return block;
      changedIds.push(block.id);
      return { ...block, ...patch } as ComunicadoBlock;
    }

    // Projection já existe: só corrige frame ainda no tamanho “card único” com multi.
    if (
      block.type === "kpi_view" &&
      isNearDefaultKpiFrame(block.frame) &&
      countViewLayoutItems(block) > 1
    ) {
      const framePatch = buildViewFrameFitPatch(block);
      if (!framePatch) return block;
      changedIds.push(block.id);
      return { ...block, ...framePatch } as ComunicadoBlock;
    }
    return block;
  });

  return { next, changedIds };
}
