import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "../../..");
const src = join(root, "src");

describe("Conta header avatar upload/remove", () => {
  it("CustomerDetailHeader tem upload/remove e chama APIs de avatar", () => {
    const header = readFileSync(
      join(src, "features/customers/components/CustomerDetailHeader.tsx"),
      "utf8",
    );
    assert.match(header, /upsertCustomerAvatar/);
    assert.match(header, /deleteCustomerAvatar/);
    assert.match(header, /type="file"/);
    assert.match(header, /Trocar logo/);
    assert.match(header, /Remover logo/);
    assert.match(header, /onAvatarChanged/);
    assert.match(header, /avatarRefreshKey/);
  });

  it("CustomerDetailPage refresca audit após mudança de avatar", () => {
    const page = readFileSync(
      join(src, "features/customers/pages/CustomerDetailPage.tsx"),
      "utf8",
    );
    assert.match(page, /onAvatarChanged/);
    assert.match(page, /avatarRefreshKey=\{contactsRefreshKey\}/);
    assert.match(page, /setContactsRefreshKey/);
  });

  it("CustomerAvatar aceita refreshKey para refetch do blob", () => {
    const avatar = readFileSync(
      join(src, "features/customers/components/CustomerAvatar.tsx"),
      "utf8",
    );
    assert.match(avatar, /refreshKey/);
    assert.match(avatar, /hasAvatar, refreshKey/);
  });
});
