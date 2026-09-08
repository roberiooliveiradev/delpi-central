import { act, cleanup, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { RefObject } from "react";

import {
  TOPBAR_OVERFLOW_EXPAND_HYSTERESIS_PX,
  resolveTopBarMeasureNeededWidth,
  shouldKeepTopBarOverflowCollapsed,
  useTopBarOverflowCollapsed,
} from "./useTopBarOverflowCollapsed";

afterEach(cleanup);

describe("resolveTopBarMeasureNeededWidth", () => {
  it("usa a largura intrínseca da row filha, não o scrollWidth do wrapper 100%", () => {
    const measure = document.createElement("div");
    Object.defineProperty(measure, "scrollWidth", {
      value: 1200,
      configurable: true,
    });
    const row = document.createElement("div");
    Object.defineProperty(row, "scrollWidth", {
      value: 520,
      configurable: true,
    });
    Object.defineProperty(row, "offsetWidth", {
      value: 520,
      configurable: true,
    });
    measure.appendChild(row);

    expect(resolveTopBarMeasureNeededWidth(measure)).toBe(520);
  });

  it("cai no scrollWidth do wrapper quando não há filho", () => {
    const measure = document.createElement("div");
    Object.defineProperty(measure, "scrollWidth", {
      value: 640,
      configurable: true,
    });
    expect(resolveTopBarMeasureNeededWidth(measure)).toBe(640);
  });
});

describe("shouldKeepTopBarOverflowCollapsed", () => {
  it("colapsa com overflow e reexpande com folga ≥ histerese", () => {
    expect(
      shouldKeepTopBarOverflowCollapsed({
        needed: 520,
        available: 400,
        previouslyCollapsed: false,
      }),
    ).toBe(true);
    expect(
      shouldKeepTopBarOverflowCollapsed({
        needed: 520,
        available: 530,
        previouslyCollapsed: true,
      }),
    ).toBe(true);
    expect(
      shouldKeepTopBarOverflowCollapsed({
        needed: 520,
        available: 550,
        previouslyCollapsed: true,
      }),
    ).toBe(false);
  });
});

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

  /**
   * Espelha o DOM real: wrapper measure (width 100%) + row max-content.
   * Quando cabe, scrollWidth do wrapper ≈ available; a row mantém needed.
   */
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
      value: available,
      configurable: true,
      writable: true,
    });
    host.appendChild(measure);

    const row = document.createElement("div");
    Object.defineProperty(row, "scrollWidth", {
      value: needed,
      configurable: true,
      writable: true,
    });
    Object.defineProperty(row, "offsetWidth", {
      value: needed,
      configurable: true,
      writable: true,
    });
    measure.appendChild(row);

    return {
      measureRef: { current: measure } as RefObject<HTMLDivElement>,
      host,
      measure,
      row,
      setAvailable: (next: number) => {
        Object.defineProperty(host, "clientWidth", {
          value: next,
          configurable: true,
        });
        // Wrapper 100%: scrollWidth acompanha o host quando o conteúdo cabe.
        Object.defineProperty(measure, "scrollWidth", {
          value: Math.max(next, needed),
          configurable: true,
        });
      },
      setNeeded: (next: number) => {
        Object.defineProperty(row, "scrollWidth", {
          value: next,
          configurable: true,
        });
        Object.defineProperty(row, "offsetWidth", {
          value: next,
          configurable: true,
        });
        Object.defineProperty(measure, "scrollWidth", {
          value: Math.max(host.clientWidth, next),
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

    host.setAvailable(550);
    host.setNeeded(520);
    act(() => {
      callback?.([], {} as ResizeObserver);
    });
    expect(result.current.collapsed).toBe(false);
  });

  it("reexpande com host largo mesmo se scrollWidth do wrapper ≈ available", () => {
    const fixture = createMeasureHost(520, 400);
    const { result } = renderHook(() =>
      useTopBarOverflowCollapsed(fixture.measureRef, { enabled: true }),
    );
    act(() => {
      callback?.([], {} as ResizeObserver);
    });
    expect(result.current.collapsed).toBe(true);

    // Caso real pós-colapso: wrapper reporta ~1200, conteúdo intrínseco 520.
    fixture.setAvailable(1200);
    Object.defineProperty(fixture.measure, "scrollWidth", {
      value: 1200,
      configurable: true,
    });
    Object.defineProperty(fixture.row, "scrollWidth", {
      value: 520,
      configurable: true,
    });
    Object.defineProperty(fixture.row, "offsetWidth", {
      value: 520,
      configurable: true,
    });
    act(() => {
      callback?.([], {} as ResizeObserver);
    });
    expect(result.current.collapsed).toBe(false);
  });
});
