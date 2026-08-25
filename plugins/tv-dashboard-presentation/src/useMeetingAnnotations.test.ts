import { describe, expect, it, vi } from "vitest";
import { act, renderHook } from "@testing-library/react";

import { useMeetingAnnotations } from "./useMeetingAnnotations";

describe("useMeetingAnnotations", () => {
  it("publica stroke e ignora eco remoto do próprio clientId", () => {
    const send = vi.fn();
    const sendRef = { current: send };
    const { result } = renderHook(() =>
      useMeetingAnnotations({
        enabled: true,
        clientId: "self",
        slideId: "s1",
        sendRef,
      }),
    );

    act(() => {
      result.current.publishStroke({
        strokeId: "st-1",
        phase: "start",
        points: [{ x: 0.1, y: 0.2 }],
      });
    });
    expect(send).toHaveBeenCalledWith(
      expect.objectContaining({ type: "meeting_ink_stroke", clientId: "self" }),
    );
    expect(result.current.strokes).toHaveLength(1);

    act(() => {
      result.current.applyRemoteInk({
        type: "meeting_ink_stroke",
        slideId: "s1",
        clientId: "self",
        strokeId: "st-echo",
        phase: "start",
        points: [{ x: 0.9, y: 0.9 }],
      });
    });
    expect(result.current.strokes).toHaveLength(1);

    act(() => {
      result.current.applyRemoteInk({
        type: "meeting_ink_stroke",
        slideId: "s1",
        clientId: "peer",
        strokeId: "st-2",
        phase: "start",
        points: [{ x: 0.5, y: 0.5 }],
      });
    });
    expect(result.current.strokes).toHaveLength(2);
  });

  it("clear publica meeting_ink_clear e zera strokes do slide", () => {
    const send = vi.fn();
    const sendRef = { current: send };
    const { result } = renderHook(() =>
      useMeetingAnnotations({
        enabled: true,
        clientId: "self",
        slideId: "s1",
        sendRef,
      }),
    );
    act(() => {
      result.current.publishStroke({
        strokeId: "st-1",
        phase: "end",
        points: [{ x: 0.2, y: 0.2 }],
      });
      result.current.clearInk();
    });
    expect(send).toHaveBeenCalledWith({
      type: "meeting_ink_clear",
      clientId: "self",
      slideId: "s1",
    });
    expect(result.current.strokes).toHaveLength(0);
  });

  it("força tool none quando disabled", () => {
    const sendRef = { current: null };
    const { result, rerender } = renderHook(
      ({ enabled }) =>
        useMeetingAnnotations({
          enabled,
          clientId: "self",
          slideId: "s1",
          sendRef,
        }),
      { initialProps: { enabled: true } },
    );
    act(() => result.current.setTool("pen"));
    expect(result.current.tool).toBe("pen");
    rerender({ enabled: false });
    expect(result.current.tool).toBe("none");
  });
});
