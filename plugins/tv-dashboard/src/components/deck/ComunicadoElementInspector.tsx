import { ArrowDown, ArrowUp, FolderOpen, Trash2, Upload } from "lucide-react";
import { HintAction } from "@delpi/plugin-ui/index";
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
  isDataBlockType,
  isDataSourceBlockType,
  isDataViewBlockType,
  isComunicadoVisualBoxBlock,
  normalizeHrefInput,
  resolveEntranceAnimation,
  isPointShapeKind,
  visualBoxSupportsShapeFormatting,
} from "@delpi/tv-dashboard-presentation";
import { useEffect, useMemo, useState } from "react";

import { listDataRoutes, type TvDataRouteCatalogItem } from "../../api/tvDashboardApi";
import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { DataBindingInspector } from "../DataBindingInspector";
import { ChartViewOptionsInspector } from "../ChartViewOptionsInspector";
import { TableViewOptionsInspector } from "../TableViewOptionsInspector";
import { VisualDataViewInspector } from "../VisualDataViewInspector";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { ComunicadoImageCropPanel } from "./ComunicadoImageCropPanel";
import { DeckActionRow } from "./DeckActionRow";
import { DeckField } from "./DeckField";
import { DeckInspectorLayout } from "./DeckInspectorLayout";
import { DeckPropertySection } from "./DeckPropertySection";

const E = TV_DASHBOARD_HELP_TOOLTIPS.element;

const FRAME_KEYS = ["x", "y", "w", "h"] as const;
const FRAME_LABELS: Record<(typeof FRAME_KEYS)[number], string> = {
  x: "X %",
  y: "Y %",
  w: "Largura %",
  h: "Altura %",
};

type Labels = Record<string, string>;

function formatFrameValue(value: number): string {
  return String(Math.round(value * 10) / 10);
}

export function ComunicadoElementInspector({
  labels = {},
  placement = "default",
  onOpenDataSources,
}: {
  labels?: Labels;
  placement?: "default" | "side";
  onOpenDataSources?: () => void;
}) {
  const {
    selected,
    selectedIds,
    uploading,
    updateSelected,
    updateSelectedStyle,
    removeSelected,
    moveLayer,
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

  useEffect(() => {
    if (!isDataBlock) return;
    void listDataRoutes().then(setRoutes).catch(() => setRoutes([]));
  }, [isDataBlock]);

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

  return (
    <DeckInspectorLayout variant={placement}>
      <DeckPropertySection
        pane={pane}
        title={labels.comunicadoBlocks ?? "Elemento selecionado"}
        hint={E.panel}
      >
        {multiSelect ? (
          <p className="td-deck-inspector__meta td-deck-inspector__meta--multi">
            {selectedIds.length} elementos selecionados — edite texto e link direto no palco.
          </p>
        ) : (
          <p className="td-deck-inspector__meta">Tipo: {selected.type}</p>
        )}

        {!multiSelect && isDataBlock ? <DataBindingInspector route={selectedRoute} pane={pane} /> : null}
        {!multiSelect && isViewBlock ? (
          <VisualDataViewInspector pane={pane} onOpenDataSources={onOpenDataSources} />
        ) : null}
        {!multiSelect && selected?.type === "chart_view" ? (
          <ChartViewOptionsInspector pane={pane} />
        ) : null}
        {!multiSelect && selected?.type === "table_view" ? (
          <TableViewOptionsInspector pane={pane} />
        ) : null}

        {!multiSelect && isShapeBlock ? (
          <>
            <DeckField id="td-shape-content" label="Texto na forma" hint={E.shapeText}>
              <input
                id="td-shape-content"
                type="text"
                value={selected.content ?? ""}
                onChange={(e) => updateSelected({ content: e.target.value } as Partial<typeof selected>)}
              />
            </DeckField>
            <DeckField id="td-shape-stroke-width" label="Espessura do contorno" hint={E.strokeWidth}>
              <input
                id="td-shape-stroke-width"
                type="number"
                min={0}
                max={20}
                value={selected.style?.strokeWidth ?? 2}
                onChange={(e) => updateSelectedStyle({ strokeWidth: Number(e.target.value) })}
              />
            </DeckField>
          </>
        ) : null}

        {!multiSelect && isSidebarLinkBlock ? (
          <DeckField id="td-block-link" label="Link" hint={E.link}>
            <input
              id="td-block-link"
              type="url"
              placeholder="https://…"
              value={selected.href ?? ""}
              onChange={(e) =>
                updateBlockLink(
                  selected.id,
                  normalizeHrefInput(e.target.value) || undefined,
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

      {!multiSelect && selected.type === "image" ? (
        <div id="td-comunicado-crop-panel">
          <ComunicadoImageCropPanel />
        </div>
      ) : null}

      {!multiSelect ? (
        <DeckPropertySection pane={pane} title="Animação de entrada" hint={E.entranceAnimation}>
          <DeckField id="td-entrance-kind" label="Efeito" hint={E.entranceAnimation}>
            <select
              id="td-entrance-kind"
              value={entrancePresetValue(resolveEntranceAnimation(selected.animations))}
              onChange={(e) => {
                const entrance = resolveEntranceAnimation(selected.animations);
                updateSelected({
                  animations: entranceAnimationFromPreset(e.target.value, {
                    delayMs: entrance?.delayMs ?? 0,
                    durationMs: entrance?.durationMs ?? BLOCK_ENTRANCE_DURATION_DEFAULT_MS,
                  }),
                } as Partial<typeof selected>);
              }}
            >
              {BLOCK_ENTRANCE_PRESET_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </DeckField>
          {resolveEntranceAnimation(selected.animations) ? (
            <>
              <DeckField id="td-entrance-delay" label="Atraso (ms)" hint={E.entranceDelay}>
                <input
                  id="td-entrance-delay"
                  type="number"
                  min={BLOCK_ENTRANCE_DELAY_MIN_MS}
                  max={BLOCK_ENTRANCE_DELAY_MAX_MS}
                  step={BLOCK_ENTRANCE_DELAY_STEP_MS}
                  value={resolveEntranceAnimation(selected.animations)?.delayMs ?? 0}
                  onChange={(e) => {
                    const entrance = resolveEntranceAnimation(selected.animations);
                    if (!entrance) return;
                    updateSelected({
                      animations: entranceAnimationFromPreset(entrancePresetValue(entrance), {
                        delayMs: Number(e.target.value),
                        durationMs: entrance.durationMs ?? BLOCK_ENTRANCE_DURATION_DEFAULT_MS,
                      }),
                    } as Partial<typeof selected>);
                  }}
                />
              </DeckField>
              <DeckField id="td-entrance-duration" label="Duração (ms)" hint={E.entranceDuration}>
                <input
                  id="td-entrance-duration"
                  type="number"
                  min={BLOCK_ENTRANCE_DURATION_MIN_MS}
                  max={BLOCK_ENTRANCE_DURATION_MAX_MS}
                  step={BLOCK_ENTRANCE_DURATION_STEP_MS}
                  value={
                    resolveEntranceAnimation(selected.animations)?.durationMs ??
                    BLOCK_ENTRANCE_DURATION_DEFAULT_MS
                  }
                  onChange={(e) => {
                    const entrance = resolveEntranceAnimation(selected.animations);
                    if (!entrance) return;
                    updateSelected({
                      animations: entranceAnimationFromPreset(entrancePresetValue(entrance), {
                        delayMs: entrance.delayMs ?? 0,
                        durationMs: Number(e.target.value),
                      }),
                    } as Partial<typeof selected>);
                  }}
                />
              </DeckField>
            </>
          ) : null}
        </DeckPropertySection>
      ) : null}

      {!multiSelect ? (
        <DeckPropertySection pane={pane} title="Posição e tamanho" hint={E.position}>
          <div className="td-deck-frame-grid">
            {(selected.type === "shape" && isPointShapeKind(selected.shape)
              ? (["x", "y"] as const)
              : FRAME_KEYS
            ).map((key) => (
              <DeckField
                key={key}
                id={`td-frame-${key}`}
                label={FRAME_LABELS[key]}
                hint={E.position}
                className="td-field--compact"
              >
                <input
                  id={`td-frame-${key}`}
                  type="number"
                  min={0}
                  max={100}
                  step={0.1}
                  value={formatFrameValue(selected.frame[key])}
                  onChange={(e) =>
                    updateSelected({
                      frame: { ...selected.frame, [key]: Number(e.target.value) },
                    } as Partial<typeof selected>)
                  }
                />
              </DeckField>
            ))}
          </div>
          <DeckField id="td-rotation" label="Rotação (°)" hint={E.rotation}>
            <input
              id="td-rotation"
              type="number"
              min={-180}
              max={180}
              step={1}
              value={selected.style?.rotation ?? 0}
              onChange={(e) => updateSelectedStyle({ rotation: Number(e.target.value) })}
            />
          </DeckField>
        </DeckPropertySection>
      ) : null}

      <DeckPropertySection pane={pane} title="Ações" hint={E.layerUp}>
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
