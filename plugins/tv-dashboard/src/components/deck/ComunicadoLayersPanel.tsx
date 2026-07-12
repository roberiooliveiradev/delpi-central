import { useMemo, useState } from "react";
import { GripVertical } from "lucide-react";
import { HintAction } from "@delpi/plugin-ui/index";
import {
  assignStaggeredEntranceDelays,
  clearEntranceAnimations,
  resolveEntranceAnimation,
  sortBlocksByZIndex,
  syncEntranceDelaysSameInstant,
  type ComunicadoBlockAnimation,
} from "@delpi/tv-dashboard-presentation";

import { TV_DASHBOARD_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { useComunicadoEditor } from "../comunicadoEditorContext";
import { comunicadoBlockSummary, comunicadoBlockTypeLabel } from "../../utils/comunicadoBlockLabels";
import { DeckPropertySection } from "./DeckPropertySection";

const L = TV_DASHBOARD_HELP_TOOLTIPS.layers;

type Props = {
  pane?: boolean;
  /** ribbon = grade full-width na top bar; pane = painel lateral. */
  layout?: "ribbon" | "pane";
};

export function ComunicadoLayersPanel({ pane = true, layout = "pane" }: Props) {
  const {
    blocks,
    selectedIds,
    selectBlock,
    selectBlocksByIds,
    reorderBlockLayer,
    updateBlock,
  } = useComunicadoEditor();
  const [dragId, setDragId] = useState<string | null>(null);
  const isRibbon = layout === "ribbon";

  const layers = useMemo(() => [...sortBlocksByZIndex(blocks)].reverse(), [blocks]);

  const buildOrder = useMemo(
    () =>
      sortBlocksByZIndex(blocks).map((block) => ({
        id: block.id,
        label: comunicadoBlockSummary(block),
        type: comunicadoBlockTypeLabel(block.type),
        delayMs: resolveEntranceAnimation(block.animations)?.delayMs ?? 0,
        hasAnim: Boolean(resolveEntranceAnimation(block.animations)),
      })),
    [blocks],
  );

  function onDrop(targetId: string) {
    if (!dragId || dragId === targetId) return;
    const targetReversedIndex = layers.findIndex((block) => block.id === targetId);
    if (targetReversedIndex < 0) return;
    const sorted = sortBlocksByZIndex(blocks);
    const targetIndex = sorted.length - 1 - targetReversedIndex;
    reorderBlockLayer(dragId, targetIndex);
    setDragId(null);
  }

  function applyBuildMap(map: Map<string, ComunicadoBlockAnimation[] | undefined>) {
    for (const [id, animations] of map.entries()) {
      updateBlock(id, { animations });
    }
  }

  const buildOrderSection = (
    <>
      {buildOrder.length === 0 ? (
        <p className="td-subtitle">Nenhum elemento no slide.</p>
      ) : (
        <ol className="td-build-order">
          {buildOrder.map((item, index) => (
            <li key={item.id} className="td-build-order__item">
              <span className="td-build-order__index">{index + 1}</span>
              <span className="td-build-order__meta">
                <span className="td-build-order__type">{item.type}</span>
                <span className="td-build-order__summary">{item.label}</span>
              </span>
              <span className="td-build-order__delay">{item.hasAnim ? `${item.delayMs} ms` : "—"}</span>
            </li>
          ))}
        </ol>
      )}
      <div className="td-build-order__actions">
        <HintAction hint={L.buildSequenciar} ariaLabel="Ajuda: Sequenciar">
          <button
            type="button"
            className="td-btn td-btn--sm"
            onClick={() =>
              applyBuildMap(
                assignStaggeredEntranceDelays(sortBlocksByZIndex(blocks), {
                  stepMs: 300,
                  preset: "fade",
                }),
              )
            }
          >
            Sequenciar
          </button>
        </HintAction>
        <HintAction hint={L.buildSameInstant} ariaLabel="Ajuda: Mesmo instante">
          <button
            type="button"
            className="td-btn td-btn--sm"
            onClick={() => applyBuildMap(syncEntranceDelaysSameInstant(sortBlocksByZIndex(blocks), 0))}
          >
            Mesmo instante
          </button>
        </HintAction>
        <HintAction hint={L.buildClear} ariaLabel="Ajuda: Limpar">
          <button
            type="button"
            className="td-btn td-btn--sm"
            onClick={() => applyBuildMap(clearEntranceAnimations(blocks))}
          >
            Limpar
          </button>
        </HintAction>
      </div>
    </>
  );

  const layersSection = (
    <>
      {layers.length === 0 ? (
        <p className="td-subtitle">Nenhum elemento no slide.</p>
      ) : (
        <ul className="td-layers-list">
          {layers.map((block) => {
            const active = selectedIds.includes(block.id);
            return (
              <li key={block.id}>
                <button
                  type="button"
                  className={`td-layers-list__item${active ? " td-layers-list__item--active" : ""}`}
                  draggable
                  onDragStart={() => setDragId(block.id)}
                  onDragOver={(event) => event.preventDefault()}
                  onDrop={() => onDrop(block.id)}
                  onClick={(event) => selectBlock(block.id, { additive: event.shiftKey })}
                >
                  <GripVertical size={16} className="td-layers-list__handle" aria-hidden="true" />
                  <span className="td-layers-list__meta">
                    <span className="td-layers-list__type">{comunicadoBlockTypeLabel(block.type)}</span>
                    <span className="td-layers-list__summary">{comunicadoBlockSummary(block)}</span>
                  </span>
                </button>
              </li>
            );
          })}
        </ul>
      )}
      {selectedIds.length > 1 ? (
        <button type="button" className="td-btn td-btn--sm" onClick={() => selectBlocksByIds([selectedIds[0]!])}>
          Focar primeiro selecionado
        </button>
      ) : null}
    </>
  );

  if (isRibbon) {
    return (
      <div className="td-deck-ribbon__panel td-deck-ribbon__panel--layers">
        <div className="td-deck-ribbon__panel-zone">
          <h4 className="td-deck-ribbon__panel-zone-title">Ordem de construção</h4>
          {buildOrderSection}
        </div>
        <div className="td-deck-ribbon__panel-zone">
          <h4 className="td-deck-ribbon__panel-zone-title">Lista de camadas</h4>
          {layersSection}
        </div>
      </div>
    );
  }

  return (
    <>
      <DeckPropertySection pane={pane} title="Ordem de construção" hint={L.buildOrder} defaultOpen>
        {buildOrderSection}
      </DeckPropertySection>

      <DeckPropertySection pane={pane} title="Lista de camadas" hint={L.list} defaultOpen>
        {layersSection}
      </DeckPropertySection>
    </>
  );
}
