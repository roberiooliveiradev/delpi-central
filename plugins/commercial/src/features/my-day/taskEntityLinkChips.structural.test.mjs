import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

const src = join(dirname(fileURLToPath(import.meta.url)));

describe("task entity link chips avatars", () => {
  it("chips aceitam avatar e subtitle; card usa assignedByValue", () => {
    const chips = readFileSync(join(src, "TaskEntityLinkChips.tsx"), "utf8");
    assert.match(chips, /avatar\?:/);
    assert.match(chips, /subtitle\?:/);
    assert.match(chips, /cm-task-link-chip__avatar/);

    const card = readFileSync(join(src, "TaskDetailCard.tsx"), "utf8");
    assert.match(card, /assignedByValue/);
    assert.doesNotMatch(card, /assignedByLabel/);

    const page = readFileSync(join(src, "MyDayPage.tsx"), "utf8");
    assert.match(page, /TaskUserChipAvatar/);
    assert.match(page, /CustomerAvatar/);
    assert.match(page, /assignedByValue=/);
  });
});
