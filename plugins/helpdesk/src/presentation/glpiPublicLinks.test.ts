import { describe, expect, it } from "vitest";
import { GLPI_PUBLIC_ORIGIN, glpiConsoleUrl, glpiTicketFormUrl } from "./glpiPublicLinks";

describe("glpiConsoleUrl", () => {
  it("monta a entrada SAML do console", () => {
    expect(glpiConsoleUrl()).toBe(`${GLPI_PUBLIC_ORIGIN}/?samlIdpId=1`);
  });
});

describe("glpiTicketFormUrl", () => {
  it("monta SSO + redirect para o formulário do chamado", () => {
    const url = glpiTicketFormUrl(1122);
    expect(url.startsWith(`${GLPI_PUBLIC_ORIGIN}/?samlIdpId=1&redirect=`)).toBe(true);
    expect(decodeURIComponent(url.split("redirect=")[1]!)).toBe("/front/ticket.form.php?id=1122");
  });

  it("sem id válido cai só na entrada SAML", () => {
    expect(glpiTicketFormUrl(0)).toBe(glpiConsoleUrl());
    expect(glpiTicketFormUrl(-3)).toBe(glpiConsoleUrl());
  });
});
