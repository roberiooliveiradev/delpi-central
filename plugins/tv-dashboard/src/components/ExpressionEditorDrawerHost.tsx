/**
 * Host do drawer de expressão — lê `expressionEditRequest` do contexto do
 * editor e conecta o preview backend (`previewTvDataRoute`) com o draft.
 * Montado ao lado do `DataCatalogModalHost` nas duas superfícies do editor.
 */
import { useCallback, useMemo } from "react";
import type {
  ComunicadoBlock,
  ComunicadoDataBinding,
  ParamExpressionSpec,
} from "@delpi/tv-dashboard-presentation";

import { useParamExpressionCapability } from "../hooks/useParamExpressionCapability";
import { useTvDataRouteLabelCatalog } from "../hooks/useTvDataRouteLabelCatalog";
import {
  applyDataParamRawUpdates,
  buildParamValueUpdates,
} from "../utils/applyDataParamUpdates";
import { previewTvDataRoute } from "../utils/previewTvDataRoute";
import { resolveRouteForDataBoundBlock } from "../utils/resolveDataBoundBlockRoute";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import {
  visibleParamSchema,
  type DataParamSchema,
} from "../utils/dataParamSchema";
import { ExpressionEditorDrawer } from "./ExpressionEditorDrawer";

export function ExpressionEditorDrawerHost() {
  const {
    expressionEditRequest,
    closeExpressionEditor,
    blocks,
    config,
    playlistId,
    playlistDefaults,
  } = useComunicadoEditor();
  const { routes } = useTvDataRouteLabelCatalog({
    enabled: expressionEditRequest != null,
  });
  const support = useParamExpressionCapability();

  const previewBlock = useMemo(() => {
    const id = expressionEditRequest?.previewBlockId;
    if (!id) return null;
    const found = blocks.find(
      (block) => block.id === id && "dataBinding" in block,
    );
    return (found as
      | (ComunicadoBlock & { dataBinding: ComunicadoDataBinding })
      | undefined) ?? null;
  }, [blocks, expressionEditRequest]);

  const route = useMemo(
    () =>
      resolveRouteForDataBoundBlock(
        previewBlock,
        blocks,
        routes,
        config.dataModels,
      ),
    [previewBlock, blocks, routes, config.dataModels],
  );

  const paramSchema = useMemo(
    () =>
      visibleParamSchema(
        (route?.paramSchema ?? undefined) as DataParamSchema | undefined,
        route?.fixedQueryParams,
      ),
    [route],
  );

  // Preview do DRAFT: aplica o spec no clone do binding e chama o
  // preview-block real — sem avaliador no frontend.
  const onPreview = useCallback(
    async (spec: ParamExpressionSpec) => {
      if (!expressionEditRequest || !previewBlock || !route) return null;
      const nextParams = applyDataParamRawUpdates(
        previewBlock.dataBinding.params,
        buildParamValueUpdates(expressionEditRequest.paramKey, spec, {
          schema: paramSchema,
          values: previewBlock.dataBinding.params,
        }),
        paramSchema,
      );
      return previewTvDataRoute({
        route,
        block: {
          ...previewBlock,
          dataBinding: { ...previewBlock.dataBinding, params: nextParams },
        },
        config,
        playlistId,
        playlistDefaults,
        slideFilters: config.dataFilters,
      });
    },
    [
      expressionEditRequest,
      previewBlock,
      route,
      paramSchema,
      config,
      playlistId,
      playlistDefaults,
    ],
  );

  if (!expressionEditRequest) return null;

  return (
    <ExpressionEditorDrawer
      key={`${expressionEditRequest.previewBlockId ?? "none"}:${expressionEditRequest.paramKey}`}
      open
      request={expressionEditRequest}
      support={support}
      onPreview={previewBlock && route ? onPreview : undefined}
      onClose={closeExpressionEditor}
    />
  );
}
