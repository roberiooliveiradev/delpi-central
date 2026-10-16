import { useCallback, useState, type DragEvent } from "react";

/** Reordena item de `from` para `to` (imutável). */
export function moveArrayItem<T>(items: T[], from: number, to: number): T[] {
  if (from === to || from < 0 || to < 0 || from >= items.length || to >= items.length) {
    return items;
  }
  const next = [...items];
  const [item] = next.splice(from, 1);
  next.splice(to, 0, item!);
  return next;
}

/**
 * HTML5 drag-and-drop para reordenar linhas da carga máquina (CT ativo).
 * Padrão alinhado a `useProjectionDragReorder` do TV Dashboard.
 *
 * `options.enabled=false` suspende arraste e drop sem remover os handlers —
 * usado quando a seleção múltipla está ativa (o arraste é individual).
 */
export function useMachineLoadRowReorder<T>(
  items: T[],
  onReorder: (next: T[]) => void,
  options: { enabled?: boolean } = {},
) {
  const { enabled = true } = options;
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);
  const [overIndex, setOverIndex] = useState<number | null>(null);
  const canDrag = enabled && items.length > 1;

  const handleDragStart = useCallback((index: number, event: DragEvent) => {
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", String(index));
    setDraggedIndex(index);
  }, []);

  const handleDragEnd = useCallback(() => {
    setDraggedIndex(null);
    setOverIndex(null);
  }, []);

  const handleDragOver = useCallback(
    (index: number, event: DragEvent) => {
      if (!enabled) return;
      event.preventDefault();
      event.dataTransfer.dropEffect = "move";
      if (draggedIndex !== null && draggedIndex !== index) {
        setOverIndex(index);
      }
    },
    [draggedIndex, enabled],
  );

  const handleDrop = useCallback(
    (index: number, event: DragEvent) => {
      if (!enabled) return;
      event.preventDefault();
      const from =
        draggedIndex ?? Number.parseInt(event.dataTransfer.getData("text/plain"), 10);
      if (!Number.isNaN(from) && from !== index) {
        onReorder(moveArrayItem(items, from, index));
      }
      setDraggedIndex(null);
      setOverIndex(null);
    },
    [draggedIndex, enabled, items, onReorder],
  );

  const rowClassName = useCallback(
    (index: number) =>
      [
        draggedIndex === index ? "ppc-load__row--dragging" : "",
        overIndex === index && draggedIndex !== null && draggedIndex !== index
          ? "ppc-load__row--drop-target"
          : "",
      ]
        .filter(Boolean)
        .join(" ") || undefined,
    [draggedIndex, overIndex],
  );

  const rowDropProps = useCallback(
    (index: number) => ({
      onDragOver: (event: DragEvent) => handleDragOver(index, event),
      onDrop: (event: DragEvent) => handleDrop(index, event),
      onDragEnd: handleDragEnd,
    }),
    [handleDragEnd, handleDragOver, handleDrop],
  );

  const handleProps = useCallback(
    (index: number) => ({
      draggable: canDrag,
      onDragStart: (event: DragEvent) => handleDragStart(index, event),
      onDragEnd: handleDragEnd,
    }),
    [canDrag, handleDragEnd, handleDragStart],
  );

  return {
    canDrag,
    draggedIndex,
    overIndex,
    rowClassName,
    rowDropProps,
    handleProps,
  };
}
