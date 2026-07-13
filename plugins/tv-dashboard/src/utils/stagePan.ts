/**
 * Delta de scroll do pan (arrastar o palco): movimento do ponteiro inverte no scroll.
 */
export function applyStagePanScrollDelta(
  scroll: { scrollLeft: number; scrollTop: number },
  dx: number,
  dy: number,
): { scrollLeft: number; scrollTop: number } {
  return {
    scrollLeft: scroll.scrollLeft - dx,
    scrollTop: scroll.scrollTop - dy,
  };
}
