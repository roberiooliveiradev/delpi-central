import { describe, expect, it } from "vitest";
import { renderHook, act } from "@testing-library/react";

import {
  unsavedChangesDialogOptions,
  useConfirmDialogController,
} from "./useConfirmDialog";

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

  it("confirmChoice resolve secondary e cancel", async () => {
    const { result } = renderHook(() => useConfirmDialogController());

    let promise!: Promise<"confirm" | "secondary" | "cancel">;
    act(() => {
      promise = result.current.confirmChoice(unsavedChangesDialogOptions());
    });

    act(() => {
      result.current.secondaryPending();
    });
    await expect(promise).resolves.toBe("secondary");

    act(() => {
      promise = result.current.confirmChoice(unsavedChangesDialogOptions());
    });
    act(() => {
      result.current.cancelPending();
    });
    await expect(promise).resolves.toBe("cancel");
  });
});
