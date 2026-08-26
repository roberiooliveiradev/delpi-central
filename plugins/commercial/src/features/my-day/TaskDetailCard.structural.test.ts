import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));

describe("TaskDetailCard layout", () => {
  it("usa corpo rico no topo e mentions da mensagem de origem", () => {
    const source = readFileSync(join(dir, "TaskDetailCard.tsx"), "utf8");
    expect(source).toMatch(/CommercialMessageBodyReadonly/);
    expect(source).toMatch(/source_message_mentions/);
    expect(source).toMatch(/cm-task-detail-card__prose/);
    expect(source).toMatch(/attachmentIdsInMarkdown/);
    expect(source).toMatch(/TaskAttachmentsBlock/);
    expect(source).not.toMatch(/Observação/);
  });
});
