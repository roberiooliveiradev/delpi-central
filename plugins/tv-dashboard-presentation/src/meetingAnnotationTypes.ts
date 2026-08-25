export type MeetingAnnotationTool = "none" | "pen" | "laser";

export type MeetingNormPoint = { x: number; y: number };

export type MeetingInkStroke = {
  strokeId: string;
  clientId: string;
  slideId: string;
  points: MeetingNormPoint[];
  /** Stroke ainda sendo desenhado (local ou remoto). */
  active?: boolean;
};

export type MeetingLaserState = {
  clientId: string;
  slideId: string;
  x: number;
  y: number;
  visible: boolean;
};

export type MeetingInkStrokePhase = "start" | "move" | "end";

/** Cor accent única (P0) — vermelho estilo PowerPoint. */
export const MEETING_INK_COLOR = "#ef4444";
/** Núcleo do apontador laser (mesmo vermelho da caneta). */
export const MEETING_LASER_COLOR = "#ff1a1a";
export const MEETING_INK_WIDTH_PX = 3.5;
