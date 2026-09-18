import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { resolveManifestRoutePermission } from "../../../../portal/src/utils/manifestRoutePermission";

const ACCESS = "transformometro.access";
const MANAGE = "transformometro.manage";

type PublishedRoute = {
  path: string;
  permission: string;
};

const manifest = JSON.parse(
  readFileSync(resolve(dirname(fileURLToPath(import.meta.url)), "../../transformometro.manifest.json"), "utf8"),
) as {
  version: string;
  permissions: { code: string }[];
  routes: PublishedRoute[];
};

const publishedRoutes = manifest.routes.map((route) => ({
  app: "transformometro",
  path: route.path,
  permission: route.permission,
}));

/**
 * Espelha o `ProtectedRoute` do portal: superadmin passa; permission resolvida
 * precisa estar na lista; permission ausente não nega. Não é uma regra nova.
 */
function portalAllows(
  permissions: readonly string[],
  pathname: string,
  isSuperadmin = false,
): boolean {
  if (isSuperadmin) return true;
  const required = resolveManifestRoutePermission(publishedRoutes, pathname);
  if (!required) return true;
  return permissions.includes(required);
}

describe("Ajuda como rota interna do MFE", () => {
  it("não publica /help no manifesto 0.5.5", () => {
    expect(manifest.version).toBe("0.5.5");
    expect(manifest.permissions.map((item) => item.code)).toEqual([ACCESS, MANAGE]);
    expect(manifest.routes.map((route) => route.path)).not.toContain("/apps/transformometro/help");
    expect(manifest.routes.map((route) => route.path)).not.toContain("/apps/transformometro/ajuda");
  });

  it("resolve /help pelo prefixo de access, sem entrada própria", () => {
    expect(resolveManifestRoutePermission(publishedRoutes, "/apps/transformometro/help")).toBe(ACCESS);
    expect(resolveManifestRoutePermission(publishedRoutes, "/apps/transformometro/administration")).toBe(MANAGE);
    expect(resolveManifestRoutePermission(publishedRoutes, "/apps/transformometro/settings/units")).toBe(MANAGE);
  });

  it("libera Ajuda com access e nega sem access ou só com manage", () => {
    expect(portalAllows([ACCESS], "/apps/transformometro/help")).toBe(true);
    expect(portalAllows([ACCESS, MANAGE], "/apps/transformometro/help")).toBe(true);
    expect(portalAllows([], "/apps/transformometro/help")).toBe(false);
    expect(portalAllows([MANAGE], "/apps/transformometro/help")).toBe(false);
    expect(portalAllows([MANAGE], "/apps/transformometro/dashboard")).toBe(false);
    expect(portalAllows([ACCESS], "/apps/transformometro/administration")).toBe(false);
  });
});
