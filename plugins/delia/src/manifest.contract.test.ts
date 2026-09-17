import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const pluginRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const manifestPath = path.join(pluginRoot, "delpi.manifest.json");

describe("DÉLIA publication manifest contract", () => {
  const raw = readFileSync(manifestPath, "utf8");
  const manifest = JSON.parse(raw) as Record<string, unknown>;

  it("uses canonical identity and federation paths", () => {
    expect(manifest.schemaVersion).toBe("1.0.0");
    expect(manifest.id).toBe("delia");
    expect(manifest.name).toBe("DÉLIA");
    expect(manifest.type).toBe("microfrontend");
    expect(manifest.basePath).toBe("/apps/delia");
    expect(manifest.entry).toBe("/apps/delia/assets/remoteEntry.js");
    expect((manifest.ui as { renderMode: string }).renderMode).toBe("federated");
  });

  it("does not invent business capability routes or Chat identity", () => {
    const routes = manifest.routes as Array<{ path: string }>;
    expect(routes).toHaveLength(1);
    expect(routes[0].path).toBe("/apps/delia");
    for (const forbidden of ["/chat", "/work", "/watch", "/decision", "/evidence", "/admin"]) {
      expect(routes.some((r) => r.path.includes(forbidden))).toBe(false);
    }
    expect(JSON.stringify(manifest)).not.toContain("minha-delpi-copilot");
    expect(JSON.stringify(manifest)).not.toContain("minha-delpi-chat");
  });

  it("declares only bootstrap visibility permission metadata", () => {
    const permissions = manifest.permissions as Array<{ code: string; module: string }>;
    expect(permissions).toHaveLength(1);
    expect(permissions[0].code).toBe("delia.access");
    expect(permissions[0].module).toBe("delia");
  });

  it("declares backend metadata without secrets", () => {
    const backend = manifest.backend as Record<string, unknown>;
    expect(backend.required).toBe(true);
    expect(backend.serviceName).toBe("delia-api");
    expect(backend.baseUrl).toBe("/apps/delia-api");
    expect(backend.validateJwt).toBe(true);
    expect(backend).not.toHaveProperty("client_secret");
    expect(JSON.stringify(manifest).toLowerCase()).not.toContain("password");
    expect(JSON.stringify(manifest)).not.toContain("Bearer");
  });

  it("does not declare exposedModule (Portal defaults to ./App)", () => {
    expect(manifest).not.toHaveProperty("exposedModule");
  });

  it("matches C1-T3 Vite base and remoteEntry convention", () => {
    const viteConfig = readFileSync(path.join(pluginRoot, "vite.config.ts"), "utf8");
    expect(viteConfig).toContain('base: "/apps/delia/"');
    expect(viteConfig).toContain('filename: "remoteEntry.js"');
    expect(viteConfig).toContain('"./App": "./src/bootstrap.tsx"');
    expect(manifest.entry).toBe("/apps/delia/assets/remoteEntry.js");
  });
});
