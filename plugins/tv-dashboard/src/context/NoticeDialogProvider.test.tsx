import { act, cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { TV_DASHBOARD_ROOT_CLASS } from "../constants/pluginRootClass";
import { NoticeDialogProvider } from "../context/NoticeDialogProvider";
import { tvDashboardNotice } from "../utils/tvDashboardNotice";

afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

describe("NoticeDialogProvider", () => {
  it("exibe «Link copiado.» como toast flutuante (não modal)", async () => {
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
    expect(screen.queryByRole("dialog")).toBeNull();
    expect(screen.queryByRole("button", { name: "OK" })).toBeNull();

    const toast = screen.getByRole("status");
    expect(toast.className).toContain("delpi-ui-floating-notice--info");
    expect(toast.className).toContain("td-floating-notice--info");
    expect(
      document.querySelector(`.${TV_DASHBOARD_ROOT_CLASS} .delpi-ui-floating-notices`),
    ).toBeTruthy();
  });

  it("fecha sozinho após o auto-dismiss de info", () => {
    vi.useFakeTimers();
    render(
      <div className={TV_DASHBOARD_ROOT_CLASS}>
        <NoticeDialogProvider>
          <button type="button" onClick={() => tvDashboardNotice("Link copiado.")}>
            Copiar
          </button>
        </NoticeDialogProvider>
      </div>,
    );
    act(() => {
      screen.getByRole("button", { name: "Copiar" }).click();
    });
    expect(screen.getByText("Link copiado.")).toBeTruthy();

    act(() => {
      vi.advanceTimersByTime(6001);
    });
    expect(screen.queryByText("Link copiado.")).toBeNull();
  });
});
