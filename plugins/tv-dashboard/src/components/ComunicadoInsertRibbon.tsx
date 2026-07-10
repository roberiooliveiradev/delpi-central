import { useEffect, useRef, useState } from "react";
import { BarChart3, Database, Heading, Image as ImageIcon, Shapes, Sparkles, Table2, Text, Video } from "lucide-react";
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

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../content/helpTooltips";
import { rememberComunicadoShape } from "../utils/comunicadoRecentShapes";
import { ComunicadoShapeLibraryMenu } from "./ComunicadoShapeLibraryMenu";
import { DeckRibbonGroup } from "./deck/DeckRibbonGroup";
import { DeckRibbonTile } from "./deck/DeckRibbonTile";
import { useComunicadoEditor } from "./comunicadoEditorContext";

type Labels = Record<string, string>;

const H = TV_DASHBOARD_HELP_TOOLTIPS.ribbon;

export function ComunicadoInsertRibbon({ labels = {} }: { labels?: Labels }) {
  const {
    shapeMenuOpen,
    setShapeMenuOpen,
    addBlock,
    addShape,
    addIconBlock,
    addChartViewBlock,
    addTableViewBlock,
    openDataPanel,
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
          ".td-shape-library--portal, .delpi-ui-lucide-icon-grid, .delpi-ui-chart-catalog, .delpi-ui-table-insert-catalog",
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
            onClick={() => addBlock("heading")}
          />
          <DeckRibbonTile
            icon={Text}
            label={labels.comunicadoAddText ?? "Texto"}
            hint={H.insertText}
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
            onClick={() => openMediaLibrary("insert-image")}
          />
          <DeckRibbonTile
            icon={Video}
            label={labels.comunicadoAddVideo ?? "Vídeo"}
            hint={H.insertVideo}
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
        </div>
      </DeckRibbonGroup>

      <DeckRibbonGroup label="Dados" hint={H.insertDataGroup ?? H.insertIndicator}>
        <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact">
          <DeckRibbonTile
            icon={Database}
            label={labels.comunicadoAddDataSource ?? "Dados"}
            hint={H.insertDataSource ?? H.insertIndicator}
            onClick={() => openDataPanel()}
          />
          <div ref={chartAnchorRef} className="td-composer__dropdown">
            <DeckRibbonTile
              icon={BarChart3}
              label={labels.comunicadoAddChart ?? "Gráficos"}
              hint={H.insertChart ?? H.insertIndicator}
              active={chartMenuOpen}
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
