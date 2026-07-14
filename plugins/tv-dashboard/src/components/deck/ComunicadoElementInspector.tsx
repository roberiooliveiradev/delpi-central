import { FolderOpen, Move, PaintBucket, Pentagon, Upload } from "lucide-react";
import { HintAction, NativeCheckboxControl, NativeTextControl } from "@delpi/plugin-ui/index";
import {
  isDataBlockType,
  isDataSourceBlockType,
  isDataViewBlockType,
  isComunicadoVisualBoxBlock,
  normalizeHrefInput,
  normalizeCanvasTableCells,
  visualBoxSupportsShapeFormatting,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";
import { useEffect, useMemo, useState } from "react";

import { listDataRoutes, type BranchScope, type TvDataRouteCatalogItem } from "../../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { comunicadoBlockTypeLabel } from "../../utils/comunicadoBlockLabels";
import { DataBindingInspector } from "../DataBindingInspector";
import { InputBindingInspector } from "../InputBindingInspector";
import { InputViewOptionsInspector } from "../InputViewOptionsInspector";
import { ChartViewOptionsInspector } from "../ChartViewOptionsInspector";
import { KpiViewOptionsInspector } from "../KpiViewOptionsInspector";
import { TableViewOptionsInspector } from "../TableViewOptionsInspector";
import { VisualDataViewInspector } from "../VisualDataViewInspector";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { SelectionSectionsHost } from "../selectionSections";
import { ComunicadoImageCropPanel } from "./ComunicadoImageCropPanel";
import { DeckField } from "./DeckField";
import { DeckInspectorLayout } from "./DeckInspectorLayout";
import { DeckPropertySection } from "./DeckPropertySection";

const E = TV_DASHBOARD_HELP_TOOLTIPS.element;

const SHAPE_PANE_ICONS = [
  { id: "fill-line", label: "Preenchimento e linha", Icon: PaintBucket },
  { id: "effects", label: "Efeitos", Icon: Pentagon },
  { id: "size", label: "Tamanho e posição", Icon: Move },
] as const;

type Labels = Record<string, string>;

export function ComunicadoElementInspector({
  labels = {},
  placement = "default",
  onOpenDataSources,
  branchScope = null,
}: {
  labels?: Labels;
  placement?: "default" | "side";
  onOpenDataSources?: () => void;
  branchScope?: BranchScope | null;
}) {
  const {
    selected,
    selectedIds,
    selectedKpiPart,
    selectedChartPart,
    selectedInputPart,
    uploading,
    updateSelected,
    triggerUpload,
    openMediaLibrary,
    updateBlockLink,
  } = useComunicadoEditor();

  const multiSelect = selectedIds.length > 1;
  const isShapeBlock =
    selected && isComunicadoVisualBoxBlock(selected) && visualBoxSupportsShapeFormatting(selected);
  const isIconBlock = selected?.type === "icon";
  const isMediaBlock = selected?.type === "image" || selected?.type === "video";
  const isSidebarLinkBlock = isMediaBlock || isShapeBlock || isIconBlock;
  const isDataBlock = selected ? isDataBlockType(selected.type) || isDataSourceBlockType(selected.type) : false;
  const isViewBlock = selected ? isDataViewBlockType(selected.type) : false;
  const [routes, setRoutes] = useState<TvDataRouteCatalogItem[]>([]);
  const [shapePaneIcon, setShapePaneIcon] = useState<(typeof SHAPE_PANE_ICONS)[number]["id"]>("fill-line");
  const [shapeOptionsTab, setShapeOptionsTab] = useState<"shape" | "text">("shape");

  useEffect(() => {
    if (!isDataBlock) return;
    void listDataRoutes().then(setRoutes).catch(() => setRoutes([]));
  }, [isDataBlock]);

  useEffect(() => {
    if (!isShapeBlock || shapeOptionsTab !== "shape") return;
    const el = document.getElementById(`td-shape-pane-${shapePaneIcon}`);
    el?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [shapePaneIcon, isShapeBlock, shapeOptionsTab]);

  const selectedRoute = useMemo(() => {
    if (!isDataBlock || !selected || !("dataBinding" in selected)) return null;
    return routes.find((route) => route.operationId === selected.dataBinding.operationId) ?? null;
  }, [isDataBlock, routes, selected]);

  if (selectedIds.length === 0 || !selected) {
    return (
      <DeckInspectorLayout variant={placement}>
        <p className="td-subtitle td-deck-inspector__empty">
          Selecione um elemento no palco ou arraste para posicionar.
        </p>
      </DeckInspectorLayout>
    );
  }

  const pane = placement === "side";

  const typeLabel = comunicadoBlockTypeLabel(selected.type);

  return (
    <DeckInspectorLayout variant={placement}>
      {!multiSelect && isShapeBlock ? (
        <>
          <div className="td-format-pane-subtabs" role="tablist" aria-label="Opções de forma ou texto">
            <button
              type="button"
              role="tab"
              aria-selected={shapeOptionsTab === "shape"}
              className={[
                "td-format-pane-subtab",
                shapeOptionsTab === "shape" ? "td-format-pane-subtab--active" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              onClick={() => setShapeOptionsTab("shape")}
            >
              Opções de Forma
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={shapeOptionsTab === "text"}
              className={[
                "td-format-pane-subtab",
                shapeOptionsTab === "text" ? "td-format-pane-subtab--active" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              onClick={() => setShapeOptionsTab("text")}
            >
              Opções de Texto
            </button>
          </div>
          {shapeOptionsTab === "shape" ? (
            <div className="td-format-pane-icons" role="tablist" aria-label="Categorias de forma">
              {SHAPE_PANE_ICONS.map(({ id, label, Icon }) => (
                <button
                  key={id}
                  type="button"
                  role="tab"
                  aria-selected={shapePaneIcon === id}
                  aria-label={label}
                  title={label}
                  className={[
                    "td-format-pane-icons__btn",
                    shapePaneIcon === id ? "td-format-pane-icons__btn--active" : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  onClick={() => setShapePaneIcon(id)}
                >
                  <Icon size={16} aria-hidden="true" />
                </button>
              ))}
            </div>
          ) : null}
        </>
      ) : null}

      <DeckPropertySection
        pane={pane}
        title={labels.comunicadoBlocks ?? "Elemento selecionado"}
        hint={E.panel}
        defaultOpen
      >
        {multiSelect ? (
          <p className="td-deck-inspector__meta td-deck-inspector__meta--multi">
            {selectedIds.length} elementos selecionados — edite texto e link direto no palco.
          </p>
        ) : (
          <p className="td-deck-inspector__meta">{typeLabel}</p>
        )}

        {!multiSelect && isShapeBlock && shapeOptionsTab === "text" ? (
          <DeckField id="td-shape-content" label="Texto na forma" hint={E.shapeText}>
            <NativeTextControl
              id="td-shape-content"
              type="text"
              value={selected.content ?? ""}
              onChange={(value) => updateSelected({ content: value } as Partial<ComunicadoBlock>)}
            />
          </DeckField>
        ) : null}
        {!multiSelect && isShapeBlock && shapeOptionsTab === "text" ? (
          <p className="td-deck-inspector__hint">
            Tipografia da forma abaixo (mesmas seções da faixa Elemento).
          </p>
        ) : null}

        {!multiSelect && isSidebarLinkBlock ? (
          <DeckField id="td-block-link" label="Link" hint={E.link}>
            <NativeTextControl
              id="td-block-link"
              type="url"
              placeholder="https://…"
              value={selected.href ?? ""}
              onChange={(value) =>
                updateBlockLink(
                  selected.id,
                  normalizeHrefInput(value) || undefined,
                )
              }
            />
          </DeckField>
        ) : null}

        {!multiSelect && isMediaBlock ? (
          <div className="td-deck-inspector__actions">
            <HintAction hint={E.uploadMedia} ariaLabel="Ajuda: biblioteca de mídia">
              <button
                type="button"
                className="td-btn td-btn--sm"
                onClick={() => openMediaLibrary("block")}
              >
                <FolderOpen size={15} aria-hidden="true" />
                Biblioteca
              </button>
            </HintAction>
            <HintAction hint={E.uploadMedia} ariaLabel="Ajuda: enviar arquivo">
              <button
                type="button"
                className="td-btn td-btn--sm"
                disabled={uploading}
                onClick={() => triggerUpload("block")}
              >
                <Upload size={15} aria-hidden="true" />
                {uploading ? "Enviando…" : labels.comunicadoUpload ?? "Enviar arquivo"}
              </button>
            </HintAction>
          </div>
        ) : null}
      </DeckPropertySection>

      {/* Irmãos L1 — evita FormatPaneSection aninhado (4M.3). */}
      {!multiSelect && selected.type === "canvas_table" ? (
        <DeckPropertySection pane={pane} title="Tabela (canvas)" defaultOpen>
          <DeckField id="td-canvas-table-rows" label="Linhas">
            <NativeTextControl
              id="td-canvas-table-rows"
              type="number"
              min={1}
              max={20}
              value={selected.rows}
              onChange={(value) => {
                const rows = Math.max(1, Math.min(20, Number(value) || 1));
                updateSelected({
                  rows,
                  cells: normalizeCanvasTableCells(selected.cells, rows, selected.cols),
                });
              }}
            />
          </DeckField>
          <DeckField id="td-canvas-table-cols" label="Colunas">
            <NativeTextControl
              id="td-canvas-table-cols"
              type="number"
              min={1}
              max={12}
              value={selected.cols}
              onChange={(value) => {
                const cols = Math.max(1, Math.min(12, Number(value) || 1));
                updateSelected({
                  cols,
                  cells: normalizeCanvasTableCells(selected.cells, selected.rows, cols),
                });
              }}
            />
          </DeckField>
          <NativeCheckboxControl
            id="td-canvas-table-header-row"
            className="td-deck-inspector__checkbox"
            checked={selected.headerRow ?? false}
            label="Primeira linha como cabeçalho"
            onChange={(checked) => updateSelected({ headerRow: checked })}
          />
        </DeckPropertySection>
      ) : null}

      {!multiSelect && selected.type === "input" ? <InputBindingInspector pane={pane} /> : null}
      {!multiSelect && selected.type === "input" ? <InputViewOptionsInspector pane={pane} /> : null}

      {!multiSelect && isDataBlock ? (
        <DataBindingInspector route={selectedRoute} pane={pane} branchScope={branchScope} />
      ) : null}
      {!multiSelect && isViewBlock ? (
        <VisualDataViewInspector
          pane={pane}
          route={selectedRoute}
          onOpenDataSources={onOpenDataSources}
        />
      ) : null}
      {!multiSelect && selected?.type === "chart_view" ? (
        <ChartViewOptionsInspector pane={pane} />
      ) : null}
      {!multiSelect && selected?.type === "table_view" ? (
        <>
          <SelectionSectionsHost
            layout="pane"
            only={[
              "tableStyleOptions",
              "tableStyles",
              "tableBorders",
              "frame",
              "organize",
              "animation",
              "actions",
            ]}
            labels={labels}
          />
          <TableViewOptionsInspector pane={pane} omitDesignChrome />
        </>
      ) : null}
      {!multiSelect && selected?.type === "kpi_view" ? (
        <KpiViewOptionsInspector pane={pane} />
      ) : null}

      {!multiSelect && selected.type === "image" ? (
        <div id="td-comunicado-crop-panel">
          <ComunicadoImageCropPanel />
        </div>
      ) : null}

      {multiSelect ? (
        <SelectionSectionsHost layout="pane" full labels={labels} />
      ) : null}

      {!multiSelect && isShapeBlock && shapeOptionsTab === "text" ? (
        <SelectionSectionsHost layout="pane" only={["typography"]} labels={labels} />
      ) : null}

      {!multiSelect &&
      isShapeBlock &&
      shapeOptionsTab === "shape" &&
      !selectedKpiPart &&
      !selectedChartPart &&
      !selectedInputPart ? (
        <div id="td-shape-pane-size">
          <SelectionSectionsHost
            layout="pane"
            only={[
              "shapeGallery",
              "shapeChrome",
              "frame",
              "organize",
              "animation",
              "actions",
            ]}
            labels={labels}
          />
        </div>
      ) : null}

      {!multiSelect &&
      !isShapeBlock &&
      selected.type !== "table_view" &&
      !selectedKpiPart &&
      !selectedChartPart &&
      !selectedInputPart ? (
        <SelectionSectionsHost layout="pane" full labels={labels} />
      ) : null}

      {!multiSelect &&
      (selectedKpiPart || selectedChartPart || selectedInputPart) ? (
        <SelectionSectionsHost layout="pane" full labels={labels} />
      ) : null}
    </DeckInspectorLayout>
  );
}
