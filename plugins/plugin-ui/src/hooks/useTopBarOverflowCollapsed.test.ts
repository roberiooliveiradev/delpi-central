import { act, cleanup, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { RefObject } from "react";

import {
  TOPBAR_OVERFLOW_EXPAND_HYSTERESIS_PX,
  useTopBarOverflowCollapsed,
} from "./useTopBarOverflowCollapsed";

afterEach(cleanup);

describe("useTopBarOverflowCollapsed", () => {
  let observe: ReturnType<typeof vi.fn>;
  let disconnect: ReturnType<typeof vi.fn>;
  let callback: ResizeObserverCallback | null = null;

  beforeEach(() => {
    observe = vi.fn();
    disconnect = vi.fn();
    callback = null;
    vi.stubGlobal(
      "ResizeObserver",
      vi.fn(function ResizeObserverStub(this: ResizeObserver, cb: ResizeObserverCallback) {
        callback = cb;
        this.observe = observe;
        this.disconnect = disconnect;
        this.unobserve = vi.fn();
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  function createMeasureHost(needed: number, available: number) {
    const host = document.createElement("div");
    Object.defineProperty(host, "clientWidth", {
      value: available,
      configurable: true,
      writable: true,
    });
    document.body.appendChild(host);

    const measure = document.createElement("div");
    Object.defineProperty(measure, "scrollWidth", {
      value: needed,
      configurable: true,
      writable: true,
    });
    host.appendChild(measure);

    return {
      measureRef: { current: measure } as RefObject<HTMLDivElement>,
      host,
      measure,
      setAvailable: (next: number) => {
        Object.defineProperty(host, "clientWidth", {
          value: next,
          configurable: true,
        });
      },
      setNeeded: (next: number) => {
        Object.defineProperty(measure, "scrollWidth", {
          value: next,
          configurable: true,
        });
      },
    };
  }

  it("colapsa quando conteúdo medido excede a largura do host", () => {
    const { measureRef } = createMeasureHost(520, 400);
    const { result } = renderHook(() =>
      useTopBarOverflowCollapsed(measureRef, { enabled: true }),
    );
    act(() => {
      callback?.([], {} as ResizeObserver);
    });
    expect(result.current.collapsed).toBe(true);
    expect(observe).toHaveBeenCalled();
  });

  it("permanece expandido quando cabe no host", () => {
    const { measureRef } = createMeasureHost(520, 600);
    const { result } = renderHook(() =>
      useTopBarOverflowCollapsed(measureRef, { enabled: true }),
    );
    act(() => {
      callback?.([], {} as ResizeObserver);
    });
    expect(result.current.collapsed).toBe(false);
  });

  it("desliga quando enabled=false", () => {
    const { measureRef } = createMeasureHost(520, 400);
    const { result } = renderHook(() =>
      useTopBarOverflowCollapsed(measureRef, { enabled: false }),
    );
    expect(result.current.collapsed).toBe(false);
    expect(observe).not.toHaveBeenCalled();
  });

  it("não reexpande com folga menor que a histerese", () => {
    const host = createMeasureHost(520, 400);
    const { result } = renderHook(() =>
      useTopBarOverflowCollapsed(host.measureRef, { enabled: true }),
    );
    act(() => {
      callback?.([], {} as ResizeObserver);
    });
    expect(result.current.collapsed).toBe(true);

    // Folga de 10px (< 24): still collapsed
    host.setAvailable(530);
    host.setNeeded(520);
    act(() => {
      callback?.([], {} as ResizeObserver);
    });
    expect(result.current.collapsed).toBe(true);
    expect(TOPBAR_OVERFLOW_EXPAND_HYSTERESIS_PX).toBe(24);
  });

  it("reexpande quando a folga é ≥ histerese", () => {
    const host = createMeasureHost(520, 400);
    const { result } = renderHook(() =>
      useTopBarOverflowCollapsed(host.measureRef, { enabled: true }),
    );
    act(() => {
      callback?.([], {} as ResizeObserver);
    });
    expect(result.current.collapsed).toBe(true);

    // Folga de 30px (≥ 24): expand
    host.setAvailable(550);
    host.setNeeded(520);
    act(() => {
      callback?.([], {} as ResizeObserver);
    });
    expect(result.current.collapsed).toBe(false);
  });
});
