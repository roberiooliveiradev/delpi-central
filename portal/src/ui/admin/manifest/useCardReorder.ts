// portal/src/ui/admin/manifest/useCardReorder.ts

import { useRef, useState, type DragEvent, type KeyboardEvent } from "react";

const HANDLE_ATTR = "data-card-reorder-handle";

type Options = {
  /** Quantidade de cards da lista — limita o alvo do arraste e das setas. */
  count: number;
  disabled?: boolean;
  /** Rótulo singular usado no `aria-label` da alça (ex.: "rota"). */
  itemLabel: string;
  onMove: (from: number, to: number) => void;
};

/**
 * Arrastar/soltar cards do editor de manifesto com equivalente por teclado.
 * Compartilhado por rotas e permissões — a ordem é posicional nos dois casos.
 */
export function useCardReorder({ count, disabled, itemLabel, onMove }: Options) {
  const [dragIndex, setDragIndex] = useState<number | null>(null);
  const [dropIndex, setDropIndex] = useState<number | null>(null);
  const cardRefs = useRef<(HTMLLIElement | null)[]>([]);

  const move = (from: number, to: number) => {
    if (disabled || from === to || to < 0 || to >= count) return;
    onMove(from, to);
    // Mantém a alça sob o teclado depois que o card troca de posição.
    requestAnimationFrame(() => {
      cardRefs.current[to]
        ?.querySelector<HTMLButtonElement>(`[${HANDLE_ATTR}]`)
        ?.focus();
    });
  };

  const endDrag = () => {
    setDragIndex(null);
    setDropIndex(null);
  };

  const getCardProps = (index: number, className: string) => ({
    ref: (node: HTMLLIElement | null) => {
      cardRefs.current[index] = node;
    },
    className: [
      className,
      dragIndex === index ? `${className}--dragging` : "",
      dropIndex === index && dragIndex !== index
        ? `${className}--drop-target`
        : "",
    ]
      .filter(Boolean)
      .join(" "),
    onDragOver: (event: DragEvent<HTMLLIElement>) => {
      if (dragIndex === null) return;
      event.preventDefault();
      event.dataTransfer.dropEffect = "move";
      if (index !== dropIndex) setDropIndex(index);
    },
    onDrop: (event: DragEvent<HTMLLIElement>) => {
      event.preventDefault();
      if (dragIndex !== null) move(dragIndex, index);
      endDrag();
    },
  });

  const getHandleProps = (index: number) => ({
    [HANDLE_ATTR]: "",
    type: "button" as const,
    draggable: !disabled,
    disabled,
    "aria-label": `Reordenar ${itemLabel} ${index + 1} de ${count}. Arraste ou use as setas.`,
    title: "Arraste para reordenar (ou use ↑ ↓)",
    onDragStart: (event: DragEvent<HTMLButtonElement>) => {
      if (disabled) return;
      setDragIndex(index);
      event.dataTransfer.effectAllowed = "move";
      // Firefox só inicia o arraste quando há payload definido.
      event.dataTransfer.setData("text/plain", String(index));
      const card = cardRefs.current[index];
      if (card) event.dataTransfer.setDragImage(card, 24, 24);
    },
    onDragEnd: endDrag,
    onKeyDown: (event: KeyboardEvent<HTMLButtonElement>) => {
      if (event.key === "ArrowUp") {
        event.preventDefault();
        move(index, index - 1);
      } else if (event.key === "ArrowDown") {
        event.preventDefault();
        move(index, index + 1);
      }
    },
  });

  return { getCardProps, getHandleProps };
}
