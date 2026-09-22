#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const root = join(dirname(fileURLToPath(import.meta.url)), "../..");
const src = join(root, "src");

describe("ShellUserPortfolioMenu (TopBar)", () => {
  it("TopBar recebe o menu de usuário no slot actions", () => {
    const shell = readFileSync(join(src, "app/PluginShell.tsx"), "utf8");
    assert.match(shell, /ShellUserPortfolioMenu/);
    assert.match(shell, /actions=\{\s*<ShellUserPortfolioMenu/);
    assert.doesNotMatch(shell, /SHELL_NAV_CONTENT\.scopeLabel/);
  });

  it("modo 0/1/N e deep link ficam no helper canônico", () => {
    const helper = readFileSync(join(src, "app/shellUserPortfolioNav.ts"), "utf8");
    assert.match(helper, /resolveShellUserPortfolioNavMode/);
    assert.match(helper, /buildShellPortfolioCustomersSearch/);
    assert.match(helper, /kind: "disabled"/);
    assert.match(helper, /kind: "direct"/);
    assert.match(helper, /kind: "menu"/);
  });

  it("textos do menu vivem em shellNav", () => {
    const nav = readFileSync(join(src, "content/shellNav.ts"), "utf8");
    assert.match(nav, /userMenu:/);
    assert.match(nav, /profileAriaLabel/);
    assert.match(nav, /menuOpenAriaLabel/);
    assert.doesNotMatch(nav, /enlargePhotoAriaLabel/);
    assert.doesNotMatch(nav, /openProfileFromPreview/);
  });

  it("avatar na TopBar abre o perfil do Portal Comercial (/users/:id)", () => {
    const menu = readFileSync(join(src, "app/ShellUserPortfolioMenu.tsx"), "utf8");
    assert.match(menu, /CommercialTopBarUserIdentity/);
    assert.match(menu, /avatarHref/);
    assert.match(menu, /onAvatarNavigate/);
    assert.match(menu, /goToPortalProfile/);
    assert.match(menu, /navigateUserProfile/);
    assert.match(menu, /buildUserProfileHref/);
    assert.match(menu, /userProfilePhotoAbsoluteUrl/);
    assert.match(menu, /menuItems/);
    assert.doesNotMatch(menu, /HOST_SELF_PROFILE_PATH/);
    assert.doesNotMatch(menu, /navigateHostPath/);
    assert.doesNotMatch(menu, /goToHostProfile/);
    assert.doesNotMatch(menu, /previewable=\{hasPhoto\}/);
    assert.doesNotMatch(menu, /openProfileFromPreview/);
    assert.doesNotMatch(menu, /cm-shell-user__trigger/);
  });
});
