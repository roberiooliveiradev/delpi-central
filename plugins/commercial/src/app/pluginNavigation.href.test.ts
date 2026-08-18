import { describe, expect, it } from "vitest";

import {
  buildCustomerDetailHref,
  buildOverviewKpiHref,
  buildProductHref,
  buildUserProfileHref,
} from "./pluginNavigation";

describe("buildUserProfileHref / buildCustomerDetailHref", () => {
  it("anexa returnTo no perfil", () => {
    const href = buildUserProfileHref("user-1", {
      basePath: "/apps/commercial",
      returnNav: {
        returnTo: "/apps/commercial/my-day",
        returnLabel: "Meu Dia",
      },
    });
    expect(href).toContain("/apps/commercial/users/user-1");
    expect(href).toContain("returnTo=");
    expect(href).toContain("returnLabel=Meu");
  });

  it("anexa returnTo na conta", () => {
    const href = buildCustomerDetailHref("0001", "01", {
      basePath: "/apps/commercial",
      search: "",
      returnNav: {
        returnTo: "/apps/commercial/analytics/otd",
        returnLabel: "OTD",
      },
    });
    expect(href).toContain("/apps/commercial/customers/0001/01");
    expect(href).toContain("returnTo=");
  });
});

describe("buildOverviewKpiHref / buildProductHref", () => {
  it("aponta kpi para a Visão geral", () => {
    expect(buildOverviewKpiHref("ROL", { basePath: "/apps/commercial" })).toBe(
      "/apps/commercial/overview?kpi=ROL",
    );
  });

  it("aponta produto para a Visão geral até existir ficha", () => {
    expect(buildProductHref("90AAAA01", { basePath: "/apps/commercial" })).toBe(
      "/apps/commercial/overview?product=90AAAA01",
    );
    expect(buildProductHref("  ")).toBeNull();
  });
});
