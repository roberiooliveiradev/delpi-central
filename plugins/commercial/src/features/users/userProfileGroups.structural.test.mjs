#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const root = join(dirname(fileURLToPath(import.meta.url)), "../../..");

describe("user profile groups (E8)", () => {
  it("DTO tipa groups[]", () => {
    const source = readFileSync(join(root, "src/api/userProfileApi.ts"), "utf8");
    assert.match(source, /UserProfileGroupDto/);
    assert.match(source, /groups\?:/);
  });

  it("página renderiza chips de Grupos somente leitura", () => {
    const source = readFileSync(
      join(root, "src/features/users/UserProfilePage.tsx"),
      "utf8",
    );
    assert.match(source, /USER_ACCESS_COPY\.groupsTitle/);
    assert.match(source, /profile\.groups/);
    assert.match(source, /CommercialStatusBadge/);
  });

  it("copy de grupos está no content", () => {
    const source = readFileSync(join(root, "src/content/userAccess.json"), "utf8");
    assert.match(source, /"groupsTitle"/);
    assert.match(source, /"groupsEmpty"/);
  });
});
