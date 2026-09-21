import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const dir = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(join(dir, "MyTasksPage.tsx"), "utf8");

describe("MyTasksPage", () => {
  it("consome chrome compartilhado e a projeção unificada, sem store local", () => {
    expect(source).toMatch(/listMyTaskItems/);
    expect(source).toMatch(/TaskItemsTable/);
    expect(source).toMatch(/TaskEditorFrame/);
    expect(source).toMatch(/UserDirectoryPicker/);
    expect(source).toMatch(/LoadingActivityCard/);
    expect(source).toMatch(/EmptyState/);
    expect(source).toMatch(/Nenhuma tarefa pendente no momento/);
    expect(source).toMatch(/Nova tarefa/);
    expect(source).not.toMatch(/from ["']@delpi\/commercial/);
    expect(source).not.toMatch(/INSERT INTO/);
    expect(source).not.toMatch(/pendingAtas/);
    expect(source).not.toMatch(/createTaskEngine|SharedTaskStore/);
  });
});
