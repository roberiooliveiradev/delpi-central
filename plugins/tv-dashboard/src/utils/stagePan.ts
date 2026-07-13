/**
 * Pan do palco (ferramenta mão): scroll do wrap + gutter para alcançar cantos.
 */

export type StageScrollPoint = { scrollLeft: number; scrollTop: number };

/**
 * Delta de scroll do pan (arrastar o palco): movimento do ponteiro inverte no scroll.
 */
export function applyStagePanScrollDelta(
  scroll: StageScrollPoint,
  dx: number,
  dy: number,
): StageScrollPoint {
  return {
    scrollLeft: scroll.scrollLeft - dx,
    scrollTop: scroll.scrollTop - dy,
  };
}

/**
 * Após mudar o zoom, mantém o ponto sob o cursor (coords do wrap).
 * `contentX/Y` = scroll + offset do ponteiro no zoom anterior; `ratio = next/prev`.
 */
export function stageScrollAfterZoomTowardPoint(args: {
  prevZoom: number;
  nextZoom: number;
  scrollLeft: number;
  scrollTop: number;
  pointerOffsetX: number;
  pointerOffsetY: number;
}): StageScrollPoint {
  const { prevZoom, nextZoom, scrollLeft, scrollTop, pointerOffsetX, pointerOffsetY } = args;
  if (!(prevZoom > 0) || !(nextZoom > 0) || prevZoom === nextZoom) {
    return { scrollLeft, scrollTop };
  }
  const ratio = nextZoom / prevZoom;
  const contentX = scrollLeft + pointerOffsetX;
  const contentY = scrollTop + pointerOffsetY;
  return {
    scrollLeft: contentX * ratio - pointerOffsetX,
    scrollTop: contentY * ratio - pointerOffsetY,
  };
}

/**
 * Gutter (px) em cada lado para o pan levar qualquer canto do slide
 * até a área útil do painel (metade da viewport, mínimo 48px).
 */
export function resolveStagePanGutterPx(
  wrapClientWidth: number,
  wrapClientHeight: number,
): { x: number; y: number } {
  const min = 48;
  return {
    x: Math.max(min, Math.round(Math.max(0, wrapClientWidth) / 2)),
    y: Math.max(min, Math.round(Math.max(0, wrapClientHeight) / 2)),
  };
}

/** Centraliza o conteúdo scrollável no wrap (após fit / mudança de gutter). */
export function centerStageScroll(wrap: {
  scrollWidth: number;
  scrollHeight: number;
  clientWidth: number;
  clientHeight: number;
}): StageScrollPoint {
  return {
    scrollLeft: Math.max(0, (wrap.scrollWidth - wrap.clientWidth) / 2),
    scrollTop: Math.max(0, (wrap.scrollHeight - wrap.clientHeight) / 2),
  };
}

/** Aplica scroll centralizado no elemento (no-op se inválido). */
export function applyCenteredStageScroll(wrap: HTMLElement | null | undefined): void {
  if (!wrap) return;
  const next = centerStageScroll(wrap);
  wrap.scrollLeft = next.scrollLeft;
  wrap.scrollTop = next.scrollTop;
}
