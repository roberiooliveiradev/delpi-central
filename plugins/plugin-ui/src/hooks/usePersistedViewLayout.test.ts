import { cleanup, renderHook, act } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { usePersistedViewLayout } from "./usePersistedViewLayout";

afterEach(cleanup);

describe("usePersistedViewLayout", () => {
  const storage = new Map<string, string>();

  beforeEach(() => {
    storage.clear();
    vi.stubGlobal("localStorage", {
      getItem: (key: string) => storage.get(key) ?? null,
      setItem: (key: string, value: string) => {
        storage.set(key, value);
      },
      removeItem: (key: string) => {
        storage.delete(key);
      },
    });
    vi.stubGlobal("matchMedia", (query: string) => ({
      matches: query.includes("768"),
      media: query,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      addListener: () => undefined,
      removeListener: () => undefined,
      dispatchEvent: () => false,
      onchange: null,
    }));
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("persiste layout e usa default mobile cards", () => {
    const { result } = renderHook(() =>
      usePersistedViewLayout({ storageKey: "demo:layout" }),
    );
    expect(result.current.layout).toBe("cards");

    act(() => {
      result.current.setLayout("table");
    });
    expect(result.current.layout).toBe("table");
    expect(storage.get("demo:layout")).toBe("table");
  });

  it("respeita valor já persistido", () => {
    storage.set("demo:layout", "table");
    const { result } = renderHook(() =>
      usePersistedViewLayout({ storageKey: "demo:layout" }),
    );
    expect(result.current.layout).toBe("table");
  });
});
