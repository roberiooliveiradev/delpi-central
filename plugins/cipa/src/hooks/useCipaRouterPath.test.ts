import { describe, expect, it } from "vitest";

import { parseCipaRoute } from "./useCipaRouterPath";

describe("parseCipaRoute", () => {
  it("home do módulo", () => {
    expect(parseCipaRoute("/apps/cipa")).toEqual({ kind: "home" });
  });

  it("lista por filial", () => {
    expect(parseCipaRoute("/apps/cipa/filial-01")).toEqual({
      kind: "list",
      unitCode: "01",
    });
  });

  it("nova ata", () => {
    expect(parseCipaRoute("/apps/cipa/filial-02/minutes/new")).toEqual({
      kind: "new",
      unitCode: "02",
    });
  });

  it("assinatura", () => {
    expect(parseCipaRoute("/apps/cipa/filial-01/minutes/abc/sign")).toEqual({
      kind: "sign",
      unitCode: "01",
      minuteId: "abc",
    });
  });
});
