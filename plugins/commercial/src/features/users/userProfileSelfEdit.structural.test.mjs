import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const src = join(dirname(fileURLToPath(import.meta.url)), "../..");

describe("user profile self-only + expand photo", () => {
  it("canEdit=isSelf e editar identidade abre o /profile do host", () => {
    const page = readFileSync(
      join(src, "features/users/UserProfilePage.tsx"),
      "utf8",
    );
    const copy = readFileSync(join(src, "content/userAccess.json"), "utf8");
    assert.match(page, /const canEdit = isSelf/);
    assert.doesNotMatch(page, /canEdit = isSelf \|\|/);
    assert.match(page, /HOST_SELF_PROFILE_PATH/);
    assert.match(page, /navigateHostPath/);
    assert.match(copy, /"editIdentity"/);
    assert.match(copy, /"identityHostNote"/);
  });

  it("identidade é leitura — sem patch/upload/form de contato no Portal", () => {
    const page = readFileSync(
      join(src, "features/users/UserProfilePage.tsx"),
      "utf8",
    );
    assert.doesNotMatch(
      page,
      /patchUserProfile|uploadUserProfilePhoto|deleteUserProfilePhoto/,
    );
    assert.doesNotMatch(page, /NativeCheckboxControl|whatsappSource/);
    assert.doesNotMatch(page, /CommercialTextField/);
    assert.doesNotMatch(page, /editingBadge/);
  });

  it("avatar permite ampliar a foto no perfil", () => {
    const page = readFileSync(
      join(src, "features/users/UserProfilePage.tsx"),
      "utf8",
    );
    assert.match(page, /previewAriaLabel/);
    assert.match(page, /USER_ACCESS_COPY\.enlargePhoto/);
    assert.match(
      readFileSync(join(src, "content/userAccess.json"), "utf8"),
      /"enlargePhoto"/,
    );
  });

  it("hero usa só nome/cargo e badge Portal Comercial", () => {
    const page = readFileSync(
      join(src, "features/users/UserProfilePage.tsx"),
      "utf8",
    );
    const copy = readFileSync(join(src, "content/userAccess.json"), "utf8");
    assert.match(copy, /"appBadge": "Portal Comercial"/);
    assert.match(page, /USER_ACCESS_COPY\.appBadge/);
    assert.doesNotMatch(page, /label=["']Commercial["']/);
    assert.match(page, /directoryUserLabelOrFallback\(\{ name: profile\.name \}\)/);
    assert.match(page, /heroDescription = \(profile\?\.job_title/);
    assert.doesNotMatch(page, /heroDescription = \[profile\.email/);
  });

  it("identidade exibe contatos E.164 e mantém atalhos de contato/tarefa", () => {
    const page = readFileSync(
      join(src, "features/users/UserProfilePage.tsx"),
      "utf8",
    );
    const copy = readFileSync(join(src, "content/userAccess.json"), "utf8");
    const day = readFileSync(join(src, "features/my-day/MyDayPage.tsx"), "utf8");
    assert.match(page, /phone: profile\.phone_e164/);
    assert.match(page, /mobile: profile\.mobile_e164/);
    assert.match(page, /whatsapp: profile\.whatsapp_e164/);
    assert.match(page, /USER_ACCESS_COPY\.shortcutEmail/);
    assert.match(page, /USER_ACCESS_COPY\.shortcutCall/);
    assert.match(page, /USER_ACCESS_COPY\.shortcutWhatsapp/);
    assert.match(page, /USER_ACCESS_COPY\.shortcutAssignTask/);
    assert.match(page, /assignee_user_id=/);
    assert.match(page, /canAssignTaskToProfile/);
    assert.match(copy, /"shortcutAssignTask"/);
    assert.match(day, /assignee_user_id/);
    assert.match(day, /link\.assigneeUserId/);
  });

  it("compõe o perfil com o kit PortalUserProfilePage", () => {
    const page = readFileSync(
      join(src, "features/users/UserProfilePage.tsx"),
      "utf8",
    );
    assert.match(page, /createDashboardPortalUserProfilePage/);
    /** Layout de identidade/atalhos é do kit — sem CSS paralelo no MFE. */
    assert.doesNotMatch(
      page,
      /cm-user-profile__(grid|identity|identity-fields|meta-row|shortcuts|avatar|job|file-input)/,
    );
  });
});
