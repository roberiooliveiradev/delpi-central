import { useCallback, useMemo } from "react";
import {
  bindingTargetId,
  bindingTargetKind,
  isDataSourceBlockType,
  resolveDataSourceLabel,
  type ComunicadoBlock,
  type ComunicadoDataBinding,
  type ComunicadoDataResolved,
  type ComunicadoDataSourceBlock,
} from "@delpi/tv-dashboard-presentation";

import type { TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import { useComunicadoEditor } from "../components/comunicadoEditorContext";
import { useParamExpressionCapability } from "./useParamExpressionCapability";
import { useTvDataRouteLabelCatalog } from "./useTvDataRouteLabelCatalog";
import { applyDataParamRawUpdates, type DataParamUpdateValue } from "../utils/applyDataParamUpdates";
import { resolveParamFieldLabel } from "../content/dataParamCatalog";
import {
  paramAllowsExpression,
  paramFormatToReturnTypes,
  paramTypeToReturnTypes,
} from "../utils/paramExpressions";
import {
  visibleParamSchema,
  type DataParamSchema,
  type DataParamSchemaField,
} from "../utils/dataParamSchema";
import { resolveRouteForDataBoundBlock } from "../utils/resolveDataBoundBlockRoute";
import { resolveSelectedDataContext, type SelectedDataContext } from "../utils/selectedDataContext";

/** Parâmetro elegível a expressão tipada — projeção canônica do model. */
export type RibbonExpressionParam = {
  key: string;
  field: DataParamSchemaField;
  label: string;
  expectedReturnTypes: ReadonlySet<string> | null;
};

export type DataRibbonModel = {
  context: SelectedDataContext;
  /** Bloco selecionado representativo (visual/texto/fonte). */
  primary: ComunicadoBlock | null;
  /** Dono dos params editáveis (fonte ligada ou próprio bloco). */
  bindingTarget: (ComunicadoBlock & { dataBinding?: ComunicadoDataBinding }) | null;
  route: TvDataRouteCatalogItem | null;
  binding: ComunicadoDataBinding | null;
  params: Record<string, string | number | boolean | null | undefined> | undefined;
  paramSchema: DataParamSchema;
  /** `resolved` enriquecido do backend (preview da fonte ligada). */
  resolved: ComunicadoDataResolved | undefined;
  /** Rótulo da fonte/modelo ligado e total de fontes na seleção (§70 "+2"). */
  targetLabel: string;
  targetCount: number;
  /** Catálogo de rótulos de rotas (compartilhado com inspector/flyouts). */
  labelCatalog: ReturnType<typeof useTvDataRouteLabelCatalog>["labelCatalog"];
  expressionSupport: ReturnType<typeof useParamExpressionCapability>;
  /**
   * Params editáveis por expressão — mesmo predicado do backend
   * (`paramAllowsExpression` + fixedQueryParams + capability).
   */
  expressionParams: RibbonExpressionParam[];
  /** Patch de params — mesma regra do inspector (`applyDataParamRawUpdates`). */
  updateParams: (updates: Record<string, DataParamUpdateValue>) => void;
  /** Patch do binding inteiro (ex.: refreshSec, label). */
  applyBinding: (patch: Partial<ComunicadoDataBinding>) => void;
};

/**
 * Modelo canônico da aba/ribbon «Dados» — projeção do estado do editor
 * (mesmos `blocks`/`config`/`updateBlock` do painel lateral; §40/§92).
 */
export function useDataRibbonModel(): DataRibbonModel {
  const {
    blocks,
    config,
    selectedIds,
    updateBlock,
    getDataPreviewResolved,
  } = useComunicadoEditor();
  const { routes, labelCatalog } = useTvDataRouteLabelCatalog();
  const expressionSupport = useParamExpressionCapability();

  const context = useMemo(
    () => resolveSelectedDataContext(blocks, selectedIds, config.dataModels),
    [blocks, selectedIds, config.dataModels],
  );
  const { primary, bindingTarget, bindingTargets, bindingModel } = context;

  const route = useMemo(
    () => resolveRouteForDataBoundBlock(bindingTarget, blocks, routes, config.dataModels),
    [bindingTarget, blocks, config.dataModels, routes],
  );

  const binding =
    bindingTarget && "dataBinding" in bindingTarget
      ? (bindingTarget.dataBinding ?? null)
      : null;
  const params = binding?.params;
  const paramSchema = useMemo(
    () =>
      visibleParamSchema(
        (route?.paramSchema ?? undefined) as DataParamSchema | undefined,
        route?.fixedQueryParams,
      ),
    [route],
  );

  const resolved = useMemo(() => {
    if (!bindingTarget) return undefined;
    if (bindingModel) {
      return getDataPreviewResolved?.(bindingModel.id) ?? bindingModelResolvedFallback(bindingTarget);
    }
    if ("resolved" in bindingTarget && bindingTarget.resolved) {
      return bindingTarget.resolved as ComunicadoDataResolved;
    }
    return getDataPreviewResolved?.(bindingTarget.id);
  }, [bindingModel, bindingTarget, getDataPreviewResolved]);

  const targetLabel = useMemo(() => {
    if (bindingModel) return bindingModel.label?.trim() || bindingModel.id;
    if (!bindingTarget) return "";
    if (isDataSourceBlockType(bindingTarget.type)) {
      return resolveDataSourceLabel(
        bindingTarget as ComunicadoDataSourceBlock,
        labelCatalog,
      );
    }
    const label = binding?.label?.trim();
    return label || route?.label || "";
  }, [binding, bindingModel, bindingTarget, labelCatalog, route]);

  const updateParams = useCallback(
    (updates: Record<string, DataParamUpdateValue>) => {
      if (!bindingTarget || !binding) return;
      const nextParams = applyDataParamRawUpdates(binding.params, updates, paramSchema);
      updateBlock(bindingTarget.id, {
        dataBinding: { ...binding, params: nextParams },
      } as Partial<ComunicadoBlock>);
    },
    [binding, bindingTarget, paramSchema, updateBlock],
  );

  const expressionParams = useMemo<RibbonExpressionParam[]>(() => {
    if (!expressionSupport.enabled) return [];
    const fixedKeys = new Set(Object.keys(route?.fixedQueryParams ?? {}));
    return Object.entries(paramSchema)
      .filter(([key, field]) => paramAllowsExpression(key, field, fixedKeys))
      .map(([key, field]) => ({
        key,
        field,
        label: resolveParamFieldLabel(key, field.label),
        expectedReturnTypes:
          paramFormatToReturnTypes(field.format) ??
          paramTypeToReturnTypes(field.type),
      }));
  }, [expressionSupport.enabled, paramSchema, route]);

  const applyBinding = useCallback(
    (patch: Partial<ComunicadoDataBinding>) => {
      if (!bindingTarget || !binding) return;
      updateBlock(bindingTarget.id, {
        dataBinding: { ...binding, ...patch },
      } as Partial<ComunicadoBlock>);
    },
    [binding, bindingTarget, updateBlock],
  );

  return {
    context,
    primary: primary ?? null,
    bindingTarget: bindingTarget as DataRibbonModel["bindingTarget"],
    route,
    binding,
    params: params as DataRibbonModel["params"],
    paramSchema,
    resolved,
    targetLabel,
    targetCount: bindingTargets.length,
    labelCatalog,
    expressionSupport,
    expressionParams,
    updateParams,
    applyBinding,
  };
}

function bindingModelResolvedFallback(
  target: ComunicadoBlock & { dataBinding?: ComunicadoDataBinding },
): ComunicadoDataResolved | undefined {
  return "resolved" in target && target.resolved
    ? (target.resolved as ComunicadoDataResolved)
    : undefined;
}

/** `model:` vs fonte — target ativo do primário para o seletor unificado. */
export function primaryTargetIds(primary: ComunicadoBlock | null): {
  sourceId: string;
  modelId: string;
} {
  if (!primary) return { sourceId: "", modelId: "" };
  const targetId = bindingTargetId(primary);
  if (!targetId) return { sourceId: "", modelId: "" };
  return bindingTargetKind(primary) === "model"
    ? { sourceId: "", modelId: targetId }
    : { sourceId: targetId, modelId: "" };
}
