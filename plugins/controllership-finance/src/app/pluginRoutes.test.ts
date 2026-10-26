import { describe, expect, it } from "vitest";

import {
  buildPluginPath,
  CONTROLLERSHIP_FINANCE_BASE_PATH,
  normalizeBasePath,
  normalizePathname,
  resolveActiveNavId,
  resolvePluginRoute,
} from "./pluginRoutes";

describe("pluginRoutes", () => {
  it("resolve a rota raiz como home", () => {
    const resolved = resolvePluginRoute("/apps/controllership-finance");
    expect(resolved.view).toBe("home");
    expect(resolved.relativePath).toBe("");
  });

  it("normaliza trailing slash no base path", () => {
    const resolved = resolvePluginRoute("/apps/controllership-finance/");
    expect(resolved.view).toBe("home");
  });

  it("resolve a rota de estoque histórico", () => {
    const resolved = resolvePluginRoute(
      "/apps/controllership-finance/closing/stock-inventory",
    );
    expect(resolved.view).toBe("stock_inventory");
    expect(resolved.relativePath).toBe("closing/stock-inventory");
    expect(buildPluginPath("stock_inventory")).toBe(
      "/apps/controllership-finance/closing/stock-inventory",
    );
  });

  it("resolve a rota de pendências", () => {
    const resolved = resolvePluginRoute(
      "/apps/controllership-finance/closing/pendencies",
    );
    expect(resolved.view).toBe("pendencies");
    expect(resolved.relativePath).toBe("closing/pendencies");
    expect(buildPluginPath("pendencies")).toBe(
      "/apps/controllership-finance/closing/pendencies",
    );
  });

  it("resolve as rotas de pacotes e cockpit", () => {
    const pkg = resolvePluginRoute(
      "/apps/controllership-finance/closing/packages",
    );
    expect(pkg.view).toBe("packages");
    expect(pkg.relativePath).toBe("closing/packages");
    expect(buildPluginPath("packages")).toBe(
      "/apps/controllership-finance/closing/packages",
    );
    const cockpit = resolvePluginRoute(
      "/apps/controllership-finance/closing/cockpit",
    );
    expect(cockpit.view).toBe("cockpit");
    expect(buildPluginPath("cockpit")).toBe(
      "/apps/controllership-finance/closing/cockpit",
    );
  });

  it("deep links de pacotes e cockpit com competência", () => {
    const pkg = resolvePluginRoute(
      "/apps/controllership-finance/closing/packages/2026-11",
    );
    expect(pkg.view).toBe("packages");
    expect(pkg.checklistPeriod).toBe("2026-11");
    const cockpit = resolvePluginRoute(
      "/apps/controllership-finance/closing/cockpit/2026-11",
    );
    expect(cockpit.view).toBe("cockpit");
    expect(cockpit.checklistPeriod).toBe("2026-11");
    expect(
      resolvePluginRoute(
        "/apps/controllership-finance/closing/packages/2026-13",
      ).view,
    ).toBe("not_found");
  });

  it("resolve a rota do workspace Fechamento mensal", () => {
    const resolved = resolvePluginRoute(
      "/apps/controllership-finance/closing/monthly-closing",
    );
    expect(resolved.view).toBe("monthly_closing");
    expect(resolved.relativePath).toBe("closing/monthly-closing");
    expect(buildPluginPath("monthly_closing")).toBe(
      "/apps/controllership-finance/closing/monthly-closing",
    );
    expect(
      buildPluginPath(
        "monthly_closing",
        "/apps/controllership-finance",
        "tab=documents",
      ),
    ).toBe("/apps/controllership-finance/closing/monthly-closing?tab=documents");
  });

  it("deep link de competência no Fechamento mensal", () => {
    const resolved = resolvePluginRoute(
      "/apps/controllership-finance/closing/monthly-closing/2026-10",
    );
    expect(resolved.view).toBe("monthly_closing");
    expect(resolved.checklistPeriod).toBe("2026-10");
    expect(
      resolvePluginRoute(
        "/apps/controllership-finance/closing/monthly-closing/2026-13",
      ).view,
    ).toBe("not_found");
  });

  it("resolve a rota do checklist da competência", () => {
    const resolved = resolvePluginRoute(
      "/apps/controllership-finance/closing/checklist",
    );
    expect(resolved.view).toBe("checklist");
    expect(resolved.relativePath).toBe("closing/checklist");
    expect(resolved.checklistPeriod).toBeUndefined();
    expect(buildPluginPath("checklist")).toBe(
      "/apps/controllership-finance/closing/checklist",
    );
  });

  it("resolve deep link com competência no checklist", () => {
    const resolved = resolvePluginRoute(
      "/apps/controllership-finance/closing/checklist/2026-10",
    );
    expect(resolved.view).toBe("checklist");
    expect(resolved.checklistPeriod).toBe("2026-10");
  });

  it("deep link de checklist com período inválido cai em not_found", () => {
    for (const path of [
      "/apps/controllership-finance/closing/checklist/2026-13",
      "/apps/controllership-finance/closing/checklist/10-2026",
      "/apps/controllership-finance/closing/checklist/extra/2026-10",
    ]) {
      expect(resolvePluginRoute(path).view).toBe("not_found");
    }
  });

  it("qualquer subrota não implementada cai em not_found", () => {
    for (const path of [
      "/apps/controllership-finance/overview",
      "/apps/controllership-finance/my-tasks",
      "/apps/controllership-finance/help",
      "/apps/controllership-finance/administration",
      "/other-app/x",
    ]) {
      expect(resolvePluginRoute(path).view).toBe("not_found");
    }
  });

  it("normalizePathname remove query e hash", () => {
    expect(normalizePathname("/apps/controllership-finance?q=x#y")).toBe(
      "/apps/controllership-finance",
    );
  });

  it("normalizeBasePath cai no canônico quando vazio", () => {
    expect(normalizeBasePath("")).toBe(CONTROLLERSHIP_FINANCE_BASE_PATH);
    expect(normalizeBasePath(undefined)).toBe(CONTROLLERSHIP_FINANCE_BASE_PATH);
  });

  it("buildPluginPath home preserva ?q= para deep link", () => {
    expect(buildPluginPath("home", "/apps/controllership-finance", "?q=ini")).toBe(
      "/apps/controllership-finance?q=ini",
    );
    expect(buildPluginPath("home", "/apps/controllership-finance")).toBe(
      "/apps/controllership-finance",
    );
  });

  it("resolveActiveNavId marca somente home", () => {
    expect(resolveActiveNavId("home")).toBe("home");
    expect(resolveActiveNavId("not_found")).toBeNull();
  });
});
