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
