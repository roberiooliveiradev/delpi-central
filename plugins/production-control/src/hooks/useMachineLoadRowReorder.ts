import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type DragEvent,
} from "react";

/** Reordena item de `from` para `to` (imutável). */
export function moveArrayItem<T>(items: T[], from: number, to: number): T[] {
  if (from === to || from < 0 || to < 0 || from >= items.length || to >= items.length) {
    return items;
  }
  return moveArrayItems(items, [from], to);
}

/**
 * Move um bloco de índices (ordem relativa preservada) para a posição `to`
 * — a mesma semântica de `moveArrayItem`: o bloco ocupa o lugar do alvo.
 */
export function moveArrayItems<T>(
  items: T[],
  indices: readonly number[],
  to: number,
): T[] {
  const moved = new Set(indices);
  if (!moved.size) return items;
  const block: T[] = [];
  const remaining: T[] = [];
  items.forEach((item, index) => {
    if (moved.has(index)) block.push(item);
    else remaining.push(item);
  });
  const insertAt = Math.min(remaining.length, to);
  const next = [...remaining];
  next.splice(insertAt, 0, ...block);
  return next;
}

// --- auto-scroll durante o arraste ------------------------------------------

const AUTOSCROLL_EDGE_PX = 72;
const AUTOSCROLL_MAX_SPEED_PX = 16;

/**
 * Primeiro ancestral com rolagem vertical; fallback para o scroll da página
 * — a Carga Máquina rola no documento, não num wrapper próprio.
 */
export function resolveScrollParent(el: Element | null): HTMLElement | null {
  let node = el?.parentElement ?? null;
  while (node) {
    const style = getComputedStyle(node);
    if (
      (style.overflowY === "auto" || style.overflowY === "scroll") &&
      node.scrollHeight > node.clientHeight
    ) {
      return node;
    }
    node = node.parentElement;
  }
  return (
    (document.scrollingElement as HTMLElement | null) ??
    document.documentElement
  );
}

/** Velocidade proporcional à proximidade da borda — suave e reversível. */
export function dragAutoScrollDelta(el: HTMLElement, clientY: number): number {
  const isDocument =
    el === document.documentElement ||
    el === document.body ||
    el === document.scrollingElement;
  const top = isDocument ? 0 : el.getBoundingClientRect().top;
  const bottom = isDocument
    ? window.innerHeight
    : el.getBoundingClientRect().bottom;
  if (clientY < top + AUTOSCROLL_EDGE_PX) {
    const proximity = 1 - Math.max(0, clientY - top) / AUTOSCROLL_EDGE_PX;
    return -Math.ceil(AUTOSCROLL_MAX_SPEED_PX * proximity);
  }
  if (clientY > bottom - AUTOSCROLL_EDGE_PX) {
    const proximity = 1 - Math.max(0, bottom - clientY) / AUTOSCROLL_EDGE_PX;
    return Math.ceil(AUTOSCROLL_MAX_SPEED_PX * proximity);
  }
  return 0;
}

type ReorderOptions = {
  enabled?: boolean;
  /**
   * Índices (na lista `items`) atualmente selecionados. Quando preenchido,
   * só linhas selecionadas podem ser arrastadas e o arraste move o grupo
   * inteiro como bloco contíguo — linha fora da seleção não inicia arraste.
   */
  selectedIndices?: ReadonlySet<number>;
  /**
   * Veto do chamador para o drop de grupo (≥ 2 itens): retorna `false`
   * para abortar o movimento (ex.: run aberto deslocado). Sem o callback,
   * o drop aplica o bloco direto em `onReorder`.
   */
  onBeforeGroupDrop?: (draggedIndices: number[], targetIndex: number) => boolean;
};

/**
 * HTML5 drag-and-drop para reordenar linhas da carga máquina (CT ativo).
 * Padrão alinhado a `useProjectionDragReorder` do TV Dashboard.
 *
 * Com seleção múltipla ativa (`selectedIndices`), arrastar uma linha
 * selecionada move todo o grupo como bloco contíguo. Durante qualquer
 * arraste, a página rola sozinha quando o ponteiro se aproxima das bordas
 * do contêiner de rolagem — permite soltar em posições fora da tela.
 */
export function useMachineLoadRowReorder<T>(
  items: T[],
  onReorder: (next: T[]) => void,
  options: ReorderOptions = {},
) {
  const { enabled = true, selectedIndices, onBeforeGroupDrop } = options;
  const [draggedIndices, setDraggedIndices] = useState<number[] | null>(null);
  const [overIndex, setOverIndex] = useState<number | null>(null);
  const hasGroup = Boolean(selectedIndices && selectedIndices.size >= 2);
  const canDrag = enabled && items.length > 1;

  const scrollParentRef = useRef<HTMLElement | null>(null);
  const pointerClientYRef = useRef<number | null>(null);
  const rafRef = useRef<number | null>(null);

  const handleDragStart = useCallback(
    (index: number, event: DragEvent) => {
      event.dataTransfer.effectAllowed = "move";
      event.dataTransfer.setData("text/plain", String(index));
      const group =
        hasGroup && selectedIndices?.has(index)
          ? [...selectedIndices].sort((a, b) => a - b)
          : [index];
      scrollParentRef.current = resolveScrollParent(
        event.currentTarget as Element,
      );
      setDraggedIndices(group);
    },
    [hasGroup, selectedIndices],
  );

  const handleDragEnd = useCallback(() => {
    setDraggedIndices(null);
    setOverIndex(null);
  }, []);

  const handleDragOver = useCallback(
    (index: number, event: DragEvent) => {
      if (!enabled) return;
      event.preventDefault();
      event.dataTransfer.dropEffect = "move";
      if (draggedIndices !== null && !draggedIndices.includes(index)) {
        setOverIndex(index);
      }
    },
    [draggedIndices, enabled],
  );

  const handleDrop = useCallback(
    (index: number, event: DragEvent) => {
      if (!enabled) return;
      event.preventDefault();
      const group = draggedIndices;
      const from =
        group?.[0] ??
        Number.parseInt(event.dataTransfer.getData("text/plain"), 10);
      if (group !== null && group.length > 1) {
        if (!group.includes(index)) {
          const allowed =
            onBeforeGroupDrop == null || onBeforeGroupDrop(group, index);
          if (allowed) {
            onReorder(moveArrayItems(items, group, index));
          }
        }
      } else if (!Number.isNaN(from) && from !== index) {
        onReorder(moveArrayItem(items, from, index));
      }
      setDraggedIndices(null);
      setOverIndex(null);
    },
    [draggedIndices, enabled, items, onBeforeGroupDrop, onReorder],
  );

  // Auto-scroll: enquanto o arraste estiver ativo, um loop de rAF rola o
  // contêiner quando o ponteiro entra na faixa de borda (topo/rodapé).
  const dragging = draggedIndices !== null;
  useEffect(() => {
    if (!dragging) return;
    const trackPointer = (event: Event) => {
      pointerClientYRef.current = (event as { clientY?: number }).clientY ?? null;
    };
    window.addEventListener("dragover", trackPointer, true);
    const step = () => {
      const y = pointerClientYRef.current;
      const el = scrollParentRef.current;
      if (y != null && el) {
        const delta = dragAutoScrollDelta(el, y);
        if (delta !== 0) el.scrollTop += delta;
      }
      rafRef.current = requestAnimationFrame(step);
    };
    rafRef.current = requestAnimationFrame(step);
    return () => {
      window.removeEventListener("dragover", trackPointer, true);
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
      pointerClientYRef.current = null;
      scrollParentRef.current = null;
    };
  }, [dragging]);

  const rowClassName = useCallback(
    (index: number) =>
      [
        draggedIndices?.includes(index) ? "ppc-load__row--dragging" : "",
        overIndex === index &&
        draggedIndices !== null &&
        !draggedIndices.includes(index)
          ? "ppc-load__row--drop-target"
          : "",
      ]
        .filter(Boolean)
        .join(" ") || undefined,
    [draggedIndices, overIndex],
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
      // Com seleção ativa só a linha selecionada inicia o arraste do grupo;
      // fora da seleção a alça fica visualmente desabilitada pela página.
      draggable:
        canDrag && (!hasGroup || Boolean(selectedIndices?.has(index))),
      onDragStart: (event: DragEvent) => handleDragStart(index, event),
      onDragEnd: handleDragEnd,
    }),
    [canDrag, hasGroup, handleDragEnd, handleDragStart, selectedIndices],
  );

  return {
    canDrag,
    draggedIndex: draggedIndices?.[0] ?? null,
    draggedIndices,
    overIndex,
    rowClassName,
    rowDropProps,
    handleProps,
  };
}
