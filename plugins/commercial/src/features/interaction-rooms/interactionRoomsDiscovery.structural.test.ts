import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const pluginRoot = process.cwd();

describe("interaction rooms discovery", () => {
  it("manifesto declara path EN interaction-rooms", () => {
    const manifest = JSON.parse(
      readFileSync(join(pluginRoot, "commercial.manifest.json"), "utf8"),
    );
    const route = manifest.routes.find(
      (item: { path?: string }) => item.path === "/apps/commercial/interaction-rooms",
    );
    expect(route).toBeTruthy();
    expect(route.label).toBe("Sala de interação");
    expect(route.showInMenu).toBe(false);
    expect(route.permission).toBe("commercial.access");
  });

  it("catálogo do hub inclui interaction_rooms em operations", () => {
    const source = readFileSync(
      join(pluginRoot, "src/content/pluginRouteCatalog.ts"),
      "utf8",
    );
    expect(source).toMatch(/id: "interaction_rooms"/);
    expect(source).toMatch(/viewId: "interaction_rooms"/);
  });

  it("README documenta paths EN da sala (UI + HTTP § 3.21)", () => {
    const readme = readFileSync(join(pluginRoot, "README.md"), "utf8");
    expect(readme).toContain("/apps/commercial/interaction-rooms");
    expect(readme).toContain("/apps/commercial/interaction-rooms/:roomId");
    expect(readme).toContain("/apps/commercial-api/interaction-rooms");
    expect(readme).toContain("/interaction-rooms/resolve");
    expect(readme).toContain("/interaction-rooms/{room_id}/messages");
    expect(readme).toContain("/interaction-rooms/{room_id}/pins");
    expect(readme).toContain(
      "/interaction-rooms/{room_id}/messages/{message_id}/tasks",
    );
    expect(readme).toContain(
      "/interaction-rooms/{room_id}/messages/{message_id}/pin",
    );
    expect(readme).toContain("create_task_from_interaction_message");
    expect(readme).toContain("API-ROUTES.md");
    expect(readme).not.toMatch(/\/apps\/api-delpi.*interaction/);
  });
});
