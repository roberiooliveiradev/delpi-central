import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const dir = dirname(fileURLToPath(import.meta.url));
const source = readFileSync(join(dir, "MyTasksPage.tsx"), "utf8");

describe("MyTasksPage", () => {
  it("projeta pending-signatures no chrome compartilhado, sem task store", () => {
    expect(source).toMatch(/pendingAtas/);
    expect(source).toMatch(/projectPendingSignatureTasks/);
    expect(source).toMatch(/LoadingActivityCard/);
    expect(source).toMatch(/EmptyState/);
    expect(source).toMatch(/DataTableSection/);
    expect(source).toMatch(/Nenhuma tarefa pendente no momento/);
    expect(source).not.toMatch(/from ["']@delpi\/commercial/);
    expect(source).not.toMatch(/INSERT INTO/);
    expect(source).not.toMatch(/dueDate|priority/);
  });
});
