import type { RunTimeline } from "../types/mes";

export function liveTimelineSummary(timeline: RunTimeline, serverNowMs: number) {
  const reference = Date.parse(timeline.referenceAt);
  const extra = Number.isFinite(reference) ? Math.max(0, Math.floor((serverNowMs - reference) / 1000)) : 0;
  const open = timeline.items.find((item) => item.endedAt === null);
  return {
    elapsedSeconds: timeline.summary.elapsedSeconds + (open ? extra : 0),
    producingSeconds: timeline.summary.producingSeconds + (open?.state === "producing" ? extra : 0),
    stoppedSeconds: timeline.summary.stoppedSeconds + (open?.state === "stopped" ? extra : 0),
    stopCount: timeline.summary.stopCount,
  };
}
