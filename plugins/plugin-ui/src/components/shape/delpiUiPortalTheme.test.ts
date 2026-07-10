import { describe, expect, it } from "vitest";

import { DELPI_UI_SHAPE_THEME_HOST_CLASS, resolveDelpiUiPortalTheme } from "./delpiUiPortalTheme";

describe("resolveDelpiUiPortalTheme", () => {
  it("expõe classe canônica do host de tema", () => {
    expect(DELPI_UI_SHAPE_THEME_HOST_CLASS).toBe("delpi-ui-shape-theme-host");
  });

  it("retorna objeto de estilo sem quebrar fora do DOM", () => {
    const theme = resolveDelpiUiPortalTheme();
    expect(theme).toHaveProperty("style");
    expect(typeof theme.style).toBe("object");
  });
});
