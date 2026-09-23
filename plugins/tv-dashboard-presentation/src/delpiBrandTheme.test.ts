import { describe, expect, it } from "vitest";

import {
  delpiBrandTokensForRecipes,
  getDelpiBrandAccent,
  getDelpiBrandColors,
  getDelpiBrandMode,
  getDelpiBrandTheme,
  resolveDelpiBrandLogoFrame,
} from "./delpiBrandTheme";

describe("delpiBrandTheme JSON", () => {
  it("define modos dark e light com cores Delpi", () => {
    const doc = getDelpiBrandTheme();
    expect(doc.modes.dark).toBeTruthy();
    expect(doc.modes.light).toBeTruthy();
    expect(getDelpiBrandAccent()).toBe("#089bdb");
    expect(getDelpiBrandColors("dark").navy).toBe("#003866");
    expect(getDelpiBrandColors("light").onBg).toBe("#0f172a");
    expect(getDelpiBrandColors("light").accentWash).toBe("#e8f4fc");
    expect(getDelpiBrandColors("dark").borderMuted).toBe("#94a3b8");
    expect(getDelpiBrandMode("dark").logoVariant).toBe("onDark");
    expect(getDelpiBrandMode("light").logoVariant).toBe("onLight");
  });

  it("slideThemeBindings Delpi claro/escuro com logo", () => {
    const bindings = getDelpiBrandTheme().slideThemeBindings;
    const keys = bindings.map((b) => b.key);
    expect(keys).toContain("delpi-dark");
    expect(keys).toContain("delpi-light");
    expect(bindings.every((b) => b.showLogo !== false)).toBe(true);
    expect(bindings.find((b) => b.key === "delpi-dark")?.label).toMatch(/escuro/i);
    expect(bindings.find((b) => b.key === "delpi-light")?.label).toMatch(/claro/i);
  });

  it("frame da logo vem do JSON (canto inferior direito)", () => {
    const frame = resolveDelpiBrandLogoFrame();
    expect(frame.y).toBeGreaterThan(50);
    expect(frame.x + frame.w).toBeLessThanOrEqual(97);
    expect(frame.y + frame.h).toBeLessThanOrEqual(97);
  });

  it("tokens flat para recipes espelham modo escuro", () => {
    const tokens = delpiBrandTokensForRecipes("dark");
    expect(tokens.accent).toBe(getDelpiBrandAccent());
    expect(tokens.bgFrom).toBe(getDelpiBrandColors("dark").bgFrom);
    expect(tokens.onBg).toBe("#ffffff");
  });
});
