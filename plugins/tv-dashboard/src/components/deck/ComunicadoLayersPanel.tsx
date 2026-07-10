import { useMemo, useState } from "react";
import { GripVertical } from "lucide-react";
import { sortBlocksByZIndex } from "@delpi/tv-dashboard-presentation";

import { useComunicadoEditor } from "../comunicadoEditorContext";
import { comunicadoBlockSummary, comunicadoBlockTypeLabel } from "../../utils/comunicadoBlockLabels";
import { DeckPropertySection } from "./DeckPropertySection";

export function ComunicadoLayersPanel({ pane = true }: { pane?: boolean }) {
  const {
    blocks,
    selectedIds,
    selectBlock,
    selectBlocksByIds,
    reorderBlockLayer,
  } = useComunicadoEditor();
  const [dragId, setDragId] = useState<string | null>(null);

  const layers = useMemo(() => {
    return [...sortBlocksByZIndex(blocks)].reverse();
  }, [blocks]);

  function onDrop(targetId: string) {
    if (!dragId || dragId === targetId) return;
    const targetReversedIndex = layers.findIndex((block) => block.id === targetId);
    if (targetReversedIndex < 0) return;
    const sorted = sortBlocksByZIndex(blocks);
    const targetIndex = sorted.length - 1 - targetReversedIndex;
    reorderBlockLayer(dragId, targetIndex);
    setDragId(null);
  }

  return (
    <DeckPropertySection
      pane={pane}
      title="Lista de camadas"
      hint="Selecione ou reordene elementos. Shift+clique para multi-seleção no palco."
      defaultOpen
    >
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
                  <GripVertical size={14} className="td-layers-list__handle" aria-hidden="true" />
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
        <button type="button" className="td-btn td-btn--sm" onClick={() => selectBlocksByIds([selectedIds[0]])}>
          Focar primeiro selecionado
        </button>
      ) : null}
    </DeckPropertySection>
  );
}
