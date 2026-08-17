import { describe, expect, it } from "vitest";

import {
  buildAnalyticsOpportunityDetailHref,
  buildCustomerDetailHref,
  buildCustomerInvoiceDetailHref,
  buildCustomerOrderDetailHref,
  buildOpenOrderLineDetailPath,
  buildOpenOrderOpDetailPath,
  buildProposalDetailHref,
  buildUserProfileHref,
} from "../app/pluginNavigation";
import {
  accountLinkTitle,
  invoiceLinkTitle,
  openOrderLineLinkTitle,
  opPageLinkTitle,
  opportunityLinkTitle,
  orderLinkTitle,
  portfolioLinkTitle,
  proposalLinkTitle,
} from "../content/entityLinkHints";

describe("entity href builders + hints", () => {
  const basePath = "/apps/commercial";
  const returnNav = {
    returnTo: "/apps/commercial/open-orders",
    returnLabel: "Meus pedidos",
  };

  it("Conta com returnTo", () => {
    const href = buildCustomerDetailHref("000001", "01", {
      basePath,
      search: "",
      returnNav,
    });
    expect(href).toContain("/customers/000001/01");
    expect(href).toContain("returnTo=");
    expect(href).toContain("returnLabel=");
    expect(accountLinkTitle("WEG")).toBe("Abrir conta de WEG");
  });

  it("Perfil com returnTo", () => {
    const href = buildUserProfileHref("u-1", { basePath, returnNav });
    expect(href).toContain("/users/u-1");
    expect(href).toContain("returnTo=");
  });

  it("pedido da Conta, NF, proposta e OV", () => {
    expect(
      buildCustomerOrderDetailHref("000001", "01", "01", "102942", {
        basePath,
        returnNav,
      }),
    ).toContain("/orders/01/102942");
    expect(orderLinkTitle("102942", "01")).toBe("Abrir pedido 102942/01");

    expect(
      buildCustomerInvoiceDetailHref("000001", "01", "01", "123", "1", {
        basePath,
        returnNav,
      }),
    ).toContain("/outbound-invoices/01/123/1");
    expect(invoiceLinkTitle("123")).toBe("Abrir NF 123");

    expect(buildProposalDetailHref("P-1", { basePath, returnNav })).toContain(
      "/proposals/P-1",
    );
    expect(proposalLinkTitle("P-1")).toBe("Abrir proposta P-1");

    expect(
      buildAnalyticsOpportunityDetailHref("OV99", { basePath }),
    ).toContain("OV99");
    expect(opportunityLinkTitle("OV99")).toBe("Abrir OV OV99");
  });

  it("linha e OP de pedidos em aberto", () => {
    const line = buildOpenOrderLineDetailPath(
      basePath,
      "01",
      "102942",
      "01",
    );
    expect(line).toBe("/apps/commercial/open-orders/01/102942/01");
    expect(openOrderLineLinkTitle("102942", "01")).toBe(
      "Abrir detalhe do pedido 102942/01",
    );

    const op = buildOpenOrderOpDetailPath(
      basePath,
      "01",
      "102942",
      "01",
      "00118901001",
    );
    expect(op).toContain("/op/00118901001");
    expect(opPageLinkTitle("00118901001")).toBe(
      "Abrir página da OP 00118901001",
    );
    expect(portfolioLinkTitle("Carteira Sul")).toBe("Abrir carteira Carteira Sul");
  });
});
