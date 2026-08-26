import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = dirname(fileURLToPath(import.meta.url));

describe("AdministrationGroupsPage mural entry", () => {
  it("expõe ação para abrir mural do grupo", () => {
    const source = readFileSync(join(dir, "AdministrationGroupsPage.tsx"), "utf8");
    expect(source).toMatch(/openGroupWall/);
    expect(source).toMatch(/resolveInteractionRoom/);
    expect(source).toMatch(/group_id:\s*group\.id/);
  });
});
