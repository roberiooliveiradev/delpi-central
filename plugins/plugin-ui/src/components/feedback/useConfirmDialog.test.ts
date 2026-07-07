import { describe, expect, it } from "vitest";
import { renderHook, act } from "@testing-library/react";

import { useConfirmDialogController } from "./useConfirmDialog";

describe("useConfirmDialogController", () => {
  it("resolve true ao confirmar", async () => {
    const { result } = renderHook(() => useConfirmDialogController());

    let promise!: Promise<boolean>;
    act(() => {
      promise = result.current.confirm({ message: "Excluir?" });
    });

    expect(result.current.isOpen).toBe(true);

    act(() => {
      result.current.confirmPending();
    });

    await expect(promise).resolves.toBe(true);
    expect(result.current.isOpen).toBe(false);
  });
});
