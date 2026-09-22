import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { parseTransformometroPath } from "./routeParser";
import { buildTransformometroUserPath } from "./userProfileLinks";

const dir = dirname(fileURLToPath(import.meta.url));

describe("Transforma+ user profile routes", () => {
  it("parseia /apps/transformometro/users/:id", () => {
    const route = parseTransformometroPath(
      "/apps/transformometro/users/c9b8d8dd-a1cf-4252-a5c0-426214505f89",
    );
    expect(route.view).toBe("user");
    expect(route.userId).toBe("c9b8d8dd-a1cf-4252-a5c0-426214505f89");
  });

  it("buildTransformometroUserPath gera path do portal", () => {
    expect(buildTransformometroUserPath("u-1")).toBe(
      "/apps/transformometro/users/u-1",
    );
    expect(buildTransformometroUserPath("")).toBeNull();
  });

  it("TopBar e App usam perfil do portal (não só /profile host)", () => {
    const topBar = readFileSync(
      join(dir, "../components/PortalTopBarUserIdentity.tsx"),
      "utf8",
    );
    const app = readFileSync(join(dir, "../App.tsx"), "utf8");
    const links = readFileSync(join(dir, "userProfileLinks.ts"), "utf8");
    expect(topBar).toMatch(/buildTransformometroUserPath/);
    expect(topBar).toMatch(/navigateTransformometroUserProfile/);
    expect(topBar).not.toMatch(/HOST_SELF_PROFILE_PATH/);
    expect(app).toMatch(/PersonDirectoryPage/);
    expect(app).toMatch(/route\.view === "user"/);
    expect(links).toMatch(/navigateTransformometro\(path\)/);
    expect(links).not.toMatch(/navigateHostPath/);
  });

  it("PersonDirectoryPage tem atalhos e Editar → /profile para o próprio", () => {
    const page = readFileSync(
      join(dir, "../ui/pages/PersonDirectoryPage.tsx"),
      "utf8",
    );
    expect(page).toMatch(/Editar perfil/);
    expect(page).toMatch(/HOST_SELF_PROFILE_PATH/);
    expect(page).toMatch(/navigateHostPath/);
    expect(page).toMatch(/Minhas tarefas/);
    expect(page).toMatch(/isSelf === true/);
  });

  it("InteractionRooms liga autores/participantes ao perfil do portal", () => {
    const source = readFileSync(
      join(dir, "../ui/pages/InteractionRoomsPage.tsx"),
      "utf8",
    );
    expect(source).toMatch(/authorHref/);
    expect(source).toMatch(/buildTransformometroUserPath/);
    expect(source).toMatch(/navigateTransformometroUserProfile/);
  });
});
