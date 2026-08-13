#!/usr/bin/env node
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";

const root = join(dirname(fileURLToPath(import.meta.url)), "../../..");
const src = join(root, "src");

describe("MyDay task groups + XOR + anexos (E6.S3 / E10)", () => {
  it("form e card cobrem grupos e concluída por", () => {
    const page = readFileSync(join(src, "features/my-day/MyDayPage.tsx"), "utf8");
    assert.match(page, /assignee_group_ids/);
    assert.match(page, /CommercialMultiSelectField/);
    assert.match(page, /listCommercialGroups/);
    assert.match(page, /completedByValue/);
    assert.match(page, /groupsValue/);
    assert.match(page, /completed_by_user_id/);
    assert.match(page, /CommercialSegmentToggle/);
    assert.match(page, /assigneeMode/);
    assert.match(page, /taskAssigneeXor/);
    assert.match(page, /Usuários/);
    assert.match(page, /Grupos/);

    const card = readFileSync(join(src, "features/my-day/TaskDetailCard.tsx"), "utf8");
    assert.match(card, /Concluída por/);
    assert.match(card, /completedByValue/);
    assert.match(card, /groupsValue/);
  });

  it("create/edit usam AttachmentPreviewStrip manage; preview só leitura", () => {
    const page = readFileSync(join(src, "features/my-day/MyDayPage.tsx"), "utf8");
    assert.match(page, /CommercialAttachmentPreviewStrip/);
    assert.match(page, /mode="manage"/);
    assert.doesNotMatch(page, /CommercialAttachmentFileList/);

    const block = readFileSync(
      join(src, "features/my-day/TaskAttachmentsBlock.tsx"),
      "utf8",
    );
    assert.match(block, /CommercialAttachmentPreviewStrip/);
    assert.match(block, /mode="manage"/);
    assert.match(block, /mode="preview"/);
    assert.match(block, /onRemove/);
    assert.doesNotMatch(block, /CommercialAttachmentFileList/);

    const help = readFileSync(join(src, "content/helpTooltips.ts"), "utf8");
    assert.match(help, /taskAssigneeXor/);
    assert.match(help, /taskAttachment/);
    assert.match(help, /Exclusivo com Grupos|não os dois/);
  });
});
