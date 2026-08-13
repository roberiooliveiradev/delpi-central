import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const src = join(dirname(fileURLToPath(import.meta.url)));

describe("task entity link chips avatars", () => {
  it("avatar fica dentro do badge; clique abre perfil/Conta", () => {
    const chips = readFileSync(join(src, "TaskEntityLinkChips.tsx"), "utf8");
    assert.match(chips, /cm-task-link-chip__avatar/);
    assert.match(chips, /delpi-ui-tag-chip cm-task-link-chip/);
    assert.match(chips, /onClick=\{item\.onOpen\}/);

    const userChip = readFileSync(join(src, "TaskUserLinkChip.tsx"), "utf8");
    assert.match(userChip, /previewable=\{false\}/);
    assert.match(userChip, /profile\.email/);
    assert.match(userChip, /navigateUserProfile|onOpen/);

    const page = readFileSync(join(src, "MyDayPage.tsx"), "utf8");
    assert.match(page, /TaskUserLinkChip/);
    assert.match(page, /previewable=\{false\}/);
    assert.match(page, /navigateUserProfile/);
    assert.match(page, /navigateCustomerDetail/);
  });
});
