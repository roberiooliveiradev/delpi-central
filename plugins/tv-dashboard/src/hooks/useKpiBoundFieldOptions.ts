import {
  bindingTargetId,
  bindingTargetKind,
  discoverResolvedFieldOptions,
  findDataModel,
  isDataSourceBlockType,
  type ComunicadoDataSourceBlock,
} from "@delpi/tv-dashboard-presentation";
import { useMemo } from "react";

import { useComunicadoEditor } from "../components/comunicadoEditorContext";
import type { ValueFieldOption } from "../components/ValueFieldsMultiSelect";

/** Campos projetáveis do DataModel/fonte ligados ao KPI selecionado. */
export function useKpiBoundFieldOptions(
  blockId: string | undefined,
): ValueFieldOption[] {
  const { selected, blocks, config, getDataPreviewResolved } = useComunicadoEditor();
  const block =
    selected && selected.id === blockId && selected.type === "kpi_view" ? selected : null;

  return useMemo(() => {
    if (!block) return [];
    const targetId = bindingTargetId(block);
    const kind = bindingTargetKind(block);
    if (kind === "model") {
      const model = findDataModel(config, targetId);
      const resolved = model ? getDataPreviewResolved?.(model.id) : undefined;
      return discoverResolvedFieldOptions(resolved, undefined, model?.fieldLabels);
    }
    if (kind === "source" && targetId) {
      const source = blocks.find(
        (item) => item.id === targetId && isDataSourceBlockType(item.type),
      ) as ComunicadoDataSourceBlock | undefined;
      const resolved = source?.resolved;
      return discoverResolvedFieldOptions(resolved, undefined, source?.fieldLabels);
    }
    return [];
  }, [block, blocks, config, getDataPreviewResolved]);
}
