#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const root = join(dirname(fileURLToPath(import.meta.url)), "../../..");
const src = join(root, "src");

describe("MyDay task groups (E6.S3)", () => {
  it("form e card cobrem grupos e concluída por", () => {
    const page = readFileSync(join(src, "features/my-day/MyDayPage.tsx"), "utf8");
    assert.match(page, /assignee_group_ids/);
    assert.match(page, /CommercialMultiSelectField/);
    assert.match(page, /listCommercialGroups/);
    assert.match(page, /completedByValue/);
    assert.match(page, /groupsValue/);
    assert.match(page, /completed_by_user_id/);

    const card = readFileSync(join(src, "features/my-day/TaskDetailCard.tsx"), "utf8");
    assert.match(card, /Concluída por/);
    assert.match(card, /completedByValue/);
    assert.match(card, /groupsValue/);
  });
});
