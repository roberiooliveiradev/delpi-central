import { describe, expect, it, vi } from "vitest";

import { observeElementOnce } from "./useLazyBillingSeriesActivation";

describe("observeElementOnce", () => {
  it("ativa somente na primeira entrada no viewport e desconecta", () => {
    const activate = vi.fn();
    const disconnect = vi.fn();
    let emit: ((entries: readonly { isIntersecting: boolean }[]) => void) | undefined;
    const observe = vi.fn();
    const target = {} as Element;

    const cleanup = observeElementOnce(target, activate, (callback) => {
      emit = callback;
      return { observe, disconnect };
    });

    expect(observe).toHaveBeenCalledWith(target);
    emit?.([{ isIntersecting: false }]);
    expect(activate).not.toHaveBeenCalled();
    emit?.([{ isIntersecting: true }]);
    emit?.([{ isIntersecting: true }]);
    expect(activate).toHaveBeenCalledTimes(1);
    expect(disconnect).toHaveBeenCalled();
    cleanup();
  });

  it("ativa imediatamente como fallback sem IntersectionObserver", () => {
    const original = globalThis.IntersectionObserver;
    const activate = vi.fn();
    vi.stubGlobal("IntersectionObserver", undefined);
    try {
      observeElementOnce({} as Element, activate);
      expect(activate).toHaveBeenCalledTimes(1);
    } finally {
      vi.stubGlobal("IntersectionObserver", original);
    }
  });
});
