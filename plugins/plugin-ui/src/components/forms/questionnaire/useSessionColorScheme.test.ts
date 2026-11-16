import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useSessionColorScheme } from "./useSessionColorScheme";

type MediaChangeListener = (event: { matches: boolean }) => void;

const originalMatchMedia = window.matchMedia;

function installMatchMedia(initialDark: boolean) {
  const listeners = new Set<MediaChangeListener>();
  const mql = {
    matches: initialDark,
    media: "(prefers-color-scheme: dark)",
    onchange: null,
    addEventListener: (_type: string, cb: MediaChangeListener) => {
      listeners.add(cb);
    },
    removeEventListener: (_type: string, cb: MediaChangeListener) => {
      listeners.delete(cb);
    },
    addListener: (cb: MediaChangeListener) => {
      listeners.add(cb);
    },
    removeListener: (cb: MediaChangeListener) => {
      listeners.delete(cb);
    },
    dispatchEvent: () => true,
  };
  Object.defineProperty(window, "matchMedia", {
    configurable: true,
    writable: true,
    value: vi.fn(() => mql),
  });
  return {
    emitDeviceChange(matches: boolean) {
      mql.matches = matches;
      act(() => {
        listeners.forEach((cb) => cb({ matches }));
      });
    },
  };
}

function removeMatchMedia() {
  Object.defineProperty(window, "matchMedia", {
    configurable: true,
    writable: true,
    value: undefined,
  });
}

afterEach(() => {
  Object.defineProperty(window, "matchMedia", {
    configurable: true,
    writable: true,
    value: originalMatchMedia,
  });
});

describe("useSessionColorScheme", () => {
  it("inicia em dark quando o aparelho está em modo escuro", () => {
    installMatchMedia(true);
    const { result } = renderHook(() => useSessionColorScheme());
    expect(result.current.scheme).toBe("dark");
    expect(result.current.userChosen).toBe(false);
  });

  it("inicia em light quando o aparelho está em modo claro", () => {
    installMatchMedia(false);
    const { result } = renderHook(() => useSessionColorScheme());
    expect(result.current.scheme).toBe("light");
  });

  it("inicia em light quando matchMedia não existe", () => {
    removeMatchMedia();
    const { result } = renderHook(() => useSessionColorScheme());
    expect(result.current.scheme).toBe("light");
  });

  it("toggle() alterna o tema sem ler nem gravar storage", () => {
    installMatchMedia(false);
    const spies = [
      vi.spyOn(Storage.prototype, "getItem"),
      vi.spyOn(Storage.prototype, "setItem"),
      vi.spyOn(Storage.prototype, "removeItem"),
    ];

    const { result } = renderHook(() => useSessionColorScheme());
    act(() => result.current.toggle());

    expect(result.current.scheme).toBe("dark");
    expect(result.current.userChosen).toBe(true);
    spies.forEach((spy) => expect(spy).not.toHaveBeenCalled());
  });

  it("segue a mudança do aparelho até o primeiro toggle(); depois ignora", () => {
    const device = installMatchMedia(false);
    const { result } = renderHook(() => useSessionColorScheme());

    device.emitDeviceChange(true);
    expect(result.current.scheme).toBe("dark");

    act(() => result.current.toggle());
    expect(result.current.scheme).toBe("light");

    device.emitDeviceChange(true);
    expect(result.current.scheme).toBe("light");
  });

  it("ao remontar volta ao tema do aparelho (escolha não é persistida)", () => {
    installMatchMedia(false);
    const first = renderHook(() => useSessionColorScheme());
    act(() => first.result.current.toggle());
    expect(first.result.current.scheme).toBe("dark");
    first.unmount();

    const second = renderHook(() => useSessionColorScheme());
    expect(second.result.current.scheme).toBe("light");
    expect(second.result.current.userChosen).toBe(false);
  });
});
