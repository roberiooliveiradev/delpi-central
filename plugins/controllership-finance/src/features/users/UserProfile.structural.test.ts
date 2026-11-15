import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  buildUserProfileHref,
  resolvePluginRoute,
} from "../../app/pluginRoutes";

const dir = dirname(fileURLToPath(import.meta.url));

describe("UserProfile (U9 R4)", () => {
  it("resolve users/:userId e alias /profile para user_profile", () => {
    const byId = resolvePluginRoute(
      "/apps/controllership-finance/users/22222222-2222-2222-2222-222222222222",
    );
    expect(byId.view).toBe("user_profile");
    expect(byId.userId).toBe("22222222-2222-2222-2222-222222222222");

    const byMe = resolvePluginRoute("/apps/controllership-finance/users/me");
    expect(byMe.view).toBe("user_profile");
    expect(byMe.userId).toBe("me");

    const legacy = resolvePluginRoute("/apps/controllership-finance/profile");
    expect(legacy.view).toBe("user_profile");
    expect(legacy.userId).toBe("me");
  });

  it("buildUserProfileHref gera path canônico", () => {
    expect(buildUserProfileHref("abc", "/apps/controllership-finance")).toBe(
      "/apps/controllership-finance/users/abc",
    );
    expect(buildUserProfileHref("", "/apps/controllership-finance")).toBe(
      "/apps/controllership-finance/users/me",
    );
  });

  it("App e página usam PortalUserProfilePage + /me/profile", () => {
    const app = readFileSync(join(dir, "../../App.tsx"), "utf8");
    const page = readFileSync(join(dir, "UserProfilePage.tsx"), "utf8");
    const shell = readFileSync(join(dir, "../../app/PluginShell.tsx"), "utf8");
    expect(app).toMatch(/UserProfilePage/);
    expect(page).toMatch(/createDashboardPortalUserProfilePage/);
    expect(page).toMatch(/getMyProfile/);
    expect(page).toMatch(/HOST_SELF_PROFILE_PATH/);
    expect(page).toMatch(/isSelf=\{isSelf\}/);
    expect(shell).toMatch(/buildUserProfileHref/);
    expect(shell).not.toMatch(/avatarHref="\/profile"/);
  });
});
