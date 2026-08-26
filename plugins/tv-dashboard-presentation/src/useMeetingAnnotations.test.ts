import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import { act, renderHook } from "@testing-library/react";

import { useMeetingAnnotations } from "./useMeetingAnnotations";

describe("useMeetingAnnotations", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

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

  it("preserva strokes ao mudar slideId (ink por slide)", () => {
    const sendRef = { current: vi.fn() };
    const { result, rerender } = renderHook(
      ({ slideId }) =>
        useMeetingAnnotations({
          enabled: true,
          clientId: "self",
          slideId,
          sendRef,
        }),
      { initialProps: { slideId: "s1" } },
    );

    act(() => {
      result.current.publishStroke({
        strokeId: "st-a",
        phase: "end",
        points: [{ x: 0.1, y: 0.1 }],
      });
    });
    expect(result.current.strokes).toHaveLength(1);
    expect(result.current.strokes[0]?.slideId).toBe("s1");

    rerender({ slideId: "s2" });
    expect(result.current.strokes).toHaveLength(1);

    act(() => {
      result.current.publishStroke({
        strokeId: "st-b",
        phase: "end",
        points: [{ x: 0.5, y: 0.5 }],
      });
    });
    expect(result.current.strokes).toHaveLength(2);

    rerender({ slideId: "s1" });
    expect(result.current.strokes.filter((s) => s.slideId === "s1")).toHaveLength(1);
  });

  it("clearInk só remove strokes do slide atual", () => {
    const sendRef = { current: vi.fn() };
    const { result, rerender } = renderHook(
      ({ slideId }) =>
        useMeetingAnnotations({
          enabled: true,
          clientId: "self",
          slideId,
          sendRef,
        }),
      { initialProps: { slideId: "s1" } },
    );

    act(() => {
      result.current.publishStroke({
        strokeId: "st-s1",
        phase: "end",
        points: [{ x: 0.1, y: 0.1 }],
      });
    });
    rerender({ slideId: "s2" });
    act(() => {
      result.current.publishStroke({
        strokeId: "st-s2",
        phase: "end",
        points: [{ x: 0.2, y: 0.2 }],
      });
    });
    expect(result.current.strokes).toHaveLength(2);

    act(() => result.current.clearInk());
    expect(result.current.strokes).toHaveLength(1);
    expect(result.current.strokes[0]?.slideId).toBe("s1");
  });

  it("publishLaserNetwork envia WS sem alterar strokes", () => {
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
      result.current.publishLaserNetwork({ x: 0.3, y: 0.4, visible: true });
      result.current.publishLaserNetwork({ x: 0.31, y: 0.41, visible: true });
    });
    expect(send).toHaveBeenCalledTimes(2);
    expect(send).toHaveBeenCalledWith(
      expect.objectContaining({
        type: "meeting_laser",
        clientId: "self",
        slideId: "s1",
        visible: true,
      }),
    );
    expect(result.current.strokes).toHaveLength(0);
  });

  it("applyRemoteLaser delega ao overlayRef sem setState", () => {
    const paintRemoteLaser = vi.fn();
    const sendRef = { current: null };
    const { result } = renderHook(() =>
      useMeetingAnnotations({
        enabled: true,
        clientId: "self",
        slideId: "s1",
        sendRef,
      }),
    );
    result.current.overlayRef.current = { paintRemoteLaser, clearLasersForSlide: vi.fn() };

    act(() => {
      result.current.applyRemoteLaser({
        type: "meeting_laser",
        clientId: "peer",
        slideId: "s1",
        x: 0.5,
        y: 0.5,
        visible: true,
      });
    });
    expect(paintRemoteLaser).toHaveBeenCalledWith(
      expect.objectContaining({ clientId: "peer", visible: true }),
    );
    expect(result.current.strokes).toHaveLength(0);
  });
});
