import {
  bindingTargetId,
  bindingTargetKind,
  catalogFieldsFromRouteLabels,
  consolidateTextBindingToProjection,
  discoverResolvedFieldOptions,
  findDataModel,
  isComunicadoVisualBoxBlock,
  readEffectiveTextProjection,
  type ComunicadoBlock,
  type ComunicadoTextProjection,
} from "@delpi/tv-dashboard-presentation";
import { useCallback, useMemo } from "react";

import type { TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import { useComunicadoEditor } from "../components/comunicadoEditorContext";

export type TextProjectionModel = {
  /** Caixa visual com vínculo de texto (ou null). */
  visualBox: ComunicadoBlock | null;
  /** Projeção efetiva (respeita owner paint vs textProjection). */
  projection: ComunicadoTextProjection;
  fieldOptions: Array<{ field: string; label: string }>;
  patchProjection: (patch: Partial<ComunicadoTextProjection>) => void;
};

/**
 * Projeção «campo dinâmico» de texto/forma — owner compartilhado entre
 * `TextDataBindingInspector` (painel) e o flyout «Campo» da ribbon.
 */
export function useTextProjectionModel(
  block: ComunicadoBlock | null,
  route: TvDataRouteCatalogItem | null,
): TextProjectionModel {
  const { blocks, config, updateSelected, getDataPreviewResolved } = useComunicadoEditor();

  const visualBox = block && isComunicadoVisualBoxBlock(block) ? block : null;
  const targetId = visualBox ? bindingTargetId(visualBox) : "";
  const targetKind = visualBox ? bindingTargetKind(visualBox) : "none";
  const linkedModel = targetKind === "model" ? findDataModel(config, targetId) : null;
  const modelResolved = linkedModel ? getDataPreviewResolved?.(linkedModel.id) : undefined;
  const linkedSource =
    targetKind === "source" && targetId
      ? blocks.find((item) => item.id === targetId) ?? null
      : null;
  const resolved =
    modelResolved ??
    (linkedSource && "resolved" in linkedSource && linkedSource.resolved
      ? linkedSource.resolved
      : visualBox && "resolved" in visualBox && visualBox.resolved
        ? visualBox.resolved
        : undefined);

  const catalogFields = useMemo(
    () =>
      catalogFieldsFromRouteLabels(
        route?.valueFields,
        route?.valueFieldLabels,
        route?.projectableFields,
      ),
    [route?.projectableFields, route?.valueFieldLabels, route?.valueFields],
  );

  const fieldOptions = useMemo(
    () =>
      discoverResolvedFieldOptions(
        resolved,
        catalogFields,
        linkedModel?.fieldLabels ??
          (linkedSource && "fieldLabels" in linkedSource
            ? (linkedSource as { fieldLabels?: Record<string, string> }).fieldLabels
            : undefined),
      ),
    [catalogFields, linkedModel, linkedSource, resolved],
  );

  const projection: ComunicadoTextProjection = visualBox
    ? readEffectiveTextProjection(visualBox)
    : { field: "" };

  const patchProjection = useCallback(
    (patch: Partial<ComunicadoTextProjection>) => {
      if (!visualBox) return;
      const consolidated = consolidateTextBindingToProjection(visualBox, patch);
      updateSelected({
        textProjection: consolidated.textProjection,
        contentRuns: consolidated.contentRuns,
        ...(consolidated.content !== undefined ? { content: consolidated.content } : {}),
      } as Partial<typeof visualBox>);
    },
    [updateSelected, visualBox],
  );

  return { visualBox, projection, fieldOptions, patchProjection };
}
