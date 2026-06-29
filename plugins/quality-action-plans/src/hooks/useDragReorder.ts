import { useCallback, useState, type DragEvent } from "react";

import { moveArrayItem } from "../utils/arrayOrder";

export function useDragReorder<T>(items: T[], onReorder: (next: T[]) => void) {
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);
  const [overIndex, setOverIndex] = useState<number | null>(null);

  const canDrag = items.length > 1;

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
      event.preventDefault();
      event.dataTransfer.dropEffect = "move";
      if (draggedIndex !== null && draggedIndex !== index) {
        setOverIndex(index);
      }
    },
    [draggedIndex],
  );

  const handleDrop = useCallback(
    (index: number, event: DragEvent) => {
      event.preventDefault();
      const from =
        draggedIndex ?? Number.parseInt(event.dataTransfer.getData("text/plain"), 10);
      if (!Number.isNaN(from) && from !== index) {
        onReorder(moveArrayItem(items, from, index));
      }
      setDraggedIndex(null);
      setOverIndex(null);
    },
    [draggedIndex, items, onReorder],
  );

  const rowClassName = useCallback(
    (baseClass: string, index: number) =>
      [
        baseClass,
        draggedIndex === index ? "pac-row--dragging" : "",
        overIndex === index && draggedIndex !== null && draggedIndex !== index
          ? "pac-row--drag-over"
          : "",
      ]
        .filter(Boolean)
        .join(" "),
    [draggedIndex, overIndex],
  );

  const rowDropProps = useCallback(
    (index: number) => ({
      onDragOver: (event: DragEvent) => handleDragOver(index, event),
      onDrop: (event: DragEvent) => handleDrop(index, event),
    }),
    [handleDragOver, handleDrop],
  );

  const handleDragProps = useCallback(
    (index: number) => ({
      draggable: canDrag,
      onDragStart: (event: DragEvent) => handleDragStart(index, event),
      onDragEnd: handleDragEnd,
    }),
    [canDrag, handleDragEnd, handleDragStart],
  );

  return { canDrag, rowClassName, rowDropProps, handleDragProps };
}
