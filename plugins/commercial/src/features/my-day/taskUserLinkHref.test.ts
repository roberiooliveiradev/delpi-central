import { describe, expect, it } from "vitest";

import { profileLinkTitle } from "../../content/entityLinkHints";
import { buildUserProfileHref } from "../../app/pluginNavigation";

describe("E3.S2 profile href surfaces", () => {
  it("gera href de perfil com returnTo", () => {
    const href = buildUserProfileHref("u1", {
      basePath: "/apps/commercial",
      returnNav: { returnTo: "/apps/commercial/my-day", returnLabel: "Minhas tarefas" },
    });
    expect(href).toContain("/users/u1");
    expect(href).toContain("returnTo=");
    expect(profileLinkTitle("Ana")).toBe("Abrir perfil de Ana");
  });
});
