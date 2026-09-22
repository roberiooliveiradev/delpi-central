import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { canAccessUserProfile } from "../../app/routeAccess";
import { resolvePluginRoute } from "../../app/pluginRoutes";

const dir = dirname(fileURLToPath(import.meta.url));

describe("UserProfile", () => {
  it("resolve users/:userId para user_profile", () => {
    const route = resolvePluginRoute(
      "/apps/supplies/users/22222222-2222-2222-2222-222222222222",
    );
    expect(route.view).toBe("user_profile");
    expect(route.userId).toBe("22222222-2222-2222-2222-222222222222");
  });

  it("App e página usam BFF supplies-api", () => {
    const app = readFileSync(join(dir, "../../App.tsx"), "utf8");
    const page = readFileSync(join(dir, "UserProfilePage.tsx"), "utf8");
    const api = readFileSync(join(dir, "../../api/userProfileApi.ts"), "utf8");
    expect(app).toMatch(/UserProfilePage/);
    expect(page).toMatch(/preferencesTitle/);
    expect(page).toMatch(/useMyPersonProfile/);
    expect(page).toMatch(/jobTitleLabel/);
    expect(api).toMatch(/suppliesApiUrl\(`\/users\//);
    expect(api).not.toMatch(/purchase-requests-api/);
  });

  it("compõe o perfil com o kit PortalUserProfilePage", () => {
    const page = readFileSync(join(dir, "UserProfilePage.tsx"), "utf8");
    expect(page).toMatch(/createDashboardPortalUserProfilePage/);
    /** Layout de identidade/atalhos é do kit — sem CSS paralelo no MFE. */
    expect(page).not.toMatch(
      /sp-user-profile__(grid|identity|shortcuts|error)\b/,
    );
    /** Identidade é leitura; editar abre o Meu Perfil da Minha DELPI. */
    expect(page).toMatch(/HOST_SELF_PROFILE_PATH/);
  });

  it("acesso self ok · outro sem admin negado · admin ok", () => {
    const selfId = "self-1";
    const caps = {
      access: true,
      manage: false,
    };
    expect(canAccessUserProfile(selfId, { userId: selfId, capabilities: caps })).toBe(true);
    expect(canAccessUserProfile("other", { userId: selfId, capabilities: caps })).toBe(false);
    expect(
      canAccessUserProfile("other", {
        userId: selfId,
        capabilities: { ...caps, manage: true },
      }),
    ).toBe(true);
  });
});
