import { useEffect } from "react";
import {
  CalendarDays,
  Database,
  RotateCw,
  Sigma,
  SlidersHorizontal,
  Tag,
} from "lucide-react";
import {
  isDataBoundEditorBlockType,
  resolveDataBlockRefreshSec,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS as H } from "../content/helpTooltips";
import {
  useDataRibbonModel,
  type DataRibbonModel,
} from "../hooks/useDataRibbonModel";
import {
  DATE_RANGE_PRESET_OPTIONS,
  DATE_RANGE_PRESET_PARAM,
} from "../utils/dateRangePresets";
import { isParamExpressionValue } from "../utils/paramExpressions";
import { useComunicadoEditor } from "./comunicadoEditorContext";
import {
  DataRibbonExpressionFlyout,
  DataRibbonFieldControls,
  DataRibbonFieldFlyout,
  DataRibbonMoreFlyout,
  DataRibbonPeriodFlyout,
  DataRibbonRefreshFlyout,
  DataRibbonSourceFlyout,
  DataRibbonSourceSelect,
} from "./DataRibbonControls";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";
import { DeckRibbonGroups } from "./deck/DeckRibbonGroups";
import { DeckRibbonTile } from "./deck/DeckRibbonTile";
import { DeckRibbonTilePopover } from "./deck/DeckRibbonTilePopover";

const GROUP_ORDER = {
  source: 10,
  field: 20,
  period: 30,
  refresh: 40,
  expression: 50,
  more: 60,
} as const;

function periodTileLabel(model: DataRibbonModel): string {
  const raw = String(model.params?.[DATE_RANGE_PRESET_PARAM] ?? "").trim();
  if (!raw) return "Período";
  return (
    DATE_RANGE_PRESET_OPTIONS.find((option) => option.value === raw)?.label ??
    "Período"
  );
}

function expressionTileLabel(model: DataRibbonModel): string {
  const count = Object.values(model.params ?? {}).filter(isParamExpressionValue)
    .length;
  return count > 0 ? `Expressão (${count})` : "Expressão";
}

/**
 * Aba Dados na top bar — grupos reais (Fonte/Campo/Período/Atualização/
 * Expressão/Mais) projetados do mesmo estado do painel lateral via
 * `useDataRibbonModel`. O colapso responsivo (expandido → compacto →
 * mínimo) é o do `DeckRibbonGroups`/`RibbonGroupsRow` — nenhuma lógica
 * de overflow local.
 */
export function ComunicadoDataRibbon() {
  const {
    selected,
    setSelectionPanelTab,
    setDataPanelIntent,
    setDataPanelOpen,
    openDataCatalog,
    globalRefreshSec,
  } = useComunicadoEditor();
  const model = useDataRibbonModel();

  const selectedId = selected?.id ?? "";
  const selectedType = selected?.type;
  useEffect(() => {
    setSelectionPanelTab("data");
    setDataPanelOpen(true);
    const preferCatalog = !selectedType || !isDataBoundEditorBlockType(selectedType);
    setDataPanelIntent(preferCatalog ? "catalog" : "binding");
    // selected object identity muda a cada preview/hydrate — só id/tipo importam.
  }, [selectedId, selectedType, setDataPanelIntent, setDataPanelOpen, setSelectionPanelTab]);

  const hasBinding = model.bindingTarget != null && model.binding != null;
  const hasParams = Object.keys(model.paramSchema).length > 0;
  const hasExpressionSurface =
    hasBinding &&
    (model.expressionParams.length > 0 ||
      Object.values(model.params ?? {}).some(isParamExpressionValue));
  const refreshLabel = hasBinding
    ? `${resolveDataBlockRefreshSec(model.binding ?? undefined, globalRefreshSec)}s`
    : "Atualização";

  return (
    <DeckRibbonGroups>
      {/* Fonte — sempre presente; sem seleção vira onboarding do catálogo. */}
      <DeckRibbonGroup
        groupId="data-source"
        order={GROUP_ORDER.source}
        label="Fonte"
        hint={H.data.dataRibbonSource}
      >
        {model.primary ? (
          <>
            <DataRibbonSourceSelect model={model} />
            <DeckRibbonTilePopover
              icon={Database}
              label={model.targetLabel || "Fonte"}
              hint={H.data.dataRibbonSource}
              panelLabel="Fonte de dados"
            >
              <DataRibbonSourceFlyout model={model} />
            </DeckRibbonTilePopover>
          </>
        ) : (
          <DeckRibbonTile
            icon={Database}
            label="Inserir fonte…"
            hint={H.data.connectFlow}
            onClick={() => openDataCatalog()}
          />
        )}
      </DeckRibbonGroup>

      {model.primary ? (
        <>
          {/* Campo + Agregação — inline para KPI/texto; flyout canônico para
              gráfico/tabela (editor multi-coluna é largo demais para a faixa). */}
          <DeckRibbonGroup
            groupId="data-field"
            order={GROUP_ORDER.field}
            label="Campo"
            hint={H.data.dataRibbonField}
          >
            <DataRibbonFieldControls model={model} />
            <DeckRibbonTilePopover
              icon={Tag}
              label="Campos"
              hint={H.data.dataRibbonField}
              panelLabel="Campos do visual"
            >
              <DataRibbonFieldFlyout model={model} />
            </DeckRibbonTilePopover>
          </DeckRibbonGroup>

          {/* Período — recorte do DataParamFields canônico (preset + datas). */}
          <DeckRibbonGroup
            groupId="data-period"
            order={GROUP_ORDER.period}
            label="Período"
            hint={H.data.dataRibbonPeriod}
          >
            <DeckRibbonTilePopover
              icon={CalendarDays}
              label={periodTileLabel(model)}
              hint={H.data.dataRibbonPeriod}
              panelLabel="Período da fonte"
            >
              <DataRibbonPeriodFlyout model={model} />
            </DeckRibbonTilePopover>
          </DeckRibbonGroup>

          {/* Atualização — refreshSec da fonte (mesmo campo do inspector). */}
          <DeckRibbonGroup
            groupId="data-refresh"
            order={GROUP_ORDER.refresh}
            label="Atualização"
            hint={H.data.dataRibbonRefresh}
          >
            <DeckRibbonTilePopover
              icon={RotateCw}
              label={refreshLabel}
              hint={H.data.dataRibbonRefresh}
              panelLabel="Atualizar na TV"
            >
              <DataRibbonRefreshFlyout model={model} />
            </DeckRibbonTilePopover>
          </DeckRibbonGroup>

          {/* Expressão — resumo por parâmetro; edição completa no drawer. */}
          {hasExpressionSurface ? (
            <DeckRibbonGroup
              groupId="data-expression"
              order={GROUP_ORDER.expression}
              label="Expressão"
              hint={H.data.dataRibbonExpression}
            >
              <DeckRibbonTilePopover
                icon={Sigma}
                label={expressionTileLabel(model)}
                hint={H.data.dataRibbonExpression}
                panelLabel="Expressões dos parâmetros"
              >
                <DataRibbonExpressionFlyout model={model} />
              </DeckRibbonTilePopover>
            </DeckRibbonGroup>
          ) : null}

          {/* Mais — demais parâmetros (fora do grupo Período) + painel. */}
          <DeckRibbonGroup
            groupId="data-more"
            order={GROUP_ORDER.more}
            label="Mais"
            hint={H.data.dataRibbonMore}
          >
            <DeckRibbonTilePopover
              icon={SlidersHorizontal}
              label="Mais"
              hint={H.data.dataRibbonMore}
              panelLabel="Demais parâmetros"
              panelClassName={
                hasParams ? "td-deck-ribbon-tile-popover--wide" : undefined
              }
            >
              <DataRibbonMoreFlyout model={model} />
            </DeckRibbonTilePopover>
          </DeckRibbonGroup>
        </>
      ) : null}
    </DeckRibbonGroups>
  );
}
