import { renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useUnsavedChangesWarning } from "./useUnsavedChangesWarning";

describe("useUnsavedChangesWarning", () => {
  afterEach(() => vi.restoreAllMocks());

  it("registra beforeunload só quando ativo e remove na limpeza", () => {
    const add = vi.spyOn(window, "addEventListener");
    const remove = vi.spyOn(window, "removeEventListener");

    const { rerender, unmount } = renderHook(
      ({ active }) => useUnsavedChangesWarning(active),
      { initialProps: { active: false } },
    );
    expect(add).not.toHaveBeenCalledWith("beforeunload", expect.any(Function));

    rerender({ active: true });
    expect(add).toHaveBeenCalledWith("beforeunload", expect.any(Function));

    rerender({ active: false });
    expect(remove).toHaveBeenCalledWith("beforeunload", expect.any(Function));

    unmount();
  });
});
