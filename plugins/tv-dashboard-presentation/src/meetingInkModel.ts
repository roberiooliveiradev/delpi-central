import type {
  MeetingInkStroke,
  MeetingInkStrokePhase,
  MeetingNormPoint,
} from "./meetingAnnotationTypes";

const MAX_POINTS_PER_STROKE = 500;

function clamp01(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.min(1, Math.max(0, value));
}

export function normalizeMeetingPoint(x: number, y: number): MeetingNormPoint {
  return { x: clamp01(x), y: clamp01(y) };
}

export function applyMeetingInkStrokeEvent(
  strokes: MeetingInkStroke[],
  event: {
    strokeId: string;
    clientId: string;
    slideId: string;
    phase: MeetingInkStrokePhase;
    points: MeetingNormPoint[];
  },
): MeetingInkStroke[] {
  const points = event.points.map((point) => normalizeMeetingPoint(point.x, point.y));
  const idx = strokes.findIndex((stroke) => stroke.strokeId === event.strokeId);
  if (event.phase === "start") {
    const next: MeetingInkStroke = {
      strokeId: event.strokeId,
      clientId: event.clientId,
      slideId: event.slideId,
      points: points.slice(0, MAX_POINTS_PER_STROKE),
      active: true,
    };
    if (idx >= 0) {
      const copy = strokes.slice();
      copy[idx] = next;
      return copy;
    }
    return [...strokes, next];
  }
  if (idx < 0) {
    if (points.length === 0) return strokes;
    return [
      ...strokes,
      {
        strokeId: event.strokeId,
        clientId: event.clientId,
        slideId: event.slideId,
        points: points.slice(0, MAX_POINTS_PER_STROKE),
        active: event.phase !== "end",
      },
    ];
  }
  const current = strokes[idx]!;
  const merged = [...current.points, ...points].slice(0, MAX_POINTS_PER_STROKE);
  const copy = strokes.slice();
  copy[idx] = {
    ...current,
    points: merged,
    active: event.phase !== "end",
  };
  return copy;
}

export function clearMeetingInkForSlide(
  strokes: MeetingInkStroke[],
  slideId: string,
): MeetingInkStroke[] {
  return strokes.filter((stroke) => stroke.slideId !== slideId);
}

export function strokesForSlide(
  strokes: MeetingInkStroke[],
  slideId: string,
): MeetingInkStroke[] {
  return strokes.filter((stroke) => stroke.slideId === slideId);
}

export function meetingPointsToSvgPath(points: MeetingNormPoint[]): string {
  if (points.length === 0) return "";
  const [first, ...rest] = points;
  if (!first) return "";
  let path = `M ${first.x * 100} ${first.y * 100}`;
  for (const point of rest) {
    path += ` L ${point.x * 100} ${point.y * 100}`;
  }
  return path;
}

export function createMeetingStrokeId(clientId: string): string {
  const rand =
    typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
      ? crypto.randomUUID()
      : `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
  return `${clientId}:${rand}`;
}
