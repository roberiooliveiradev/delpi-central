import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const src = join(dirname(fileURLToPath(import.meta.url)), "../..");

describe("user profile self-only + expand photo", () => {
  it("isSelf + onEditSelf abrem o /profile do host — chrome self é do kit", () => {
    const page = readFileSync(
      join(src, "features/users/UserProfilePage.tsx"),
      "utf8",
    );
    assert.match(page, /isSelf=\{isSelf\}/);
    assert.match(page, /onEditSelf=/);
    assert.match(page, /HOST_SELF_PROFILE_PATH/);
    assert.match(page, /navigateHostPath/);
    assert.doesNotMatch(page, /canEdit = isSelf/);
    assert.doesNotMatch(page, /badgeSelf/);
    assert.doesNotMatch(page, /editIdentity/);
    assert.doesNotMatch(page, /identityHostNote/);
    assert.doesNotMatch(page, /showEmptyFields/);
    assert.doesNotMatch(page, /density:\s*"comfortable"/);
    assert.doesNotMatch(page, /Editar identidade|Editar perfil/);
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

  it("hero usa eyebrow Portal Comercial e cargo no supporting — badge Você é do kit", () => {
    const page = readFileSync(
      join(src, "features/users/UserProfilePage.tsx"),
      "utf8",
    );
    const copy = readFileSync(join(src, "content/userAccess.json"), "utf8");
    assert.match(copy, /"appBadge": "Portal Comercial"/);
    assert.match(page, /eyebrow: USER_ACCESS_COPY\.appBadge/);
    assert.match(page, /contextBadges=/);
    assert.match(page, /formatPortfoliosCount/);
    assert.doesNotMatch(page, /USER_ACCESS_COPY\.badgeSelf/);
    assert.doesNotMatch(page, /label=\{USER_ACCESS_COPY\.appBadge\}/);
    assert.doesNotMatch(page, /aboutTitle|aboutBody/);
    assert.match(page, /directoryUserLabelOrFallback\(\{ name: profile\.name \}\)/);
    assert.match(page, /heroDescription =/);
    assert.match(page, /profile\?\.job_title/);
    assert.match(page, /profile\?\.email/);
  });

  it("CTA Editar só via onEditSelf do kit — sem actions/note manuais no Hero/Identity", () => {
    const page = readFileSync(
      join(src, "features/users/UserProfilePage.tsx"),
      "utf8",
    );
    assert.match(page, /onEditSelf=/);
    assert.doesNotMatch(page, /actions:\s*canEdit/);
    assert.doesNotMatch(page, /note:\s*USER_ACCESS_COPY\.identityHostNote/);
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
    assert.doesNotMatch(
      page,
      /cm-user-profile__(grid|identity|identity-fields|meta-row|shortcuts|avatar|job|file-input)/,
    );
  });
});
