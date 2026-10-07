import {
  createDataSourceBlock,
  type ComunicadoBlock,
  type ComunicadoConfig,
  type ComunicadoDataBinding,
  type DataParamValue,
} from "@delpi/tv-dashboard-presentation";
import {
  mapEnrichedBlockToDataRoutePreview,
  primaryDataRouteDisplayKind,
  resolveDataRouteDisplayKinds,
  type DataRoutePreviewPayload,
} from "@delpi/plugin-ui/index";

import type { TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import {
  requestDataPreviewBlock,
  serializeNativeConfigForPreview,
} from "./dataPreviewRequest";

export type PreviewTvDataRouteParams = {
  route: TvDataRouteCatalogItem;
  /** Bloco fonte (ou qualquer com dataBinding) — params/rótulo atuais. */
  block: ComunicadoBlock & { dataBinding: ComunicadoDataBinding };
  config: ComunicadoConfig;
  playlistId?: string;
  /** dataDefaults live da programação. */
  playlistDefaults?: Record<string, unknown> | null;
  /** Filtros do slide preenchidos só onde o bloco não define o param. */
  slideFilters?: Record<string, unknown>;
  /** Draft do Filtro (`input.defaultValue`) — aplicado no clone do config. */
  inputDraft?: { blockId: string; defaultValue: DataParamValue } | null;
};

/** Config do preview com o draft do Filtro; «Dado específico» passa a mirar o probe. */
function applyInputDraft(
  config: ComunicadoConfig,
  draft: PreviewTvDataRouteParams["inputDraft"],
  sourceBlockId: string,
  probeId: string,
): ComunicadoConfig {
  if (!draft) return config;
  return {
    ...config,
    blocks: (config.blocks ?? []).map((item) => {
      if (item.id !== draft.blockId || item.type !== "input") return item;
      const targets = item.input.targetSourceIds ?? [];
      return {
        ...item,
        input: {
          ...item.input,
          defaultValue: draft.defaultValue,
          ...(targets.includes(sourceBlockId) ? { targetSourceIds: [...targets, probeId] } : {}),
        },
      };
    }),
  };
}

/** Sugestão de forma no preview (não restringe o payload — data_source resolve kpi+table+chart). */
function suggestedPreviewKind(route: TvDataRouteCatalogItem): "kpi" | "series" | "table" {
  return primaryDataRouteDisplayKind(
    resolveDataRouteDisplayKinds({
      metaShape: route.metaShape,
      allowedDisplayModes: route.allowedDisplayModes ?? route.suggestedDisplayModes,
    }),
    route.metaShape,
  );
}

/**
 * Chama preview-block com a rota/params atuais e devolve payload tipado do catálogo.
 * O kind do catálogo só prioriza qual fatia mostrar; a fonte resolve os três formatos.
 */
export async function previewTvDataRoute(
  args: PreviewTvDataRouteParams,
): Promise<DataRoutePreviewPayload> {
  const {
    route,
    block,
    config,
    playlistId,
    playlistDefaults = null,
    slideFilters = {},
    inputDraft = null,
  } = args;
  const preferred = suggestedPreviewKind(route);
  const binding = block.dataBinding;
  const params: NonNullable<ComunicadoDataBinding["params"]> = {
    ...(binding.params ?? {}),
  };
  for (const [key, value] of Object.entries(slideFilters)) {
    if ((params[key] === undefined || params[key] === "") && value != null && value !== "") {
      params[key] = value as string | number | boolean;
    }
  }

  const probe = createDataSourceBlock(route.operationId, {
    label: binding.label?.trim() || undefined,
    defaultParams: params,
    refreshSec: binding.refreshSec,
  });
  if (probe.dataBinding) {
    // Neutro: enrichment de data_source sempre monta kpi + chart + table.
    probe.dataBinding.displayMode = "auto";
    if (binding.selectedValueFields?.length) {
      probe.dataBinding.selectedValueFields = [...binding.selectedValueFields];
    }
    if (binding.valueField) {
      probe.dataBinding.valueField = binding.valueField;
    }
    if (binding.maxRows != null) {
      probe.dataBinding.maxRows = binding.maxRows;
    }
  }

  const previewConfig = applyInputDraft(config, inputDraft, block.id, probe.id);
  const response = await requestDataPreviewBlock({
    block: probe as unknown as Record<string, unknown>,
    nativeConfig: serializeNativeConfigForPreview({
      ...previewConfig,
      blocks: [...(previewConfig.blocks ?? []).filter((item) => item.id !== probe.id), probe],
    }),
    playlistId,
    playlistDefaults,
    forceRefresh: true,
  });

  return mapEnrichedBlockToDataRoutePreview(
    (response.block ?? {}) as Record<string, unknown>,
    preferred,
  );
}
