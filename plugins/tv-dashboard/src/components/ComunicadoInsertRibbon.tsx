import { useRef, useState } from "react";
import {
  BarChart3,
  Braces,
  Database,
  Filter,
  Gauge,
  Grid3X3,
  Heading,
  Image as ImageIcon,
  Shapes,
  Sparkles,
  Table2,
  Text,
  Type,
  Video,
} from "lucide-react";
import {
  AnchoredPanelPortal,
  ChartTypeCatalogPanel,
  LucideIconPickerPopover,
  TableInsertCatalogPanel,
  useRibbonSectionPopoverSurface,
  type DelpiChartType,
  type DelpiTableInsertSelection,
} from "@delpi/plugin-ui/index";
import {
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
import { DeckRibbonGroups } from "./deck/DeckRibbonGroups";
import { DeckRibbonTile } from "./deck/DeckRibbonTile";
import { useComunicadoEditor } from "./comunicadoEditorContext";

type Labels = Record<string, string>;

/** Catálogo Inserir: portal na faixa; inline no popover da seção colapsada. */
function InsertCatalogPortal({
  open,
  anchorRef,
  panelRef,
  className,
  ariaLabel,
  onDismiss,
  children,
}: {
  open: boolean;
  anchorRef: React.RefObject<HTMLDivElement | null>;
  panelRef: React.RefObject<HTMLDivElement | null>;
  className: string;
  ariaLabel: string;
  onDismiss: () => void;
  children: React.ReactNode;
}) {
  const flattenNested = useRibbonSectionPopoverSurface();
  if (!open) return null;
  if (flattenNested) {
    return (
      <div className={`${className} ${className}--inline`} role="menu" aria-label={ariaLabel}>
        {children}
      </div>
    );
  }
  return (
    <AnchoredPanelPortal
      open={open}
      anchorRef={anchorRef}
      panelRef={panelRef}
      variant="bare"
      portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
      className={className}
      role="menu"
      aria-label={ariaLabel}
      onDismiss={onDismiss}
    >
      {children}
    </AnchoredPanelPortal>
  );
}

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
    insertTextDataFieldBlock,
  } = useComunicadoEditor();
  const shapeAnchorRef = useRef<HTMLDivElement>(null);
  const iconAnchorRef = useRef<HTMLDivElement>(null);
  const chartAnchorRef = useRef<HTMLDivElement>(null);
  const tableAnchorRef = useRef<HTMLDivElement>(null);
  const chartPanelRef = useRef<HTMLDivElement>(null);
  const tablePanelRef = useRef<HTMLDivElement>(null);
  const [iconMenuOpen, setIconMenuOpen] = useState(false);
  const [chartMenuOpen, setChartMenuOpen] = useState(false);
  const [tableMenuOpen, setTableMenuOpen] = useState(false);

  const closeInsertMenus = () => {
    setShapeMenuOpen(false);
    setIconMenuOpen(false);
    setChartMenuOpen(false);
    setTableMenuOpen(false);
  };

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
    <DeckRibbonGroups>
      <DeckRibbonGroup
        groupId="insert-text"
        label="Texto"
        hint={H.insertTextGroup ?? H.insert}
        order={0}
        collapseIcon={Type}
      >
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

      <DeckRibbonGroup
        groupId="insert-media"
        label="Mídia"
        hint={H.insertMediaGroup ?? H.insert}
        order={1}
        collapseIcon={ImageIcon}
      >
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

      <DeckRibbonGroup
        groupId="insert-illustrations"
        label="Ilustrações"
        hint={H.insertIllustrationsGroup ?? H.insertShape}
        order={2}
        collapseIcon={Shapes}
      >
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
                onDismiss={closeInsertMenus}
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
            <LucideIconPickerPopover
              open={iconMenuOpen}
              onOpenChange={(open) => {
                if (!open) closeInsertMenus();
                else setIconMenuOpen(true);
              }}
              anchorRef={iconAnchorRef}
              nameFormat="pascal"
              curatedOnly={false}
              title="Ícones"
              showClear={false}
              portalScopeClassName={TV_DASHBOARD_ROOT_CLASS}
              ariaLabel="Biblioteca de ícones"
              onChange={(name) => {
                if (!name?.trim()) return;
                addIconBlock(name.trim());
                closeInsertMenus();
              }}
            />
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

      <DeckRibbonGroup
        groupId="insert-data"
        label="Dados"
        hint={H.insertDataGroup ?? H.insertIndicator}
        order={3}
        collapseIcon={Database}
      >
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile
            icon={Database}
            label={labels.comunicadoAddDataSource ?? "Dados"}
            hint={H.insertDataSource ?? H.insertIndicator}
            keyTip={K.dataSource}
            onClick={(event) => openDataCatalog("insert", { anchor: event.currentTarget })}
          />
          <DeckRibbonTile
            icon={Filter}
            label="Filtro"
            hint="Campo no palco que filtra fontes (params da rota). Editável também na TV."
            onClick={() => addInputBlock()}
          />
          <DeckRibbonTile
            icon={Braces}
            label="Campo em texto"
            hint={H.insertTextDataField ?? H.insertDataSource}
            onClick={() => insertTextDataFieldBlock()}
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
              <InsertCatalogPortal
                open={chartMenuOpen}
                anchorRef={chartAnchorRef}
                panelRef={chartPanelRef}
                className="td-chart-catalog-portal"
                ariaLabel="Catálogo de gráficos"
                onDismiss={closeInsertMenus}
              >
                <ChartTypeCatalogPanel onSelect={insertChart} />
              </InsertCatalogPortal>
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
              <InsertCatalogPortal
                open={tableMenuOpen}
                anchorRef={tableAnchorRef}
                panelRef={tablePanelRef}
                className="td-table-catalog-portal"
                ariaLabel="Catálogo de tabelas"
                onDismiss={closeInsertMenus}
              >
                <TableInsertCatalogPanel onSelect={insertTable} />
              </InsertCatalogPortal>
            ) : null}
          </div>
        </div>
      </DeckRibbonGroup>
    </DeckRibbonGroups>
  );
}
