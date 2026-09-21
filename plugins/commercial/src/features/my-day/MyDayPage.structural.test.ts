import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const dir = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(join(dir, "MyDayPage.tsx"), "utf8");

describe("MyDayPage shared task chrome", () => {
  it("usa o editor compartilhado sem mudar o owner comercial", () => {
    expect(source).toMatch(/TaskWorkspacePage/);
    expect(source).toMatch(/TaskEditorFrame/);
    expect(source).toMatch(/TaskSearchField/);
    expect(source).toMatch(/TaskEmptyState/);
    expect(source).toMatch(/commercialTaskMatchesQuery/);
    expect(source).toMatch(/createTask\(/);
    expect(source).toMatch(/updateTask\(/);
    expect(source).toMatch(/completeTask\(/);
    expect(source).toMatch(/from ["']\.\.\/\.\.\/api\/worklistApi["']/);
    expect(source).not.toMatch(/transformometro-api|tm_tasks|SharedTaskStore/);
  });
});
