import { ArrowDown, ArrowUp, FolderOpen, Move, PaintBucket, Pentagon, Trash2, Upload } from "lucide-react";
import {
  FormSelectControl,
  HintAction,
  NativeCheckboxControl,
  NativeTextControl,
  ShapeFillMenu,
  ShapeOutlineMenu,
  ShapeShadowMenu,
  DECK_COLOR_BORDER,
  DECK_COLOR_SURFACE,
} from "@delpi/plugin-ui/index";
import {
  BLOCK_ENTRANCE_DELAY_MAX_MS,
  BLOCK_ENTRANCE_DELAY_MIN_MS,
  BLOCK_ENTRANCE_DELAY_STEP_MS,
  BLOCK_ENTRANCE_DURATION_DEFAULT_MS,
  BLOCK_ENTRANCE_DURATION_MAX_MS,
  BLOCK_ENTRANCE_DURATION_MIN_MS,
  BLOCK_ENTRANCE_DURATION_STEP_MS,
  BLOCK_ENTRANCE_PRESET_OPTIONS,
  entranceAnimationFromPreset,
  entrancePresetValue,
  formatDesignPx,
  framePercentToPageBottomLeftPx,
  isDataBlockType,
  isDataSourceBlockType,
  isDataViewBlockType,
  isComunicadoVisualBoxBlock,
  isPointShapeKind,
  normalizeHrefInput,
  normalizeCanvasTableCells,
  patchComunicadoFramePageBottomLeftPx,
  resolveEntranceAnimation,
  resolveViewportPixelSize,
  shapeHasAdjustments,
  visualBoxSupportsShapeFormatting,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";
import { useEffect, useMemo, useState } from "react";

import { listDataRoutes, type BranchScope, type TvDataRouteCatalogItem } from "../../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { comunicadoBlockTypeLabel } from "../../utils/comunicadoBlockLabels";
import { DataBindingInspector } from "../DataBindingInspector";
import { ChartViewOptionsInspector } from "../ChartViewOptionsInspector";
import { KpiViewOptionsInspector } from "../KpiViewOptionsInspector";
import { ShapeAdjustmentsControl } from "../ShapeAdjustmentsControl";
import { TableViewOptionsInspector } from "../TableViewOptionsInspector";
import { VisualDataViewInspector } from "../VisualDataViewInspector";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { ComunicadoImageCropPanel } from "./ComunicadoImageCropPanel";
import { DeckActionRow } from "./DeckActionRow";
import { DeckField } from "./DeckField";
import { DeckInspectorLayout } from "./DeckInspectorLayout";
import { DeckPropertySection } from "./DeckPropertySection";
import { COMUNICADO_BOX_SHADOW_PRESETS } from "../../content/comunicadoVisualPresets";

const E = TV_DASHBOARD_HELP_TOOLTIPS.element;

const SHAPE_PANE_ICONS = [
  { id: "fill-line", label: "Preenchimento e linha", Icon: PaintBucket },
  { id: "effects", label: "Efeitos", Icon: Pentagon },
  { id: "size", label: "Tamanho e posição", Icon: Move },
] as const;

const SHADOW_MENU_PRESETS = COMUNICADO_BOX_SHADOW_PRESETS.map((preset) => ({
  id: preset.key,
  label: preset.label,
  value: preset.value,
}));

const FRAME_KEYS = ["x", "y", "w", "h"] as const;
const FRAME_LABELS: Record<(typeof FRAME_KEYS)[number], string> = {
  x: "X px",
  y: "Y px",
  w: "Largura px",
  h: "Altura px",
};

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
    uploading,
    updateSelected,
    updateSelectedStyle,
    removeSelected,
    moveLayer,
    triggerUpload,
    openMediaLibrary,
    updateBlockLink,
    viewportProfile,
  } = useComunicadoEditor();

  const slideDesign = resolveViewportPixelSize(viewportProfile);
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

  useEffect(() => {
    if (!isDataBlock) return;
    void listDataRoutes().then(setRoutes).catch(() => setRoutes([]));
  }, [isDataBlock]);

  useEffect(() => {
    if (!isShapeBlock) return;
    const el = document.getElementById(`td-shape-pane-${shapePaneIcon}`);
    el?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [shapePaneIcon, isShapeBlock]);

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
        <div className="td-format-pane-icons" role="tablist" aria-label="Opções de forma">
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

        {!multiSelect && isShapeBlock ? (
          <>
            <DeckField id="td-shape-content" label="Texto na forma" hint={E.shapeText}>
              <NativeTextControl
                id="td-shape-content"
                type="text"
                value={selected.content ?? ""}
                onChange={(value) => updateSelected({ content: value } as Partial<ComunicadoBlock>)}
              />
            </DeckField>
          </>
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
        <TableViewOptionsInspector pane={pane} />
      ) : null}
      {!multiSelect && selected?.type === "kpi_view" ? (
        <KpiViewOptionsInspector pane={pane} />
      ) : null}

      {!multiSelect && selected.type === "image" ? (
        <div id="td-comunicado-crop-panel">
          <ComunicadoImageCropPanel />
        </div>
      ) : null}

      {!multiSelect ? (
        <DeckPropertySection
          pane={pane}
          title="Animação de entrada"
          hint={E.entranceAnimation}
          defaultOpen={false}
        >
          <DeckField id="td-entrance-kind" label="Efeito" hint={E.entranceAnimation}>
            <FormSelectControl
              id="td-entrance-kind"
              ariaLabel="Efeito"
              value={entrancePresetValue(resolveEntranceAnimation(selected.animations))}
              onChange={(value) => {
                const entrance = resolveEntranceAnimation(selected.animations);
                updateSelected({
                  animations: entranceAnimationFromPreset(value, {
                    delayMs: entrance?.delayMs ?? 0,
                    durationMs: entrance?.durationMs ?? BLOCK_ENTRANCE_DURATION_DEFAULT_MS,
                  }),
                } as Partial<ComunicadoBlock>);
              }}
              options={BLOCK_ENTRANCE_PRESET_OPTIONS.map((option) => ({
                value: option.value,
                label: option.label,
              }))}
            />
          </DeckField>
          {resolveEntranceAnimation(selected.animations) ? (
            <>
              <DeckField id="td-entrance-delay" label="Atraso (ms)" hint={E.entranceDelay}>
                <NativeTextControl
                  id="td-entrance-delay"
                  type="number"
                  min={BLOCK_ENTRANCE_DELAY_MIN_MS}
                  max={BLOCK_ENTRANCE_DELAY_MAX_MS}
                  step={BLOCK_ENTRANCE_DELAY_STEP_MS}
                  value={resolveEntranceAnimation(selected.animations)?.delayMs ?? 0}
                  onChange={(value) => {
                    const entrance = resolveEntranceAnimation(selected.animations);
                    if (!entrance) return;
                    updateSelected({
                      animations: entranceAnimationFromPreset(entrancePresetValue(entrance), {
                        delayMs: Number(value),
                        durationMs: entrance.durationMs ?? BLOCK_ENTRANCE_DURATION_DEFAULT_MS,
                      }),
                    } as Partial<ComunicadoBlock>);
                  }}
                />
              </DeckField>
              <DeckField id="td-entrance-duration" label="Duração (ms)" hint={E.entranceDuration}>
                <NativeTextControl
                  id="td-entrance-duration"
                  type="number"
                  min={BLOCK_ENTRANCE_DURATION_MIN_MS}
                  max={BLOCK_ENTRANCE_DURATION_MAX_MS}
                  step={BLOCK_ENTRANCE_DURATION_STEP_MS}
                  value={
                    resolveEntranceAnimation(selected.animations)?.durationMs ??
                    BLOCK_ENTRANCE_DURATION_DEFAULT_MS
                  }
                  onChange={(value) => {
                    const entrance = resolveEntranceAnimation(selected.animations);
                    if (!entrance) return;
                    updateSelected({
                      animations: entranceAnimationFromPreset(entrancePresetValue(entrance), {
                        delayMs: entrance.delayMs ?? 0,
                        durationMs: Number(value),
                      }),
                    } as Partial<ComunicadoBlock>);
                  }}
                />
              </DeckField>
            </>
          ) : null}
        </DeckPropertySection>
      ) : null}

      {!multiSelect && isShapeBlock ? (
        <>
          <div id="td-shape-pane-fill-line">
            <DeckPropertySection pane={pane} title="Preenchimento e linha" defaultOpen>
              <div className="td-deck-ribbon__tiles td-deck-ribbon__tiles--compact td-deck-ribbon__tiles--shape-menus">
                <ShapeFillMenu
                  value={selected.style?.fill ?? DECK_COLOR_SURFACE}
                  onChange={(color) => updateSelectedStyle({ fill: color })}
                  onNoFill={() => updateSelectedStyle({ fill: "transparent" })}
                />
                <ShapeOutlineMenu
                  color={selected.style?.stroke ?? DECK_COLOR_BORDER}
                  strokeWidth={selected.style?.strokeWidth ?? 2}
                  minWidth={0}
                  maxWidth={20}
                  onColorChange={(color) => updateSelectedStyle({ stroke: color })}
                  onNoOutline={() => updateSelectedStyle({ stroke: "transparent", strokeWidth: 0 })}
                  onStrokeWidthChange={(width) => updateSelectedStyle({ strokeWidth: width })}
                />
              </div>
            </DeckPropertySection>
          </div>
          <div id="td-shape-pane-effects">
            <DeckPropertySection pane={pane} title="Efeitos" defaultOpen={false}>
              <ShapeShadowMenu
                value={selected.style?.boxShadow}
                presets={SHADOW_MENU_PRESETS}
                shadowLabel="Sombra"
                onChange={(boxShadow) => updateSelectedStyle({ boxShadow })}
              />
            </DeckPropertySection>
          </div>
        </>
      ) : null}

      {!multiSelect && !selectedKpiPart && !selectedChartPart ? (
        <div id={isShapeBlock ? "td-shape-pane-size" : undefined}>
        <DeckPropertySection pane={pane} title="Posição e tamanho" hint={E.position} defaultOpen={false}>
          {(() => {
            const pointOnly =
              selected.type === "shape" && isPointShapeKind(selected.shape);
            const framePx = framePercentToPageBottomLeftPx(selected.frame, slideDesign);
            return (
              <>
                <div className="td-deck-frame-grid">
                  {(pointOnly ? (["x", "y"] as const) : FRAME_KEYS).map((key) => (
                    <DeckField
                      key={key}
                      id={`td-frame-${key}`}
                      label={FRAME_LABELS[key]}
                      hint={E.position}
                      className="td-field--compact"
                    >
                      <NativeTextControl
                        id={`td-frame-${key}`}
                        type="number"
                        min={key === "w" || key === "h" ? 1 : 0}
                        max={key === "x" || key === "w" ? slideDesign.width : slideDesign.height}
                        step={1}
                        value={String(formatDesignPx(framePx[key]))}
                        onChange={(value) =>
                          updateSelected({
                            frame: patchComunicadoFramePageBottomLeftPx(
                              selected.frame,
                              key,
                              Number(value),
                              slideDesign,
                            ),
                          } as Partial<ComunicadoBlock>)
                        }
                      />
                    </DeckField>
                  ))}
                </div>
                <DeckField id="td-rotation" label="Rotação (°)" hint={E.rotation}>
                  <NativeTextControl
                    id="td-rotation"
                    type="number"
                    min={-180}
                    max={180}
                    step={1}
                    value={selected.style?.rotation ?? 0}
                    onChange={(value) => updateSelectedStyle({ rotation: Number(value) })}
                  />
                </DeckField>
                {selected.type === "shape" && shapeHasAdjustments(selected.shape) ? (
                  <ShapeAdjustmentsControl
                    kind={selected.shape}
                    style={selected.style}
                    onChange={(patch) => updateSelectedStyle(patch)}
                    variant="inspector"
                    idPrefix="td-frame-shape-adj"
                  />
                ) : null}
              </>
            );
          })()}
        </DeckPropertySection>
        </div>
      ) : null}

      <DeckPropertySection pane={pane} title="Ações" hint={E.layerUp} defaultOpen={false}>
        <DeckActionRow>
          {!multiSelect ? (
            <>
              <HintAction hint={E.layerUp} ariaLabel="Ajuda: trazer frente">
                <button type="button" className="td-btn td-btn--sm" onClick={() => moveLayer("up")}>
                  <ArrowUp size={15} aria-hidden="true" />
                  Trazer frente
                </button>
              </HintAction>
              <HintAction hint={E.layerDown} ariaLabel="Ajuda: enviar fundo">
                <button type="button" className="td-btn td-btn--sm" onClick={() => moveLayer("down")}>
                  <ArrowDown size={15} aria-hidden="true" />
                  Enviar fundo
                </button>
              </HintAction>
            </>
          ) : null}
          <HintAction hint={E.remove} ariaLabel="Ajuda: remover">
            <button type="button" className="td-btn td-btn--danger td-btn--sm" onClick={removeSelected}>
              <Trash2 size={15} aria-hidden="true" />
              Remover
            </button>
          </HintAction>
        </DeckActionRow>
      </DeckPropertySection>
    </DeckInspectorLayout>
  );
}
