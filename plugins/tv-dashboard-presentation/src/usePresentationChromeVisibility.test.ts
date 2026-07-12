import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";

import {
  PRESENTATION_CHROME_HIDE_MS,
  usePresentationChromeVisibility,
} from "./usePresentationChromeVisibility";

describe("usePresentationChromeVisibility", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("oculta após inatividade e reaparece com atividade", () => {
    const { result } = renderHook(() => usePresentationChromeVisibility({ hideAfterMs: 1000 }));
    expect(result.current.visible).toBe(true);

    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(result.current.visible).toBe(false);

    act(() => {
      result.current.bump();
    });
    expect(result.current.visible).toBe(true);
  });

  it("usa timeout padrão de chrome", () => {
    expect(PRESENTATION_CHROME_HIDE_MS).toBe(3500);
  });
});
