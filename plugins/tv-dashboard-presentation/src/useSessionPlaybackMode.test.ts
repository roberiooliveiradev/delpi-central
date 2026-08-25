import { describe, expect, it, beforeEach, afterEach, vi } from "vitest";
import { act, renderHook } from "@testing-library/react";

import { useSessionPlaybackMode } from "./useSessionPlaybackMode";

describe("useSessionPlaybackMode", () => {
  beforeEach(() => {
    sessionStorage.clear();
    window.history.replaceState({}, "", "/p/tv-dashboard/present/tok");
  });

  afterEach(() => {
    sessionStorage.clear();
    window.history.replaceState({}, "", "/");
  });

  it("usa playlist quando não há sessão nem query", () => {
    const { result } = renderHook(() =>
      useSessionPlaybackMode({ scopeKey: "tok", playlistMode: "meeting" }),
    );
    expect(result.current.playbackMode).toBe("meeting");
    expect(result.current.autoAdvance).toBe(false);
  });

  it("query mode=meeting sobrescreve playlist e grava sessão", () => {
    window.history.replaceState({}, "", "/preview?mode=meeting");
    const { result } = renderHook(() =>
      useSessionPlaybackMode({ scopeKey: "pl1", playlistMode: "presentation" }),
    );
    expect(result.current.playbackMode).toBe("meeting");
    expect(sessionStorage.getItem("delpi-tv-playback-mode:pl1")).toBe("meeting");
  });

  it("setPlaybackMode atualiza sessão e URL", () => {
    const { result } = renderHook(() =>
      useSessionPlaybackMode({ scopeKey: "pl1", playlistMode: "presentation" }),
    );
    act(() => {
      result.current.setPlaybackMode("meeting");
    });
    expect(result.current.playbackMode).toBe("meeting");
    expect(sessionStorage.getItem("delpi-tv-playback-mode:pl1")).toBe("meeting");
    expect(new URL(window.location.href).searchParams.get("mode")).toBe("meeting");
  });

  it("default presentation quando nada informado", () => {
    const { result } = renderHook(() =>
      useSessionPlaybackMode({ scopeKey: "x", playlistMode: null }),
    );
    expect(result.current.playbackMode).toBe("presentation");
    expect(result.current.autoAdvance).toBe(true);
  });
});
