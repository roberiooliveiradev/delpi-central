import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useDebouncedValue } from "./useDebouncedValue";

afterEach(() => {
  vi.useRealTimers();
});

describe("useDebouncedValue", () => {
  it("entrega o valor inicial imediatamente", () => {
    const { result } = renderHook(() => useDebouncedValue("a", 400));
    expect(result.current).toBe("a");
  });

  it("posterga mudanças e colapsa digitação rápida em uma atualização", () => {
    vi.useFakeTimers();
    let value = "a";
    const { result, rerender } = renderHook(() =>
      useDebouncedValue(value, 400),
    );

    value = "ab";
    rerender();
    act(() => {
      vi.advanceTimersByTime(399);
    });
    expect(result.current).toBe("a");

    value = "abc";
    rerender();
    act(() => {
      vi.advanceTimersByTime(399);
    });
    expect(result.current).toBe("a");

    act(() => {
      vi.advanceTimersByTime(1);
    });
    expect(result.current).toBe("abc");
  });
});
