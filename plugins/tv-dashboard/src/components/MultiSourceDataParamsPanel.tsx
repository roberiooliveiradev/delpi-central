import { useMemo } from "react";
import type { BranchScope } from "../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { useTvDataRouteLabelCatalog } from "../hooks/useTvDataRouteLabelCatalog";
import {
  buildMultiSourceParamPatches,
  buildMultiSourceParamSchema,
  isMultiSourceBindingTarget,
  resolveSharedParamDisplayValues,
  type MultiSourceBindingTarget,
} from "../utils/multiSourceDataParams";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import { DataParamFields } from "./DataParamFields";
import { DeckPropertySection } from "./deck/DeckPropertySection";
import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

type Props = {
  targets: ComunicadoBlock[];
  branchScope?: BranchScope | null;
};

/**
 * Filtros unificados da multi-seleção de dados (fontes distintas).
 * Schema = união das rotas sem repetir chave; alteração aplica-se a todas as fontes que aceitam o campo.
 */
export function MultiSourceDataParamsPanel({ targets, branchScope = null }: Props) {
  const { updateBlocksAtomically } = useComunicadoEditor();
  const { routes } = useTvDataRouteLabelCatalog();

  const bindingTargets = useMemo(
    () => targets.filter(isMultiSourceBindingTarget),
    [targets],
  );

  const schema = useMemo(
    () => buildMultiSourceParamSchema(routes, bindingTargets),
    [routes, bindingTargets],
  );

  const shared = useMemo(
    () => resolveSharedParamDisplayValues(bindingTargets, schema),
    [bindingTargets, schema],
  );

  if (bindingTargets.length === 0) {
    return (
      <DeckPropertySection pane title="Dados" defaultOpen>
        <p className="td-deck-inspector__hint">
          {TV_DASHBOARD_HELP_TOOLTIPS.data.multiSelectNoSources}
        </p>
      </DeckPropertySection>
    );
  }

  if (Object.keys(schema).length === 0) {
    return (
      <DeckPropertySection pane title="Filtros das fontes" defaultOpen>
        <p className="td-deck-inspector__hint">
          {TV_DASHBOARD_HELP_TOOLTIPS.data.multiSelectEmptySchema}
        </p>
      </DeckPropertySection>
    );
  }

  function updateParams(updates: Record<string, string>) {
    const patches = buildMultiSourceParamPatches(
      bindingTargets as MultiSourceBindingTarget[],
      routes,
      updates,
    );
    if (patches.length === 0) return;
    updateBlocksAtomically(patches);
  }

  return (
    <DeckPropertySection
      pane
      title="Filtros das fontes"
      hint={TV_DASHBOARD_HELP_TOOLTIPS.data.multiSelectFilters}
      defaultOpen
    >
      <p className="td-deck-inspector__hint td-deck-inspector__hint--stage">
        {TV_DASHBOARD_HELP_TOOLTIPS.data.multiSelectFiltersSummary.replace(
          "{count}",
          String(bindingTargets.length),
        )}
      </p>
      <DataParamFields
        schema={schema}
        values={shared.values}
        divergedKeys={shared.divergedKeys}
        branchScope={branchScope}
        idPrefix="td-multi-source-filter"
        hydrateDefaultPreset={false}
        onChange={updateParams}
      />
    </DeckPropertySection>
  );
}
