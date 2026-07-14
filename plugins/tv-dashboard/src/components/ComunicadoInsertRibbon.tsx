import { useEffect, useRef, useState } from "react";
import { BarChart3, Database, Filter, Gauge, Grid3X3, Heading, Image as ImageIcon, Shapes, Sparkles, Table2, Text, Video } from "lucide-react";
import {
  AnchoredPanelPortal,
  ChartTypeCatalogPanel,
  LucideIconGridPanel,
  TableInsertCatalogPanel,
  type DelpiChartType,
  type DelpiTableInsertSelection,
} from "@delpi/plugin-ui/index";
import {
  COMUNICADO_ICON_OPTIONS,
  createChartViewBlock,
  createTableViewBlock,
  type ComunicadoChartType,
  type ComunicadoShapeKind,
  type ComunicadoTablePreset,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { rememberComunicadoShape } from "../utils/comunicadoRecentShapes";
import { DECK_INSERT_ACTION_KEYTIPS } from "../utils/deckKeyTips";
import { ComunicadoShapeLibraryMenu } from "./ComunicadoShapeLibraryMenu";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";
import { DeckRibbonTile } from "./deck/DeckRibbonTile";
import { useComunicadoEditor } from "./comunicadoEditorContext";

type Labels = Record<string, string>;

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;
const K = DECK_INSERT_ACTION_KEYTIPS;

export function ComunicadoInsertRibbon({ labels = {} }: { labels?: Labels }) {
  const {
    shapeMenuOpen,
    setShapeMenuOpen,
    addBlock,
    addShape,
    addIconBlock,
    addChartViewBlock,
    addCanvasTableBlock,
    addInputBlock,
    addTableViewBlock,
    addKpiViewBlock,
    openDataCatalog,
    openMediaLibrary,
  } = useComunicadoEditor();
  const shapeAnchorRef = useRef<HTMLDivElement>(null);
  const iconAnchorRef = useRef<HTMLDivElement>(null);
  const chartAnchorRef = useRef<HTMLDivElement>(null);
  const tableAnchorRef = useRef<HTMLDivElement>(null);
  const iconPanelRef = useRef<HTMLDivElement>(null);
  const chartPanelRef = useRef<HTMLDivElement>(null);
  const tablePanelRef = useRef<HTMLDivElement>(null);
  const [iconMenuOpen, setIconMenuOpen] = useState(false);
  const [chartMenuOpen, setChartMenuOpen] = useState(false);
  const [tableMenuOpen, setTableMenuOpen] = useState(false);

  useEffect(() => {
    if (!shapeMenuOpen && !iconMenuOpen && !chartMenuOpen && !tableMenuOpen) return undefined;

    function handlePointerDown(event: MouseEvent) {
      const target = event.target as Node;
      if (
        shapeAnchorRef.current?.contains(target) ||
        iconAnchorRef.current?.contains(target) ||
        chartAnchorRef.current?.contains(target) ||
        tableAnchorRef.current?.contains(target)
      ) {
        return;
      }
      if (
        (target as HTMLElement).closest?.(
          ".td-shape-library--portal, .td-icon-library-portal, .td-chart-catalog-portal, .td-table-catalog-portal, .delpi-ui-lucide-icon-grid, .delpi-ui-chart-catalog, .delpi-ui-table-insert-catalog",
        )
      ) {
        return;
      }
      setShapeMenuOpen(false);
      setIconMenuOpen(false);
      setChartMenuOpen(false);
      setTableMenuOpen(false);
    }

    document.addEventListener("mousedown", handlePointerDown);
    return () => document.removeEventListener("mousedown", handlePointerDown);
  }, [chartMenuOpen, iconMenuOpen, setShapeMenuOpen, shapeMenuOpen, tableMenuOpen]);

  function insertShape(kind: ComunicadoShapeKind) {
    addShape(kind);
    rememberComunicadoShape(kind);
    setShapeMenuOpen(false);
  }

  function insertChart(chartType: DelpiChartType) {
    addChartViewBlock(chartType as ComunicadoChartType);
    setChartMenuOpen(false);
  }

  function insertTable(selection: DelpiTableInsertSelection) {
    addTableViewBlock(selection.rows, selection.cols, selection.preset as ComunicadoTablePreset);
    setTableMenuOpen(false);
  }

  return (
    <div className="td-deck-ribbon__groups">
      <DeckRibbonGroup label="Texto" hint={H.insertTextGroup ?? H.insert}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile
            icon={Heading}
            label={labels.comunicadoAddHeading ?? "Título"}
            hint={H.insertHeading}
            keyTip={K.heading}
            onClick={() => addBlock("heading")}
          />
          <DeckRibbonTile
            icon={Text}
            label={labels.comunicadoAddText ?? "Texto"}
            hint={H.insertText}
            keyTip={K.text}
            onClick={() => addBlock("text")}
          />
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Mídia" hint={H.insertMediaGroup ?? H.insert}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile
            icon={ImageIcon}
            label={labels.comunicadoAddImage ?? "Imagem"}
            hint={H.insertImage}
            keyTip={K.image}
            onClick={() => openMediaLibrary("insert-image")}
          />
          <DeckRibbonTile
            icon={Video}
            label={labels.comunicadoAddVideo ?? "Vídeo"}
            hint={H.insertVideo}
            keyTip={K.video}
            onClick={() => openMediaLibrary("insert-video")}
          />
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Ilustrações" hint={H.insertIllustrationsGroup ?? H.insertShape}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <div ref={shapeAnchorRef} className="td-composer__dropdown">
            <DeckRibbonTile
              icon={Shapes}
              label={labels.comunicadoAddShape ?? "Formas"}
              hint={H.insertShape}
              active={shapeMenuOpen}
              keyTip={K.shape}
              onClick={() => {
                setIconMenuOpen(false);
                setChartMenuOpen(false);
                setTableMenuOpen(false);
                setShapeMenuOpen(!shapeMenuOpen);
              }}
            />
            {shapeMenuOpen ? (
              <ComunicadoShapeLibraryMenu
                open={shapeMenuOpen}
                anchorRef={shapeAnchorRef}
                onSelect={insertShape}
              />
            ) : null}
          </div>
          <div ref={iconAnchorRef} className="td-composer__dropdown">
            <DeckRibbonTile
              icon={Sparkles}
              label={labels.comunicadoAddIcon ?? "Ícones"}
              hint={H.insertIcon}
              active={iconMenuOpen}
              keyTip={K.icon}
              onClick={() => {
                setShapeMenuOpen(false);
                setChartMenuOpen(false);
                setTableMenuOpen(false);
                setIconMenuOpen((open) => !open);
              }}
            />
            {iconMenuOpen ? (
              <AnchoredPanelPortal
                open={iconMenuOpen}
                anchorRef={iconAnchorRef}
                panelRef={iconPanelRef}
                variant="bare"
                portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
                className="td-icon-library-portal"
                role="menu"
                aria-label="Biblioteca de ícones"
              >
                <LucideIconGridPanel
                  title="Ícones"
                  items={COMUNICADO_ICON_OPTIONS.map((item) => ({
                    name: item.name,
                    label: item.label,
                    hint: `${H.insertIcon} — ${item.label}`,
                  }))}
                  onSelect={(name) => {
                    addIconBlock(name);
                    setIconMenuOpen(false);
                  }}
                />
              </AnchoredPanelPortal>
            ) : null}
          </div>
          <DeckRibbonTile
            icon={Grid3X3}
            label="Grade"
            hint="Inserir Tabela (canvas), estática e editável."
            keyTip={K.canvasTable}
            onClick={() => addCanvasTableBlock()}
          />
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Dados" hint={H.insertDataGroup ?? H.insertIndicator}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile
            icon={Database}
            label={labels.comunicadoAddDataSource ?? "Dados"}
            hint={H.insertDataSource ?? H.insertIndicator}
            keyTip={K.dataSource}
            onClick={() => openDataCatalog()}
          />
          <DeckRibbonTile
            icon={Filter}
            label="Filtro"
            hint="Campo no palco que filtra fontes (params da rota). Editável também na TV."
            onClick={() => addInputBlock()}
          />
          <DeckRibbonTile
            icon={Gauge}
            label={labels.comunicadoAddKpi ?? "KPI"}
            hint={H.insertKpi ?? H.insertIndicator}
            keyTip={K.kpi}
            onClick={() => addKpiViewBlock()}
          />
          <div ref={chartAnchorRef} className="td-composer__dropdown">
            <DeckRibbonTile
              icon={BarChart3}
              label={labels.comunicadoAddChart ?? "Gráficos"}
              hint={H.insertChart ?? H.insertIndicator}
              active={chartMenuOpen}
              keyTip={K.chart}
              onClick={() => {
                setShapeMenuOpen(false);
                setIconMenuOpen(false);
                setTableMenuOpen(false);
                setChartMenuOpen((open) => !open);
              }}
            />
            {chartMenuOpen ? (
              <AnchoredPanelPortal
                open={chartMenuOpen}
                anchorRef={chartAnchorRef}
                panelRef={chartPanelRef}
                variant="bare"
                portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
                className="td-chart-catalog-portal"
                role="menu"
                aria-label="Catálogo de gráficos"
              >
                <ChartTypeCatalogPanel onSelect={insertChart} />
              </AnchoredPanelPortal>
            ) : null}
          </div>
          <div ref={tableAnchorRef} className="td-composer__dropdown">
            <DeckRibbonTile
              icon={Table2}
              label={labels.comunicadoAddTable ?? "Tabelas"}
              hint={H.insertTable ?? H.insertIndicator}
              active={tableMenuOpen}
              keyTip={K.table}
              onClick={() => {
                setShapeMenuOpen(false);
                setIconMenuOpen(false);
                setChartMenuOpen(false);
                setTableMenuOpen((open) => !open);
              }}
            />
            {tableMenuOpen ? (
              <AnchoredPanelPortal
                open={tableMenuOpen}
                anchorRef={tableAnchorRef}
                panelRef={tablePanelRef}
                variant="bare"
                portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
                className="td-table-catalog-portal"
                role="menu"
                aria-label="Catálogo de tabelas"
              >
                <TableInsertCatalogPanel onSelect={insertTable} />
              </AnchoredPanelPortal>
            ) : null}
          </div>
        </div>
      </DeckRibbonGroup>
    </div>
  );
}
