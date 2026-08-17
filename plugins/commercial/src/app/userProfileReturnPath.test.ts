import { describe, expect, it } from "vitest";

import { resolvePagePathBack } from "./commercialNavigationReturn";

describe("UserProfile Path returnTo", () => {
  it("resolvePagePathBack usa returnTo da query", () => {
    const back = resolvePagePathBack(
      "?returnTo=%2Fapps%2Fcommercial%2Fmy-day&returnLabel=Minhas%20tarefas",
      { href: "/apps/commercial", label: "Portal Comercial" },
      "/apps/commercial",
    );
    expect(back.href).toBe("/apps/commercial/my-day");
    expect(back.label).toBe("Minhas tarefas");
  });
});
