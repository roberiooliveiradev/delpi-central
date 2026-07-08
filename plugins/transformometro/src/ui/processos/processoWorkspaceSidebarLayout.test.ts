import { describe, expect, it } from "vitest";

import {
  clampSidebarWidth,
  SIDEBAR_WIDTH_DEFAULT,
  SIDEBAR_WIDTH_MAX,
  SIDEBAR_WIDTH_MIN,
} from "./processoWorkspaceSidebarLayout";

describe("clampSidebarWidth", () => {
  it("retorna o default para valores inválidos", () => {
    expect(clampSidebarWidth(Number.NaN)).toBe(SIDEBAR_WIDTH_DEFAULT);
  });

  it("limita ao mínimo e máximo", () => {
    expect(clampSidebarWidth(100)).toBe(SIDEBAR_WIDTH_MIN);
    expect(clampSidebarWidth(999)).toBe(SIDEBAR_WIDTH_MAX);
    expect(clampSidebarWidth(300.7)).toBe(301);
  });
});
