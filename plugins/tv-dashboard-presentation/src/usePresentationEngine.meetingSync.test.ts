import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";

import type { PresentationPayloadLike } from "./types";

const sent: Record<string, unknown>[] = [];
let cursorHandler: ((event: {
  type: "playback_cursor";
  slideId: string;
  clientId: string;
  index?: number | null;
}) => void) | undefined;

vi.mock("./usePresentationRealtime", async () => {
  const actual = await vi.importActual<typeof import("./usePresentationRealtime")>(
    "./usePresentationRealtime",
  );
  return {
    ...actual,
    usePresentationRealtime: (options: {
      sendRef?: { current: ((payload: Record<string, unknown>) => void) | null };
      onPlaybackCursor?: typeof cursorHandler;
    }) => {
      cursorHandler = options.onPlaybackCursor;
      if (options.sendRef) {
        options.sendRef.current = (payload) => {
          sent.push(payload);
        };
      }
    },
  };
});

import { usePresentationEngine } from "./usePresentationEngine";

const payload: PresentationPayloadLike = {
  playlist: {
    id: "p1",
    name: "Test",
    viewportProfile: "1080p",
    transitionStyle: "fade",
    globalRefreshSec: 300,
    defaultDurationSec: 30,
  },
  slides: [
    {
      id: "s1",
      sortOrder: 0,
      slideType: "native",
      durationSec: 30,
      title: "A",
      native: { screenKey: "custom_message", config: {}, data: {} },
    },
    {
      id: "s2",
      sortOrder: 1,
      slideType: "native",
      durationSec: 30,
      title: "B",
      native: { screenKey: "custom_message", config: {}, data: {} },
    },
  ],
};

describe("usePresentationEngine meeting sync", () => {
  beforeEach(() => {
    sent.length = 0;
    cursorHandler = undefined;
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("publica playback_cursor no goNext quando sync ligado", () => {
    const { result } = renderHook(() =>
      usePresentationEngine({
        initialPayload: payload,
        enableHiddenPause: false,
        autoAdvance: false,
        realtimeWsUrl: "ws://test",
        syncPlaybackCursor: true,
        playbackClientId: "self-1",
      }),
    );
    act(() => {
      result.current.goNext();
    });
    expect(result.current.index).toBe(1);
    expect(sent).toHaveLength(1);
    expect(sent[0]).toMatchObject({
      type: "playback_cursor",
      clientId: "self-1",
      slideId: "s2",
      index: 1,
    });
  });

  it("aplica cursor remoto e ignora eco do próprio clientId", () => {
    const { result } = renderHook(() =>
      usePresentationEngine({
        initialPayload: payload,
        enableHiddenPause: false,
        autoAdvance: false,
        realtimeWsUrl: "ws://test",
        syncPlaybackCursor: true,
        playbackClientId: "self-1",
      }),
    );
    act(() => {
      cursorHandler?.({
        type: "playback_cursor",
        slideId: "s2",
        clientId: "other",
        index: 1,
      });
    });
    expect(result.current.index).toBe(1);
    const before = sent.length;
    act(() => {
      cursorHandler?.({
        type: "playback_cursor",
        slideId: "s1",
        clientId: "self-1",
        index: 0,
      });
    });
    expect(result.current.index).toBe(1);
    expect(sent.length).toBe(before);
  });

  it("não publica quando sync desligado (modo presentation)", () => {
    const { result } = renderHook(() =>
      usePresentationEngine({
        initialPayload: payload,
        enableHiddenPause: false,
        autoAdvance: false,
        realtimeWsUrl: "ws://test",
        syncPlaybackCursor: false,
        playbackClientId: "self-1",
      }),
    );
    act(() => {
      result.current.goNext();
    });
    expect(result.current.index).toBe(1);
    expect(sent).toHaveLength(0);
  });
});
