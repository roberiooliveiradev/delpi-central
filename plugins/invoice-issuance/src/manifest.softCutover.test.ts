import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

describe("invoice-issuance manifest soft cutover (E12)", () => {
  it("oculta rotas de app do menu (showInMenu false)", () => {
    const raw = readFileSync(
      join(__dirname, "../invoice-issuance.manifest.json"),
      "utf8",
    );
    const manifest = JSON.parse(raw) as {
      routes: Array<{ path: string; showInMenu?: boolean; label?: string }>;
    };
    const appRoutes = manifest.routes.filter((r) =>
      r.path.startsWith("/apps/invoice-issuance"),
    );
    expect(appRoutes.length).toBeGreaterThan(0);
    for (const route of appRoutes) {
      expect(route.showInMenu).toBe(false);
      expect(route.label || "").toMatch(/legado/i);
    }
  });
});
