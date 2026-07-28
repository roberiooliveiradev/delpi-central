import { describe, expect, it } from "vitest";

import { shouldSuppressBrowserContextMenu } from "./useSuppressBrowserContextMenu";

describe("shouldSuppressBrowserContextMenu", () => {
  it("suprime dentro do root do plugin", () => {
    const root = document.createElement("div");
    root.className = "dashboard-tv-dashboard";
    const child = document.createElement("button");
    root.appendChild(child);
    document.body.appendChild(root);
    expect(shouldSuppressBrowserContextMenu(child)).toBe(true);
    root.remove();
  });

  it("não suprime fora do plugin (portal / host)", () => {
    const outside = document.createElement("div");
    outside.className = "portal-shell";
    document.body.appendChild(outside);
    expect(shouldSuppressBrowserContextMenu(outside)).toBe(false);
    outside.remove();
  });

  it("suprime em portal que carrega a classe de escopo do MFE", () => {
    const portal = document.createElement("div");
    portal.className = "dashboard-tv-dashboard delpi-ui-fixed-panel";
    const item = document.createElement("button");
    portal.appendChild(item);
    document.body.appendChild(portal);
    expect(shouldSuppressBrowserContextMenu(item)).toBe(true);
    portal.remove();
  });
});
