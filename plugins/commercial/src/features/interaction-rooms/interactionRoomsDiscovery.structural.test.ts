import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "../../..");

describe("interaction rooms discovery", () => {
  it("manifesto declara path EN interaction-rooms", () => {
    const manifest = JSON.parse(
      readFileSync(join(root, "commercial.manifest.json"), "utf8"),
    );
    const route = manifest.routes.find(
      (item) => item.path === "/apps/commercial/interaction-rooms",
    );
    expect(route).toBeTruthy();
    expect(route.label).toBe("Sala de interação");
    expect(route.showInMenu).toBe(false);
    expect(route.permission).toBe("commercial.access");
  });

  it("catálogo do hub inclui interaction_rooms em operations", () => {
    const source = readFileSync(
      join(root, "src/content/pluginRouteCatalog.ts"),
      "utf8",
    );
    expect(source).toMatch(/id: "interaction_rooms"/);
    expect(source).toMatch(/viewId: "interaction_rooms"/);
  });
});
