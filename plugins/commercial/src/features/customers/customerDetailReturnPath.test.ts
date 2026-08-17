import { describe, expect, it } from "vitest";

import { resolvePagePathBack } from "../../app/commercialNavigationReturn";

describe("Customer detail Path returnTo", () => {
  it("prioriza returnTo sobre lista Minha carteira", () => {
    const back = resolvePagePathBack(
      "?returnTo=%2Fapps%2Fcommercial%2Fopen-orders&returnLabel=Meus%20pedidos",
      {
        href: "/apps/commercial/customers",
        label: "Minha carteira",
      },
      "/apps/commercial",
    );
    expect(back.href).toBe("/apps/commercial/open-orders");
    expect(back.label).toBe("Meus pedidos");
  });
});
