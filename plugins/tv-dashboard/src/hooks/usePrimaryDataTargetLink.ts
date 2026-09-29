import {
  buildCanvasTableDataLinkPatch,
  buildTextDataLinkPatch,
  buildViewDataLinkPatch,
  consolidateTextBindingToProjection,
  findDataModel,
  isCanvasTableDataBoundBlockType,
  isDataSourceBlockType,
  isDataViewBlockType,
  isTextDataBoundBlock,
  readEffectiveTextProjection,
  resolveTextBindingOwner,
  staticLabelFromTextBoundBlock,
  type ComunicadoBlock,
  type ViewFieldTypes,
} from "@delpi/tv-dashboard-presentation";
import { useCallback } from "react";

import { useComunicadoEditor } from "../components/comunicadoEditorContext";

/**
 * Vínculo do bloco primário a fonte/DataModel — owner único do fluxo de
 * ligação usado pela aba Dados (painel) e pela ribbon (flyout de Fonte).
 * Escreve via `updateSelected`/`setDataPanelIntent` — mesma regra em ambos.
 */
export function usePrimaryDataTargetLink(options?: {
  /** Rota da fonte ligada — enriquece o patch de view (fieldTypes). */
  fieldTypes?: ViewFieldTypes;
}) {
  const { blocks, config, selected, updateSelected, setDataPanelIntent, getDataPreviewResolved } =
    useComunicadoEditor();
  const fieldTypes = options?.fieldTypes ?? null;

  const linkModel = useCallback(
    (primary: ComunicadoBlock, modelId: string) => {
      const trimmed = modelId.trim();
      if (!trimmed) return;
      const model = findDataModel(config, trimmed);
      if (!model) return;
      const resolved = getDataPreviewResolved?.(trimmed);
      if (isDataViewBlockType(primary.type)) {
        const patch = buildViewDataLinkPatch({
          viewType: primary.type,
          dataSourceId: "",
          modelId: trimmed,
          resolved,
          fieldTypes,
          currentFrame: primary.frame,
          existing: {
            kpiProjection: "kpiProjection" in primary ? primary.kpiProjection : undefined,
            chartProjection: "chartProjection" in primary ? primary.chartProjection : undefined,
            tableProjection: "tableProjection" in primary ? primary.tableProjection : undefined,
          },
          chartType: primary.type === "chart_view" ? primary.chartType : undefined,
        });
        updateSelected(patch as Partial<ComunicadoBlock>);
        setDataPanelIntent("binding");
        return;
      }
      if (isTextDataBoundBlock(primary)) {
        const effective = readEffectiveTextProjection(primary);
        const patch = buildTextDataLinkPatch({
          dataSourceId: "",
          modelId: trimmed,
          resolved,
          existing: effective.field?.trim() ? effective : primary.textProjection,
          staticContent: staticLabelFromTextBoundBlock(primary),
        });
        if (resolveTextBindingOwner(primary) === "contentRuns") {
          const consolidated = consolidateTextBindingToProjection(primary, {
            ...(patch.textProjection ?? effective),
          });
          updateSelected({
            ...patch,
            textProjection: consolidated.textProjection ?? patch.textProjection,
            contentRuns: consolidated.contentRuns,
          } as Partial<ComunicadoBlock>);
          setDataPanelIntent("binding");
          return;
        }
        updateSelected(patch as Partial<ComunicadoBlock>);
        setDataPanelIntent("binding");
        return;
      }
      if (isCanvasTableDataBoundBlockType(primary.type) && primary.type === "canvas_table") {
        const patch = buildCanvasTableDataLinkPatch({
          dataSourceId: "",
          modelId: trimmed,
          resolved,
          existingCells: primary.cells,
        });
        updateSelected(patch as Partial<ComunicadoBlock>);
        setDataPanelIntent("binding");
      }
    },
    [config, fieldTypes, getDataPreviewResolved, setDataPanelIntent, updateSelected],
  );

  const linkSource = useCallback(
    (primary: ComunicadoBlock, sourceId: string) => {
      const trimmed = sourceId.trim();
      if (!trimmed) {
        updateSelected({
          dataSourceId: undefined,
          modelId: undefined,
        } as Partial<ComunicadoBlock>);
        return;
      }
      const source = blocks.find(
        (block) => block.id === trimmed && isDataSourceBlockType(block.type),
      );
      if (!source) return;
      const resolved = "resolved" in source ? source.resolved : undefined;
      if (isDataViewBlockType(primary.type)) {
        const patch = buildViewDataLinkPatch({
          viewType: primary.type,
          dataSourceId: trimmed,
          resolved,
          fieldTypes,
          currentFrame: primary.frame,
          existing: {
            kpiProjection: "kpiProjection" in primary ? primary.kpiProjection : undefined,
            chartProjection: "chartProjection" in primary ? primary.chartProjection : undefined,
            tableProjection: "tableProjection" in primary ? primary.tableProjection : undefined,
          },
          chartType: primary.type === "chart_view" ? primary.chartType : undefined,
        });
        updateSelected(patch as Partial<ComunicadoBlock>);
        setDataPanelIntent("binding");
        return;
      }
      if (isTextDataBoundBlock(primary)) {
        const effective = readEffectiveTextProjection(primary);
        const patch = buildTextDataLinkPatch({
          dataSourceId: trimmed,
          resolved,
          existing: effective.field?.trim() ? effective : primary.textProjection,
          staticContent: staticLabelFromTextBoundBlock(primary),
        });
        if (resolveTextBindingOwner(primary) === "contentRuns") {
          const consolidated = consolidateTextBindingToProjection(primary, {
            ...(patch.textProjection ?? effective),
          });
          updateSelected({
            ...patch,
            textProjection: consolidated.textProjection ?? patch.textProjection,
            contentRuns: consolidated.contentRuns,
          } as Partial<ComunicadoBlock>);
          setDataPanelIntent("binding");
          return;
        }
        updateSelected(patch as Partial<ComunicadoBlock>);
        setDataPanelIntent("binding");
        return;
      }
      if (isCanvasTableDataBoundBlockType(primary.type) && primary.type === "canvas_table") {
        const patch = buildCanvasTableDataLinkPatch({
          dataSourceId: trimmed,
          resolved,
          existingCells: primary.cells,
        });
        updateSelected(patch as Partial<ComunicadoBlock>);
        setDataPanelIntent("binding");
      }
    },
    [blocks, fieldTypes, setDataPanelIntent, updateSelected],
  );

  const unlink = useCallback(
    (primary: ComunicadoBlock) => {
      updateSelected({
        dataSourceId: undefined,
        modelId: undefined,
      } as Partial<ComunicadoBlock>);
    },
    [updateSelected],
  );

  return { linkSource, linkModel, unlink, primary: selected };
}
