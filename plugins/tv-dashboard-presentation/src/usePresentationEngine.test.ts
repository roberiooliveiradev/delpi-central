import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";

import { usePresentationEngine } from "./usePresentationEngine";
import type { PresentationPayloadLike } from "./types";

const payload: PresentationPayloadLike = {
  playlist: {
    id: "p1",
    name: "Test",
    viewportProfile: "1080p",
    transitionStyle: "fade",
    globalRefreshSec: 300,
    defaultDurationSec: 2,
  },
  slides: [
    {
      id: "s1",
      sortOrder: 0,
      slideType: "native",
      durationSec: 2,
      title: "A",
      native: { screenKey: "custom_message", config: {}, data: { headline: "A" } },
    },
    {
      id: "s2",
      sortOrder: 1,
      slideType: "external",
      durationSec: 2,
      title: "B",
      external: { url: "https://example.com", sandbox: null },
    },
  ],
};

describe("usePresentationEngine", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("avances slides after duration", () => {
    const { result } = renderHook(() =>
      usePresentationEngine({ initialPayload: payload, enableHiddenPause: false }),
    );
    expect(result.current.index).toBe(0);
    act(() => {
      vi.advanceTimersByTime(2100);
    });
    expect(result.current.index).toBe(1);
  });

  it("loops back to first slide", () => {
    const { result } = renderHook(() =>
      usePresentationEngine({ initialPayload: payload, enableHiddenPause: false }),
    );
    act(() => {
      vi.advanceTimersByTime(2100);
    });
    expect(result.current.index).toBe(1);
    act(() => {
      vi.advanceTimersByTime(2100);
    });
    expect(result.current.index).toBe(0);
  });

  it("resolves transition from current slide override", () => {
    const withOverride: PresentationPayloadLike = {
      ...payload,
      slides: [
        { ...payload.slides[0], transitionStyle: "slide" },
        payload.slides[1],
      ],
    };
    const { result } = renderHook(() =>
      usePresentationEngine({ initialPayload: withOverride, enableHiddenPause: false }),
    );
    expect(result.current.transition).toBe("slide");
    act(() => {
      result.current.setIndex(1);
    });
    expect(result.current.transition).toBe("fade");
  });

  it("does not refresh when current slide is external and refreshNativeSlidesOnly", () => {
    const onRefresh = vi.fn().mockResolvedValue(payload);
    const { result } = renderHook(() =>
      usePresentationEngine({
        initialPayload: payload,
        onRefresh,
        enableHiddenPause: false,
        refreshNativeSlidesOnly: true,
      }),
    );
    act(() => {
      result.current.setIndex(1);
    });
    act(() => {
      vi.advanceTimersByTime(300_000);
    });
    expect(onRefresh).not.toHaveBeenCalled();
  });
});
