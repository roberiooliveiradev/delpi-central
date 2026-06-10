const tourTimerIds = new Set<number>();

export function schedulePortalTourTimer(callback: () => void, delayMs: number) {
  const timerId = window.setTimeout(() => {
    tourTimerIds.delete(timerId);
    callback();
  }, delayMs);
  tourTimerIds.add(timerId);
  return timerId;
}

export function clearPortalTourTimers() {
  tourTimerIds.forEach((timerId) => window.clearTimeout(timerId));
  tourTimerIds.clear();
}
