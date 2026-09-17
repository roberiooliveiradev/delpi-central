import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const dir = dirname(fileURLToPath(import.meta.url));

describe("ProductionPulseRealtime wiring", () => {
  it("App mounts RealtimeProvider", () => {
    const app = readFileSync(join(dir, "../App.tsx"), "utf8");
    expect(app).toContain("<ProductionPulseRealtimeProvider");
    expect(app).toContain("</ProductionPulseRealtimeProvider>");
    expect(app).toContain("ProductionPulseShell");
  });

  it("FirmwareLinksPage soft-reloads without structural loading", () => {
    const page = readFileSync(join(dir, "../pages/FirmwareLinksPage.tsx"), "utf8");
    expect(page).toContain("softReloadGraph");
    expect(page).toContain("useProductionPulseHubSync");
    expect(page).toContain("isHubInteractionBlocking");
    expect(page).toContain("GRAPH_FALLBACK_POLL_MS");
    expect(page).toMatch(/softReloadGraph[\s\S]*?setFirmwares/);
    expect(page).not.toMatch(
      /const softReloadGraph[\s\S]*?setLoading\(true\)/,
    );
  });

  it("FirmwareLinksPage atualiza golpes no mapa no ritmo live do operador", () => {
    const page = readFileSync(join(dir, "../pages/FirmwareLinksPage.tsx"), "utf8");
    expect(page).toContain("softReloadDevices");
    expect(page).toContain("useDeviceLiveRefresh");
    expect(page).toContain("resolveHubDevicesLiveRefreshIntervalMs");
    expect(page).toMatch(/softReloadDevices[\s\S]*?fetchDevices/);
    expect(page).not.toMatch(
      /const softReloadDevices[\s\S]*?fetchFirmwares/,
    );
  });

  it("FirmwareLinksPage troca de filial mantém canvas (soft refresh)", () => {
    const page = readFileSync(join(dir, "../pages/FirmwareLinksPage.tsx"), "utf8");
    const css = readFileSync(join(dir, "../index.css"), "utf8");
    expect(page).toContain("canvasHydrated");
    expect(page).toContain("canvasRefreshing");
    expect(page).toContain("pp-admin-viewport--refreshing");
    expect(page).toMatch(/!canvasHydrated && loading/);
    expect(page).toMatch(/const soft = canvasHydratedRef\.current/);
    expect(css).toMatch(/\.pp-admin-viewport--refreshing/);
  });
});
