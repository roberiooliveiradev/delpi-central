import { useRef, useState, type ReactNode } from "react";
import {
  BarChart3,
  Database,
  Goal,
  Grid3x3,
  LayoutTemplate,
  Palette,
  Replace,
} from "lucide-react";
import {
  AnchoredPanelPortal,
  ChartTypeCatalogPanel,
  ElementTogglePopover,
  FormSelectControl,
  type DelpiChartType,
  useRibbonSectionPopoverSurface,
} from "@delpi/plugin-ui/index";
import {
  applyChartAddElementChoiceWithParts,
  applyChartElementVisibility,
  chartElementPrimaryPartRef,
  isChartElementEnabled,
  isChartElementOpenForPart,
  mergeChartPartsWithOptions,
  mergeComunicadoChartOptions,
  partsToChartOptions,
  toSeriesChartKind,
  CHART_LEGEND_SORT_OPTIONS,
  type ChartAddElementChoiceId,
  type ChartElementId,
  type ComunicadoBlock,
  type ComunicadoChartOptions,
  type ComunicadoChartType,
  type ComunicadoChartViewBlock,
} from "@delpi/tv-dashboard-presentation";

import { CHART_ADD_ELEMENT_ITEMS } from "../../content/chartAddElementItems";
import {
  CHART_QUICK_LAYOUTS,
  applyChartQuickLayout,
} from "../../content/chartQuickLayouts";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { TV_DASHBOARD_ROOT_CLASS } from "../../constants/pluginRootClass";
import { ChartAddElementMenu } from "../ChartAddElementMenu";
import { ChartColorsStylesMenu } from "../ChartColorsStylesMenu";
import { InsertCatalogPortal } from "../InsertCatalogPortal";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { DeckField } from "../deck/DeckField";
import { DeckRibbonGroup } from "../deck/DeckRibbonGroup";
import { DeckRibbonLargeButton } from "../deck/DeckRibbonLargeButton";
import { DeckRibbonTile } from "../deck/DeckRibbonTile";
import { SelectionPaneSection } from "./SelectionPaneSection";
import type { SelectionSectionLayout } from "./types";

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

function wrapPane(
  title: string,
  hint: string | undefined,
  layout: SelectionSectionLayout,
  body: ReactNode,
  wide?: boolean,
  groupId?: string,
) {
  if (layout === "pane") {
    return (
      <SelectionPaneSection title={title} hint={hint} defaultOpen={false}>
        {body}
      </SelectionPaneSection>
    );
  }
  return (
    <DeckRibbonGroup groupId={groupId} label={title} hint={hint} wide={wide}>
      {body}
    </DeckRibbonGroup>
  );
}

function useChartDesignControls() {
  const {
    selected,
    selectedChartPart,
    updateSelected,
    selectChartPart,
    openDataPanel,
    setSelectionPanelTab,
  } = useComunicadoEditor();

  const addElementAnchorRef = useRef<HTMLDivElement>(null);
  const addElementPanelRef = useRef<HTMLDivElement>(null);
  const layoutAnchorRef = useRef<HTMLDivElement>(null);
  const layoutPanelRef = useRef<HTMLDivElement>(null);
  const colorsAnchorRef = useRef<HTMLDivElement>(null);
  const colorsPanelRef = useRef<HTMLDivElement>(null);
  const changeTypeAnchorRef = useRef<HTMLDivElement>(null);
  const changeTypePanelRef = useRef<HTMLDivElement>(null);
  const [addElementOpen, setAddElementOpen] = useState(false);
  const [layoutOpen, setLayoutOpen] = useState(false);
  const [colorsOpen, setColorsOpen] = useState(false);
  const [changeTypeOpen, setChangeTypeOpen] = useState(false);

  if (!selected || selected.type !== "chart_view") return null;

  const block = selected as ComunicadoChartViewBlock;
  const chartKind = toSeriesChartKind(block.chartType) ?? "line";
  const options = mergeComunicadoChartOptions({
    ...block.chartOptions,
    ...partsToChartOptions(block.chartParts),
  });

  const toggleElement = (elementId: ChartElementId, enabled: boolean) => {
    const result = applyChartElementVisibility(elementId, enabled, options, block.chartParts);
    updateSelected({
      chartOptions: result.options,
      chartParts: result.parts,
    } as Partial<ComunicadoBlock>);
    if (enabled) {
      const part = chartElementPrimaryPartRef(elementId);
      if (part) selectChartPart(block.id, part);
    }
  };

  const applyAddElementChoice = (choiceId: ChartAddElementChoiceId) => {
    const result = applyChartAddElementChoiceWithParts(choiceId, options, block.chartParts);
    updateSelected({
      chartOptions: result.options,
      chartParts: result.parts,
    } as Partial<ComunicadoBlock>);
  };

  const openAddElementMoreOptions = (elementId: ChartElementId) => {
    const part = chartElementPrimaryPartRef(elementId);
    if (part) selectChartPart(block.id, part);
    setSelectionPanelTab("element");
    // Com parte selecionada a lista de elementos some; o campo da meta fica no ChartPartInspector.
    const scrollId =
      elementId === "goalLine" ? "td-chart-part-goal-value" : "td-chart-pane-elements";
    queueMicrotask(() => {
      document.getElementById(scrollId)?.scrollIntoView({ block: "nearest" });
    });
    setAddElementOpen(false);
  };

  const applyLayout = (layoutId: string) => {
    const layout = CHART_QUICK_LAYOUTS.find((item) => item.id === layoutId);
    if (!layout) return;
    const result = applyChartQuickLayout(layout, options, block.chartParts);
    updateSelected({
      chartOptions: result.options,
      chartParts: result.parts,
    } as Partial<ComunicadoBlock>);
    setLayoutOpen(false);
  };

  const setChartType = (chartType: DelpiChartType) => {
    updateSelected({ chartType: chartType as ComunicadoChartType } as Partial<ComunicadoBlock>);
    setChangeTypeOpen(false);
  };

  const persistOptions = (nextOptions: ComunicadoChartOptions) => {
    updateSelected({
      chartOptions: nextOptions,
      chartParts: mergeChartPartsWithOptions(block.chartParts, nextOptions),
    } as Partial<ComunicadoBlock>);
  };

  return {
    block,
    chartKind,
    options,
    selectedChartPart,
    addElementAnchorRef,
    addElementPanelRef,
    layoutAnchorRef,
    layoutPanelRef,
    colorsAnchorRef,
    colorsPanelRef,
    changeTypeAnchorRef,
    changeTypePanelRef,
    addElementOpen,
    setAddElementOpen,
    layoutOpen,
    setLayoutOpen,
    colorsOpen,
    setColorsOpen,
    changeTypeOpen,
    setChangeTypeOpen,
    toggleElement,
    applyAddElementChoice,
    openAddElementMoreOptions,
    applyLayout,
    setChartType,
    persistOptions,
    openDataPanel,
    selectChartPart,
  };
}

export function ChartLayoutSection({ layout }: { layout: SelectionSectionLayout }) {
  const ctrl = useChartDesignControls();
  if (!ctrl) return null;

  return wrapPane(
    "Layout do gráfico",
    H.chartLabels,
    layout,
    <ChartLayoutBandOrInline ctrl={ctrl} />,
    true,
    "chart-layout",
  );
}

function ChartLayoutBandOrInline({
  ctrl,
}: {
  ctrl: NonNullable<ReturnType<typeof useChartDesignControls>>;
}) {
  const inSectionPopover = useRibbonSectionPopoverSurface();

  const addElementMenu = (
    <ChartAddElementMenu
      options={ctrl.options}
      chartKind={ctrl.chartKind}
      onApplyChoice={ctrl.applyAddElementChoice}
      onMoreOptions={ctrl.openAddElementMoreOptions}
    />
  );

  const quickLayout = (
    <div className="td-chart-quick-layout">
      {CHART_QUICK_LAYOUTS.map((item) => (
        <button
          key={item.id}
          type="button"
          className="td-chart-quick-layout__item"
          title={item.hint}
          onClick={() => ctrl.applyLayout(item.id)}
        >
          <span
            className={`td-chart-quick-layout__wire td-chart-quick-layout__wire--${item.id}`}
            aria-hidden="true"
          />
          <span className="td-chart-quick-layout__label">{item.label}</span>
        </button>
      ))}
    </div>
  );

  return (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
      <div ref={ctrl.addElementAnchorRef} className="td-composer__dropdown">
        <DeckRibbonLargeButton
          icon={LayoutTemplate}
          label={"Adicionar\nelemento"}
          hint="Inclui ou remove elementos do gráfico (título, legenda, eixos…)."
          onClick={() => {
            ctrl.setAddElementOpen((open) => !open);
            ctrl.setLayoutOpen(false);
            ctrl.setColorsOpen(false);
            ctrl.setChangeTypeOpen(false);
          }}
        />
        {ctrl.addElementOpen ? (
          <AnchoredPanelPortal
            open={ctrl.addElementOpen}
            anchorRef={ctrl.addElementAnchorRef}
            panelRef={ctrl.addElementPanelRef}
            variant="bare"
            portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
            className="td-chart-add-element-portal"
            role="menu"
            aria-label="Adicionar elemento de gráfico"
            exclusive={!inSectionPopover}
            onDismiss={() => ctrl.setAddElementOpen(false)}
          >
            <div>{addElementMenu}</div>
          </AnchoredPanelPortal>
        ) : null}
      </div>

      <div ref={ctrl.layoutAnchorRef} className="td-composer__dropdown">
        <DeckRibbonLargeButton
          icon={Grid3x3}
          label={"Layout\nrápido"}
          hint="Aplica um conjunto de visibilidade de título, legenda, eixos e tabela."
          onClick={() => {
            ctrl.setLayoutOpen((open) => !open);
            ctrl.setAddElementOpen(false);
            ctrl.setColorsOpen(false);
            ctrl.setChangeTypeOpen(false);
          }}
        />
        {ctrl.layoutOpen ? (
          <AnchoredPanelPortal
            open={ctrl.layoutOpen}
            anchorRef={ctrl.layoutAnchorRef}
            panelRef={ctrl.layoutPanelRef}
            variant="bare"
            portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
            className="td-chart-quick-layout-portal"
            role="menu"
            aria-label="Layout rápido"
            exclusive={!inSectionPopover}
            onDismiss={() => ctrl.setLayoutOpen(false)}
          >
            {quickLayout}
          </AnchoredPanelPortal>
        ) : null}
      </div>
    </div>
  );
}

export function ChartStylesSection({ layout }: { layout: SelectionSectionLayout }) {
  const ctrl = useChartDesignControls();
  if (!ctrl) return null;

  const data = (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
      <DeckRibbonTile
        icon={Database}
        label="Selecionar dados"
        hint={H.openDataPanel}
        onClick={() => ctrl.openDataPanel()}
      />
    </div>
  );

  if (layout === "pane") {
    return (
      <>
        <SelectionPaneSection
          title="Estilos"
          hint="Cores da série e presets de tema/grade."
          defaultOpen={false}
        >
          <ChartStylesBandOrInline ctrl={ctrl} />
        </SelectionPaneSection>
        <SelectionPaneSection title="Dados" hint={H.chartData} defaultOpen={false}>
          {data}
        </SelectionPaneSection>
      </>
    );
  }

  return (
    <>
      <DeckRibbonGroup
        groupId="chart-styles"
        label="Estilos"
        hint="Cores da série e presets de tema/grade."
      >
        <ChartStylesBandOrInline ctrl={ctrl} />
      </DeckRibbonGroup>
      <DeckRibbonGroup groupId="chart-data" label="Dados" hint={H.chartData}>
        {data}
      </DeckRibbonGroup>
    </>
  );
}

function ChartStylesBandOrInline({
  ctrl,
}: {
  ctrl: NonNullable<ReturnType<typeof useChartDesignControls>>;
}) {
  const inSectionPopover = useRibbonSectionPopoverSurface();

  const colorsMenu = (
    <div className="td-chart-float__popover td-chart-float__popover--style">
      <ChartColorsStylesMenu
        options={ctrl.options}
        onApplyOptions={(next) => {
          ctrl.persistOptions(next);
          ctrl.setColorsOpen(false);
        }}
      />
    </div>
  );

  return (
    <div ref={ctrl.colorsAnchorRef} className="td-composer__dropdown">
      <DeckRibbonLargeButton
        icon={Palette}
        label={"Alterar\ncores"}
        hint="Paletas Delpi para a cor da série e estilos rápidos (tema, grade, marcadores)."
        onClick={() => {
          ctrl.setColorsOpen((open) => !open);
          ctrl.setAddElementOpen(false);
          ctrl.setLayoutOpen(false);
          ctrl.setChangeTypeOpen(false);
        }}
      />
      {ctrl.colorsOpen ? (
        <AnchoredPanelPortal
          open={ctrl.colorsOpen}
          anchorRef={ctrl.colorsAnchorRef}
          panelRef={ctrl.colorsPanelRef}
          variant="bare"
          portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
          className="td-chart-colors-portal"
          role="menu"
          aria-label="Alterar cores e estilos"
          exclusive={!inSectionPopover}
          onDismiss={() => ctrl.setColorsOpen(false)}
        >
          {colorsMenu}
        </AnchoredPanelPortal>
      ) : null}
    </div>
  );
}

export function ChartTypeSection({ layout }: { layout: SelectionSectionLayout }) {
  const ctrl = useChartDesignControls();
  if (!ctrl) return null;

  const body = (
    <div ref={ctrl.changeTypeAnchorRef} className="td-composer__dropdown">
      <DeckRibbonLargeButton
        icon={Replace}
        label={"Alterar tipo\nde gráfico"}
        hint="Mesmo catálogo de tipos de Inserir → Gráficos."
        onClick={() => {
          ctrl.setChangeTypeOpen((open) => !open);
          ctrl.setAddElementOpen(false);
          ctrl.setLayoutOpen(false);
          ctrl.setColorsOpen(false);
        }}
      />
      {ctrl.changeTypeOpen ? (
        <InsertCatalogPortal
          open={ctrl.changeTypeOpen}
          anchorRef={ctrl.changeTypeAnchorRef}
          panelRef={ctrl.changeTypePanelRef}
          className="td-chart-catalog-portal"
          ariaLabel="Alterar tipo de gráfico"
          onDismiss={() => ctrl.setChangeTypeOpen(false)}
        >
          <ChartTypeCatalogPanel
            title="Alterar tipo de gráfico"
            selectedType={ctrl.block.chartType as DelpiChartType}
            onSelect={ctrl.setChartType}
          />
        </InsertCatalogPortal>
      ) : null}
    </div>
  );

  return wrapPane("Tipo", H.chartType, layout, body, false, "chart-type");
}

export function ChartLabelsSection({ layout }: { layout: SelectionSectionLayout }) {
  const ctrl = useChartDesignControls();
  if (!ctrl) return null;

  const body = (
    <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
      {CHART_ADD_ELEMENT_ITEMS.filter((item) =>
        ["chartTitle", "axisTitles", "legend", "dataLabels", "dataTable"].includes(item.id),
      ).map((item) => {
        const enabled = isChartElementEnabled(item.id, ctrl.options);
        const focused = isChartElementOpenForPart(item.id, ctrl.selectedChartPart);
        return (
          <ElementTogglePopover
            key={item.id}
            icon={item.icon}
            label={item.label.split(" ")[0] ?? item.label}
            hint={
              item.id === "dataLabels"
                ? "Liga os rótulos e edita tipografia de todos de uma vez."
                : item.label
            }
            active={enabled}
            focused={focused}
            presence={{
              enabled,
              onAdd: () => ctrl.toggleElement(item.id, true),
              onRemove: () => ctrl.toggleElement(item.id, false),
              onOpenOptions: () => ctrl.openAddElementMoreOptions(item.id),
            }}
          />
        );
      })}
    </div>
  );

  return wrapPane("Rótulos", H.chartLabels, layout, body, false, "chart-labels");
}

export function ChartAxesSection({ layout }: { layout: SelectionSectionLayout }) {
  const ctrl = useChartDesignControls();
  if (!ctrl) return null;

  const isGauge = ctrl.block.chartType === "gauge";
  const axisTiles = (
    isGauge
      ? ([
          {
            id: "goalLine" as const,
            icon: Goal,
            label: "Meta",
            hint: "Liga a meta do velocímetro e abre coluna/valor no inspetor.",
          },
        ] as const)
      : ([
          {
            id: "axes" as const,
            icon: BarChart3,
            label: "Eixos",
            hint: "Liga os eixos e abre opções de estilo.",
          },
          {
            id: "gridlines" as const,
            icon: Grid3x3,
            label: "Grade",
            hint: "Liga a grade horizontal e edita o traço das linhas.",
          },
          {
            id: "goalLine" as const,
            icon: Goal,
            label: "Meta",
            hint: "Liga a linha de meta e abre coluna ou valor numérico no inspetor.",
          },
        ] as const)
  );

  const body = (
    <div className="td-deck-ribbon__stack td-deck-ribbon__stack--ribbon-row">
      <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
        {axisTiles.map((item) => {
          const enabled = isChartElementEnabled(item.id, ctrl.options);
          const focused = isChartElementOpenForPart(item.id, ctrl.selectedChartPart);
          return (
            <ElementTogglePopover
              key={item.id}
              icon={item.icon}
              label={item.label}
              hint={item.hint}
              active={enabled}
              focused={focused}
              presence={{
                enabled,
                onAdd: () => ctrl.toggleElement(item.id, true),
                onRemove: () => ctrl.toggleElement(item.id, false),
                onOpenOptions: () => ctrl.openAddElementMoreOptions(item.id),
              }}
            />
          );
        })}
      </div>
      {!isGauge ? (
        <DeckField
          id="td-chart-ribbon-category-sort"
          label="Ordenar categorias"
          hint="A→Z nos centros de trabalho; Valor para ranking."
        >
          <FormSelectControl
            id="td-chart-ribbon-category-sort"
            ariaLabel="Ordenar categorias do eixo"
            value={ctrl.options.legendSort ?? "auto"}
            onChange={(value) =>
              ctrl.persistOptions({
                ...ctrl.options,
                legendSort: value as ComunicadoChartOptions["legendSort"],
              })
            }
            options={CHART_LEGEND_SORT_OPTIONS.map((entry) => ({
              value: entry.value,
              label: entry.label,
            }))}
          />
        </DeckField>
      ) : null}
    </div>
  );

  return wrapPane(
    isGauge ? "Meta" : "Eixos",
    isGauge ? H.chartGaugeMeta : H.chartAxes,
    layout,
    body,
    true,
    "chart-axes",
  );
}
