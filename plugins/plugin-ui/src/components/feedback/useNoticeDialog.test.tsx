import { cleanup, render, screen } from "@testing-library/react";
import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ConfirmModalPanel, confirmModalPacClasses } from "./ConfirmModalPanel";
import { useNoticeDialogController } from "./useNoticeDialog";

afterEach(() => {
  cleanup();
});

describe("ConfirmModalPanel alert mode", () => {
  it("omite Cancelar quando showCancel=false", () => {
    render(
      <ConfirmModalPanel
        message="Link copiado."
        confirmLabel="OK"
        showCancel={false}
        classNames={confirmModalPacClasses()}
        onConfirm={vi.fn()}
        onCancel={vi.fn()}
      />,
    );
    expect(screen.getByRole("button", { name: "OK" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Cancelar" })).toBeNull();
  });
});

describe("useNoticeDialogController", () => {
  it("abre aviso e resolve ao dismiss", async () => {
    const { result } = renderHook(() => useNoticeDialogController());
    let settled = false;
    act(() => {
      void result.current.notice("Link copiado.").then(() => {
        settled = true;
      });
    });
    expect(result.current.pending?.message).toBe("Link copiado.");
    act(() => {
      result.current.dismiss();
    });
    await Promise.resolve();
    expect(result.current.pending).toBeNull();
    expect(settled).toBe(true);
  });
});
