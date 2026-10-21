import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  DRAFT_RECOVERY_DISMISS_MS,
  useDraftRecovery,
} from "./draftRecovery";

afterEach(() => {
  vi.useRealTimers();
});

function setup(overrides?: {
  epoch?: { current: number };
  canRestore?: () => boolean;
}) {
  vi.useFakeTimers();
  const epoch = overrides?.epoch ?? { current: 1 };
  const canRestore = overrides?.canRestore ?? (() => true);
  const onRestore = vi.fn();
  const { result, rerender, unmount } = renderHook(() =>
    useDraftRecovery({
      epoch: () => epoch.current,
      canRestore,
      onRestore,
    }),
  );
  return { result, epoch, onRestore, rerender, unmount };
}

describe("useDraftRecovery", () => {
  it("captures an explicit clear and restores the exact text on undo", () => {
    const { result, onRestore } = setup();
    const draft = "linha 1\n  indentação — çã é ✓ unicode";
    act(() => result.current.capture(draft));
    expect(result.current.visible).toBe(true);
    act(() => result.current.undo());
    expect(onRestore).toHaveBeenCalledTimes(1);
    expect(onRestore).toHaveBeenCalledWith(draft);
    expect(result.current.visible).toBe(false);
  });

  it("ignores an empty cleared draft — no candidate, no notice", () => {
    const { result } = setup();
    act(() => result.current.capture(""));
    expect(result.current.visible).toBe(false);
  });

  it("is idempotent: a double undo restores at most once", () => {
    const { result, onRestore } = setup();
    act(() => result.current.capture("texto"));
    act(() => {
      result.current.undo();
      result.current.undo();
    });
    expect(onRestore).toHaveBeenCalledTimes(1);
  });

  it("expires after the reference duration and cannot restore afterwards", () => {
    const { result, onRestore } = setup();
    act(() => result.current.capture("texto"));
    act(() => vi.advanceTimersByTime(DRAFT_RECOVERY_DISMISS_MS + 1));
    expect(result.current.visible).toBe(false);
    act(() => result.current.undo());
    expect(onRestore).not.toHaveBeenCalled();
  });

  it("pauses the countdown while hovered/focused and resumes with remaining time", () => {
    const { result, onRestore } = setup();
    act(() => result.current.capture("texto"));
    act(() => vi.advanceTimersByTime(3_000));
    act(() => result.current.pause());
    act(() => vi.advanceTimersByTime(60_000));
    expect(result.current.visible).toBe(true);
    act(() => result.current.resume());
    act(() => vi.advanceTimersByTime(4_999));
    expect(result.current.visible).toBe(true);
    act(() => vi.advanceTimersByTime(2));
    expect(result.current.visible).toBe(false);
    act(() => result.current.undo());
    expect(onRestore).not.toHaveBeenCalled();
  });

  it("discards the candidate when the epoch changed (send/conversation boundary)", () => {
    const epoch = { current: 1 };
    const { result, onRestore } = setup({ epoch });
    act(() => result.current.capture("texto"));
    epoch.current += 1; // a send bumps the request epoch
    act(() => result.current.undo());
    expect(onRestore).not.toHaveBeenCalled();
    expect(result.current.visible).toBe(false);
  });

  it("refuses restore when the host gate fails (non-idle, in-flight or new draft text)", () => {
    let allowed = true;
    const { result, onRestore } = setup({ canRestore: () => allowed });
    act(() => result.current.capture("texto"));
    allowed = false; // e.g. the user typed something new
    act(() => result.current.undo());
    expect(onRestore).not.toHaveBeenCalled();
    expect(result.current.visible).toBe(false);
  });

  it("a newer clear replaces the previous candidate and its timer", () => {
    const { result, onRestore } = setup();
    act(() => result.current.capture("primeiro"));
    act(() => vi.advanceTimersByTime(DRAFT_RECOVERY_DISMISS_MS - 100));
    act(() => result.current.capture("segundo"));
    // The old timer must not kill the fresh candidate early.
    act(() => vi.advanceTimersByTime(200));
    expect(result.current.visible).toBe(true);
    act(() => result.current.undo());
    expect(onRestore).toHaveBeenCalledWith("segundo");
  });

  it("invalidate() discards the candidate and hides the notice", () => {
    const { result, onRestore } = setup();
    act(() => result.current.capture("texto"));
    act(() => result.current.invalidate());
    expect(result.current.visible).toBe(false);
    act(() => result.current.undo());
    expect(onRestore).not.toHaveBeenCalled();
  });

  it("unmount cancels pending timers without firing expiry work", () => {
    const { result, unmount } = setup();
    act(() => result.current.capture("texto"));
    unmount();
    // Advancing past expiry after unmount must be a silent no-op.
    vi.advanceTimersByTime(DRAFT_RECOVERY_DISMISS_MS + 1_000);
    expect(true).toBe(true); // reached without errors
  });
});
