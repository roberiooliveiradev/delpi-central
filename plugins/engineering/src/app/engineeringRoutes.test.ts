import { describe, expect, it, vi } from "vitest";

import {
  navigateGovernedHref,
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

describe("navigateGovernedHref", () => {
  function stubWindow() {
    const pushed: string[] = [];
    const assigned: string[] = [];
    const events: string[] = [];
    vi.stubGlobal("window", {
      history: {
        state: {},
        pushState: (_s: unknown, _t: string, url: string) =>
          pushed.push(url),
        replaceState: (_s: unknown, _t: string, url: string) =>
          pushed.push(`replace:${url}`),
      },
      location: { assign: (url: string) => assigned.push(url) },
      dispatchEvent: (ev: { type: string }) => events.push(ev.type),
    });
    vi.stubGlobal("PopStateEvent", class {
      constructor(public type: string, public init?: unknown) {}
    });
    return { pushed, assigned, events };
  }

  it("destino interno PRC → pushState + popstate (sem location.assign)", () => {
    const w = stubWindow();
    navigateGovernedHref(
      "/apps/engineering/product-registration/48161981-2427-4a10-a9e5-62165366b32d",
      { basePath: "/apps/engineering" },
    );
    expect(w.assigned).toEqual([]);
    expect(w.pushed).toEqual([
      "/apps/engineering/product-registration/48161981-2427-4a10-a9e5-62165366b32d",
    ]);
    expect(w.events).toEqual(["popstate"]);
  });

  it("destino externo ao MFE → location.assign (My Requests corporativo)", () => {
    const w = stubWindow();
    navigateGovernedHref("/apps/my-requests", {
      basePath: "/apps/engineering",
    });
    expect(w.pushed).toEqual([]);
    expect(w.assigned).toEqual(["/apps/my-requests"]);
  });

  it("href não governado é recusado sem efeito", () => {
    const w = stubWindow();
    navigateGovernedHref("https://externo.invalid/x", {
      basePath: "/apps/engineering",
    });
    navigateGovernedHref(null, { basePath: "/apps/engineering" });
    expect([...w.pushed, ...w.assigned]).toEqual([]);
  });
});
