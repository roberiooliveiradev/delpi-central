import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { NoticeDialogProvider } from "../context/NoticeDialogProvider";
import { tvDashboardNotice } from "../utils/tvDashboardNotice";

afterEach(() => {
  cleanup();
});

describe("NoticeDialogProvider", () => {
  it("exibe «Link copiado.» no Modal Delpi em vez do alert do navegador", async () => {
    render(
      <NoticeDialogProvider>
        <button type="button" onClick={() => tvDashboardNotice("Link copiado.")}>
          Copiar
        </button>
      </NoticeDialogProvider>,
    );
    screen.getByRole("button", { name: "Copiar" }).click();
    expect(await screen.findByText("Link copiado.")).toBeTruthy();
    expect(screen.getByRole("button", { name: "OK" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Cancelar" })).toBeNull();
  });
});
