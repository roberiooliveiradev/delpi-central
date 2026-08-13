import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "../../..");
const src = join(root, "src");

describe("Conta deep-link gate + topbar Cliente", () => {
  it("customer_detail não exige canAccessMyPortfolio; shell injeta Cliente", () => {
    const app = readFileSync(join(src, "App.tsx"), "utf8");
    assert.match(app, /ephemeralClientNav/);
    assert.match(app, /shouldShowEphemeralClientNav/);
    assert.match(
      app,
      /view === "customer_detail" && route\.codigo && route\.loja \? \(\s*<CustomerDetailPage/,
    );
    assert.doesNotMatch(
      app,
      /view === "customer_detail"[^?]{0,80}canAccessMyPortfolio/,
    );

    const shell = readFileSync(join(src, "app/PluginShell.tsx"), "utf8");
    assert.match(shell, /ephemeralClientNav/);
    assert.match(shell, /client_context/);
    assert.match(shell, /clientContextLabel/);

    const routes = readFileSync(join(src, "app/pluginRoutes.ts"), "utf8");
    assert.match(routes, /customerDetailOutsidePortfolio/);
    assert.match(routes, /"client_context"/);
  });
});
