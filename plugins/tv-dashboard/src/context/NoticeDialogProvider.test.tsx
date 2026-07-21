import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";
import { NoticeDialogProvider } from "../context/NoticeDialogProvider";
import { tvDashboardNotice } from "../utils/tvDashboardNotice";

afterEach(() => {
  cleanup();
});

describe("NoticeDialogProvider", () => {
  it("exibe «Link copiado.» no dialog contido no host (não cobre sidebar do portal)", async () => {
    render(
      <div className={TV_DASHBOARD_ROOT_CLASS}>
        <NoticeDialogProvider>
          <button type="button" onClick={() => tvDashboardNotice("Link copiado.")}>
            Copiar
          </button>
        </NoticeDialogProvider>
      </div>,
    );
    screen.getByRole("button", { name: "Copiar" }).click();
    expect(await screen.findByText("Link copiado.")).toBeTruthy();
    expect(screen.getByRole("button", { name: "OK" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Cancelar" })).toBeNull();

    const dialog = screen.getByRole("dialog", { name: "Aviso" });
    const host = document.querySelector(`.${TV_DASHBOARD_ROOT_CLASS}`);
    expect(host?.contains(dialog)).toBe(true);
    expect(dialog.closest("[data-modal-contained='true']")).toBeTruthy();
    expect(dialog.classList.contains("delpi-ui-modal--host-fill")).toBe(false);
    expect(dialog.closest(".delpi-ui-modal-overlay--contained-dialog")).toBeTruthy();
  });
});
