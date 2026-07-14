import { Move, PaintBucket, Pentagon } from "lucide-react";
import { NativeTextControl } from "@delpi/plugin-ui/index";
import {
  isDataBlockType,
  isDataSourceBlockType,
  isDataViewBlockType,
  isComunicadoVisualBoxBlock,
  normalizeHrefInput,
  visualBoxSupportsShapeFormatting,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";
import { useEffect, useMemo, useState } from "react";

import { listDataRoutes, type BranchScope, type TvDataRouteCatalogItem } from "../../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { comunicadoBlockTypeLabel } from "../../utils/comunicadoBlockLabels";
import { DataBindingInspector } from "../DataBindingInspector";
import { ChartViewOptionsInspector } from "../ChartViewOptionsInspector";
import { TableViewOptionsInspector } from "../TableViewOptionsInspector";
import { VisualDataViewInspector } from "../VisualDataViewInspector";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import {
  SelectionSectionsHost,
  SelectionTypedWithTailHost,
} from "../selectionSections";
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
    selectedTablePart,
    selectedInputPart,
    updateSelected,
    updateBlockLink,
  } = useComunicadoEditor();

  const hasPartSelection = Boolean(
    selectedKpiPart || selectedChartPart || selectedTablePart || selectedInputPart,
  );

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
                updateBlockLink(selected.id, normalizeHrefInput(value) || undefined)
              }
            />
          </DeckField>
        ) : null}
      </DeckPropertySection>

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

      {!multiSelect && selected.type === "chart_view" && !selectedChartPart ? (
        <>
          <SelectionTypedWithTailHost
            layout="pane"
            labels={labels}
            typed={[
              "typography",
              "chartLayout",
              "chartStyles",
              "chartType",
              "chartLabels",
              "chartAxes",
              "chartSeries",
            ]}
          />
          <ChartViewOptionsInspector pane={pane} omitSeries />
        </>
      ) : null}

      {!multiSelect && selected.type === "table_view" && !selectedTablePart ? (
        <>
          <SelectionTypedWithTailHost
            layout="pane"
            labels={labels}
            typed={["tableStyleOptions", "tableStyles", "tableBorders"]}
          />
          <TableViewOptionsInspector pane={pane} omitDesignChrome />
        </>
      ) : null}

      {!multiSelect && selected.type === "table_view" && selectedTablePart ? (
        <TableViewOptionsInspector pane={pane} omitDesignChrome />
      ) : null}

      {multiSelect ? (
        <SelectionSectionsHost layout="pane" full labels={labels} />
      ) : null}

      {!multiSelect && isShapeBlock && shapeOptionsTab === "text" ? (
        <SelectionSectionsHost layout="pane" only={["typography"]} labels={labels} />
      ) : null}

      {!multiSelect && isShapeBlock && shapeOptionsTab === "shape" && !hasPartSelection ? (
        <div id="td-shape-pane-size">
          <SelectionTypedWithTailHost
            layout="pane"
            labels={labels}
            typed={["shapeGallery", "shapeChrome"]}
          />
        </div>
      ) : null}

      {/* texto, heading, icon, media, canvas, kpi, input, data_source — host full */}
      {!multiSelect &&
      !isShapeBlock &&
      selected.type !== "table_view" &&
      selected.type !== "chart_view" &&
      !hasPartSelection ? (
        <SelectionSectionsHost layout="pane" full labels={labels} />
      ) : null}

      {!multiSelect && hasPartSelection ? (
        <SelectionSectionsHost layout="pane" full labels={labels} />
      ) : null}
    </DeckInspectorLayout>
  );
}
