export type DragEdgeScrollOptions = {
  /** Zona sensível no topo/fundo do container (px). */
  edgePx?: number;
  /** Passo máximo de scroll por chamada (px). */
  maxStepPx?: number;
};

/**
 * Se `clientY` está na faixa superior/inferior do container com overflow,
 * ajusta `scrollTop` proporcionalmente à proximidade da borda.
 * @returns delta aplicado em px (0 se nada scrollou).
 */
export function scrollContainerOnDragEdge(
  container: HTMLElement,
  clientY: number,
  options: DragEdgeScrollOptions = {},
): number {
  const edgePx = options.edgePx ?? 40;
  const maxStepPx = options.maxStepPx ?? 18;
  if (!(edgePx > 0) || !(maxStepPx > 0) || !Number.isFinite(clientY)) return 0;

  const maxScroll = container.scrollHeight - container.clientHeight;
  if (!(maxScroll > 0)) return 0;

  const rect = container.getBoundingClientRect();
  if (!(rect.height > 0)) return 0;

  const topDist = clientY - rect.top;
  const bottomDist = rect.bottom - clientY;
  let delta = 0;

  if (topDist < edgePx) {
    const intensity = 1 - Math.max(0, topDist) / edgePx;
    delta = -Math.ceil(maxStepPx * intensity);
  } else if (bottomDist < edgePx) {
    const intensity = 1 - Math.max(0, bottomDist) / edgePx;
    delta = Math.ceil(maxStepPx * intensity);
  }

  if (delta === 0) return 0;

  const prev = container.scrollTop;
  container.scrollTop = Math.max(0, Math.min(maxScroll, prev + delta));
  return container.scrollTop - prev;
}
