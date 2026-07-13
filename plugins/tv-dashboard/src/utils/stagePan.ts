/**
 * Pan do palco (ferramenta mão): scroll do wrap + gutter para alcançar cantos.
 */

export type StageScrollPoint = { scrollLeft: number; scrollTop: number };

/**
 * Pan tem prioridade sobre arraste/seleção do bloco (ferramenta mão ou Ctrl).
 * O handler do bloco deve retornar sem `stopPropagation` para o wrap capturar.
 */
export function shouldDeferToStagePan(
  event: Pick<PointerEvent | MouseEvent, "ctrlKey">,
  stagePanMode: boolean,
): boolean {
  return stagePanMode || Boolean(event.ctrlKey);
}

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

/** Centraliza o conteúdo scrollável no wrap (só fit explícito / Ajustar). */
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

/**
 * Mantém o mesmo ponto do slide sob o centro da viewport após resize do wrap
 * e/ou mudança do padding de gutter (abas, inspetor, etc.).
 *
 * Âncora = offset do centro da viewport relativo à borda esquerda/topo do slide
 * (scroll + client/2 − gutter). Após o layout: scroll' = âncora + gutter' − client'/2.
 */
export function stageViewAnchorFromScroll(args: {
  scrollLeft: number;
  scrollTop: number;
  clientWidth: number;
  clientHeight: number;
  gutter: { x: number; y: number };
}): { x: number; y: number } {
  return {
    x: args.scrollLeft + args.clientWidth / 2 - args.gutter.x,
    y: args.scrollTop + args.clientHeight / 2 - args.gutter.y,
  };
}

export function stageScrollFromViewAnchor(args: {
  anchorX: number;
  anchorY: number;
  clientWidth: number;
  clientHeight: number;
  gutter: { x: number; y: number };
}): StageScrollPoint {
  return {
    scrollLeft: args.anchorX + args.gutter.x - args.clientWidth / 2,
    scrollTop: args.anchorY + args.gutter.y - args.clientHeight / 2,
  };
}

/** Lê âncora + gutter a partir do wrap (client size atual). */
export function captureStageViewAnchor(wrap: {
  scrollLeft: number;
  scrollTop: number;
  clientWidth: number;
  clientHeight: number;
}): { x: number; y: number } {
  const gutter = resolveStagePanGutterPx(wrap.clientWidth, wrap.clientHeight);
  return stageViewAnchorFromScroll({
    scrollLeft: wrap.scrollLeft,
    scrollTop: wrap.scrollTop,
    clientWidth: wrap.clientWidth,
    clientHeight: wrap.clientHeight,
    gutter,
  });
}

/** Aplica âncora persistida no wrap (após zoom/layout). */
export function applyStageViewAnchor(
  wrap: HTMLElement | null | undefined,
  anchor: { x: number; y: number },
): void {
  if (!wrap) return;
  const gutter = resolveStagePanGutterPx(wrap.clientWidth, wrap.clientHeight);
  const next = stageScrollFromViewAnchor({
    anchorX: anchor.x,
    anchorY: anchor.y,
    clientWidth: wrap.clientWidth,
    clientHeight: wrap.clientHeight,
    gutter,
  });
  wrap.scrollLeft = next.scrollLeft;
  wrap.scrollTop = next.scrollTop;
}

export function stageScrollPreserveContentUnderViewportCenter(args: {
  scrollLeft: number;
  scrollTop: number;
  prevClientWidth: number;
  prevClientHeight: number;
  prevGutter: { x: number; y: number };
  nextClientWidth: number;
  nextClientHeight: number;
  nextGutter: { x: number; y: number };
}): StageScrollPoint {
  const anchor = stageViewAnchorFromScroll({
    scrollLeft: args.scrollLeft,
    scrollTop: args.scrollTop,
    clientWidth: args.prevClientWidth,
    clientHeight: args.prevClientHeight,
    gutter: args.prevGutter,
  });
  return stageScrollFromViewAnchor({
    anchorX: anchor.x,
    anchorY: anchor.y,
    clientWidth: args.nextClientWidth,
    clientHeight: args.nextClientHeight,
    gutter: args.nextGutter,
  });
}
