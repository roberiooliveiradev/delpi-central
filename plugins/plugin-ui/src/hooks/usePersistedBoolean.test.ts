import { cleanup, renderHook, act } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { usePersistedBoolean } from "./usePersistedBoolean";

afterEach(cleanup);

describe("usePersistedBoolean", () => {
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
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("usa defaultValue e persiste alterações", () => {
    const { result } = renderHook(() =>
      usePersistedBoolean({ storageKey: "demo:flag", defaultValue: false }),
    );
    expect(result.current.value).toBe(false);

    act(() => {
      result.current.setValue(true);
    });
    expect(result.current.value).toBe(true);
    expect(storage.get("demo:flag")).toBe("1");
  });

  it("respeita valor já persistido", () => {
    storage.set("demo:flag", "1");
    const { result } = renderHook(() =>
      usePersistedBoolean({ storageKey: "demo:flag", defaultValue: false }),
    );
    expect(result.current.value).toBe(true);
  });

  it("quando enabled=false não lê nem grava localStorage", () => {
    storage.set("demo:flag", "1");
    const { result } = renderHook(() =>
      usePersistedBoolean({
        storageKey: "demo:flag",
        defaultValue: false,
        enabled: false,
      }),
    );
    expect(result.current.value).toBe(false);

    act(() => {
      result.current.setValue(true);
    });
    expect(storage.get("demo:flag")).toBe("1");
  });
});
