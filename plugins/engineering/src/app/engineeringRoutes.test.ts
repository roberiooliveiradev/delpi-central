import { describe, expect, it } from "vitest";

import {
  buildEngineeringPath,
  isGovernedAppsHref,
  resolveEngineeringRoute,
} from "./engineeringRoutes";

describe("resolveEngineeringRoute", () => {
  it("base → home", () => {
    const route = resolveEngineeringRoute("/apps/engineering");
    expect(route.view).toBe("home");
  });

  it("sub-rotas canônicas → overview/help", () => {
    expect(resolveEngineeringRoute("/apps/engineering/overview").view).toBe(
      "overview",
    );
    expect(resolveEngineeringRoute("/apps/engineering/help").view).toBe(
      "help",
    );
  });

  it("sub-path desconhecido → not_found", () => {
    expect(
      resolveEngineeringRoute("/apps/engineering/qualquer-coisa").view,
    ).toBe("not_found");
  });

  it("path fora do base → not_found", () => {
    expect(resolveEngineeringRoute("/apps/outro").view).toBe("not_found");
  });

  it("trailing slash e query normalizados", () => {
    expect(
      resolveEngineeringRoute("/apps/engineering/overview/?x=1").view,
    ).toBe("overview");
  });
});

describe("buildEngineeringPath", () => {
  it("home → base path", () => {
    expect(buildEngineeringPath("home")).toBe("/apps/engineering");
  });

  it("sub-rotas → prefixo do manifest", () => {
    expect(buildEngineeringPath("overview")).toBe("/apps/engineering/overview");
    expect(buildEngineeringPath("help")).toBe("/apps/engineering/help");
  });
});

describe("isGovernedAppsHref", () => {
  it("aceita somente hrefs /apps/*", () => {
    expect(isGovernedAppsHref("/apps/my-requests")).toBe(true);
    expect(isGovernedAppsHref("/apps/dashboard-lmps/nonconformities")).toBe(
      true,
    );
    expect(isGovernedAppsHref("https://externo.invalid")).toBe(false);
    expect(isGovernedAppsHref("/api-delpi/lmps")).toBe(false);
    expect(isGovernedAppsHref("javascript:alert(1)")).toBe(false);
    expect(isGovernedAppsHref(null)).toBe(false);
    expect(isGovernedAppsHref(undefined)).toBe(false);
  });
});
