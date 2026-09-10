export const THREAD_STICK_BOTTOM_PX = 64;

export type ThreadScrollMetrics = {
  scrollTop: number;
  scrollHeight: number;
  clientHeight: number;
};

export function remainingThreadScrollPx(el: ThreadScrollMetrics): number {
  return el.scrollHeight - el.scrollTop - el.clientHeight;
}

/** Auto-scroll only when the user is still near the bottom. */
export function shouldStickThreadToBottom(
  el: ThreadScrollMetrics | null | undefined,
  thresholdPx = THREAD_STICK_BOTTOM_PX,
): boolean {
  if (!el) return true;
  return remainingThreadScrollPx(el) <= thresholdPx;
}
