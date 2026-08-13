import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const src = join(dirname(fileURLToPath(import.meta.url)), "../..");

describe("user profile self-only + expand photo", () => {
  it("canEdit=isSelf e avatar permite ampliar fora do modo edição", () => {
    const page = readFileSync(
      join(src, "features/users/UserProfilePage.tsx"),
      "utf8",
    );
    assert.match(page, /const canEdit = isSelf/);
    assert.doesNotMatch(page, /canEdit = isSelf \|\|/);
    assert.match(page, /previewable=\{Boolean\(photoObjectUrl\)\}/);
    assert.match(page, /USER_ACCESS_COPY\.enlargePhoto/);
    assert.match(
      readFileSync(join(src, "content/userAccess.json"), "utf8"),
      /"enlargePhoto"/,
    );
  });
});
