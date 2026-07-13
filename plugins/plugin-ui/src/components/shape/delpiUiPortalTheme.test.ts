import { describe, expect, it } from "vitest";

import {
  DELPI_UI_SHAPE_THEME_HOST_CLASS,
  resolveDelpiUiPortalTheme,
  resolveMfePortalScopeClassName,
} from "./delpiUiPortalTheme";

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

describe("resolveMfePortalScopeClassName", () => {
  it("prioriza escopo explícito", () => {
    expect(resolveMfePortalScopeClassName(null, "dashboard-quality")).toBe("dashboard-quality");
  });

  it("infere ancestral dashboard-* do âncora", () => {
    const root = document.createElement("div");
    root.className = "dashboard-quality dashboard-page";
    const anchor = document.createElement("div");
    root.appendChild(anchor);
    document.body.appendChild(root);

    expect(resolveMfePortalScopeClassName(anchor)).toBe("dashboard-quality");

    root.remove();
  });

  it("retorna undefined sem âncora nem prop", () => {
    expect(resolveMfePortalScopeClassName()).toBeUndefined();
  });
});
