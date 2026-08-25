import { describe, expect, it } from "vitest";

import {
  applyMeetingInkStrokeEvent,
  clearMeetingInkForSlide,
  meetingPointsToSvgPath,
  normalizeMeetingPoint,
  strokesForSlide,
} from "./meetingInkModel";

describe("meetingInkModel", () => {
  it("normaliza coords 0–1", () => {
    expect(normalizeMeetingPoint(-1, 2)).toEqual({ x: 0, y: 1 });
    expect(normalizeMeetingPoint(0.25, 0.75)).toEqual({ x: 0.25, y: 0.75 });
  });

  it("append start/move/end e clear por slide", () => {
    let strokes = applyMeetingInkStrokeEvent([], {
      strokeId: "st-1",
      clientId: "a",
      slideId: "s1",
      phase: "start",
      points: [{ x: 0.1, y: 0.1 }],
    });
    strokes = applyMeetingInkStrokeEvent(strokes, {
      strokeId: "st-1",
      clientId: "a",
      slideId: "s1",
      phase: "move",
      points: [{ x: 0.2, y: 0.2 }],
    });
    strokes = applyMeetingInkStrokeEvent(strokes, {
      strokeId: "st-1",
      clientId: "a",
      slideId: "s1",
      phase: "end",
      points: [{ x: 0.3, y: 0.3 }],
    });
    expect(strokes[0]?.points).toHaveLength(3);
    expect(strokes[0]?.active).toBe(false);

    strokes = applyMeetingInkStrokeEvent(strokes, {
      strokeId: "st-2",
      clientId: "b",
      slideId: "s2",
      phase: "start",
      points: [{ x: 0.5, y: 0.5 }],
    });
    expect(strokesForSlide(strokes, "s1")).toHaveLength(1);
    expect(clearMeetingInkForSlide(strokes, "s1")).toHaveLength(1);
  });

  it("monta path SVG em viewBox 0–100", () => {
    expect(meetingPointsToSvgPath([{ x: 0, y: 0 }, { x: 1, y: 0.5 }])).toBe(
      "M 0 0 L 100 50",
    );
  });
});
