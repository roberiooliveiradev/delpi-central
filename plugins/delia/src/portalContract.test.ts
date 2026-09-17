import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

/**
 * Portal AppHost contract: container.get("./App") → module with mount(+unmount).
 * Production expose is declared in vite.config.ts; this test locks the shape.
 */
describe("Portal federation contract", () => {
  const pluginRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

  it("exposes ./App from bootstrap with mount/unmount lifecycle", () => {
    const viteConfig = readFileSync(path.join(pluginRoot, "vite.config.ts"), "utf8");
    expect(viteConfig).toContain('name: "delia"');
    expect(viteConfig).toContain('filename: "remoteEntry.js"');
    expect(viteConfig).toContain('"./App": "./src/bootstrap.tsx"');
    expect(viteConfig).toContain("pluginUiRemote()");
    expect(viteConfig).toContain("FEDERATION_SHARED_REACT");
    expect(viteConfig).toContain("federationReactProxyFixPlugin()");
    expect(viteConfig).toContain('base: "/apps/delia/"');

    const bootstrap = readFileSync(path.join(pluginRoot, "src/bootstrap.tsx"), "utf8");
    expect(bootstrap).toContain("preparePluginUiRemote");
    expect(bootstrap).toContain("getReactDomClient");
    expect(bootstrap).toContain("export function mount");
    expect(bootstrap).toContain("export function unmount");
    expect(bootstrap).toContain("export function updateRoute");
    expect(bootstrap).toContain('await import("./App")');
    expect(bootstrap).not.toMatch(/^import\s+(?!type\b).*from\s+["']\.\/App["']/m);
  });
});
