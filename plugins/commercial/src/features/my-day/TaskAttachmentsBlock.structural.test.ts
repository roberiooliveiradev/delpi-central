import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));

describe("TaskAttachmentsBlock inline dedupe", () => {
  it("filters excludeAttachmentIds from the strip list", () => {
    const source = readFileSync(join(dir, "TaskAttachmentsBlock.tsx"), "utf8");
    expect(source).toMatch(/excludeAttachmentIds/);
    expect(source).toMatch(/visibleItems/);
    expect(source).toMatch(/excludeSet/);
  });
});
