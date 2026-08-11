import { describe, expect, it } from "vitest";

import { resolvePublicMenuUrl, suggestPublicToken, type MuralHub } from "./muralAcessosApi";

const hub: MuralHub = {
  id: "11111111-1111-4111-8111-111111111111",
  title: "Acessos DELPI",
  subtitle: "",
  publicToken: "mural",
  publicPath: "/p/mural-acessos/menu/mural",
  publicUrl: "/p/mural-acessos/menu/mural",
  qrUrl: "/apps/api-delpi/mural-acessos/hubs/11111111-1111-4111-8111-111111111111/qr.png",
};

describe("resolvePublicMenuUrl", () => {
  it("usa a origem do portal quando a API devolve path relativo", () => {
    expect(resolvePublicMenuUrl(hub)).toBe(`${window.location.origin}/p/mural-acessos/menu/mural`);
  });

  it("preserva URL absoluta da API", () => {
    expect(
      resolvePublicMenuUrl({
        ...hub,
        publicUrl: "https://portal.delpi.com.br/p/mural-acessos/menu/mural",
      }),
    ).toBe("https://portal.delpi.com.br/p/mural-acessos/menu/mural");
  });
});

describe("suggestPublicToken", () => {
  it("gera slug a partir do título", () => {
    expect(suggestPublicToken("RH - Qualidade")).toBe("rh-qualidade");
  });
});
