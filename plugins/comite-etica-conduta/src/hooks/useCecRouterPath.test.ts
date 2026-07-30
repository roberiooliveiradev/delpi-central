import { describe, expect, it } from "vitest";

import { CEC_CORPORATE_UNIT, parseCecRoute } from "./useCecRouterPath";

describe("parseCecRoute", () => {
  it("lista de atas (home e /atas)", () => {
    expect(parseCecRoute("/apps/comite-etica-conduta")).toEqual({
      kind: "list",
      unitCode: CEC_CORPORATE_UNIT,
    });
    expect(parseCecRoute("/apps/comite-etica-conduta/atas")).toEqual({
      kind: "list",
      unitCode: CEC_CORPORATE_UNIT,
    });
  });

  it("nova ata", () => {
    expect(parseCecRoute("/apps/comite-etica-conduta/atas/new")).toEqual({
      kind: "new",
      unitCode: CEC_CORPORATE_UNIT,
    });
  });

  it("assinatura", () => {
    expect(parseCecRoute("/apps/comite-etica-conduta/atas/abc/sign")).toEqual({
      kind: "sign",
      unitCode: CEC_CORPORATE_UNIT,
      minuteId: "abc",
    });
  });

  it("perfil de assinatura pessoal", () => {
    expect(parseCecRoute("/apps/comite-etica-conduta/minha-assinatura")).toEqual({
      kind: "mySignature",
    });
  });

  it("membros", () => {
    expect(parseCecRoute("/apps/comite-etica-conduta/membros")).toEqual({
      kind: "members",
      unitCode: CEC_CORPORATE_UNIT,
    });
  });

  it("pendências", () => {
    expect(parseCecRoute("/apps/comite-etica-conduta/atas/pending")).toEqual({
      kind: "pending",
    });
  });

  it("compat deep link legado estilo filial", () => {
    expect(parseCecRoute("/apps/comite-etica-conduta/filial-01/minutes/abc/sign")).toEqual({
      kind: "sign",
      unitCode: CEC_CORPORATE_UNIT,
      minuteId: "abc",
    });
  });
});
