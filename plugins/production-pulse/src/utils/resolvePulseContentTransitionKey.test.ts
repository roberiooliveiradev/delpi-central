import { describe, expect, it } from "vitest";

import { resolvePulseContentTransitionKey } from "./resolvePulseContentTransitionKey";

describe("resolvePulseContentTransitionKey", () => {
  it("mantém a mesma key no hub Admin ao mudar filial (positivo)", () => {
    expect(
      resolvePulseContentTransitionKey({
        kind: "firmwareLinks",
        branch: "01",
      }),
    ).toBe("admin:hub");
    expect(
      resolvePulseContentTransitionKey({
        kind: "firmwareLinks",
        branch: "02",
      }),
    ).toBe("admin:hub");
  });

  it("muda key entre Admin e Operador (irmão)", () => {
    expect(
      resolvePulseContentTransitionKey({
        kind: "firmwareLinks",
        branch: "01",
      }),
    ).toBe("admin:hub");
    expect(
      resolvePulseContentTransitionKey({
        kind: "operatorHub",
        branch: "01",
        anchorType: "",
        search: "",
      }),
    ).toBe("operator:hub:01");
  });

  it("muda key entre passos do operador (negativo: não colapsa tudo em operator)", () => {
    expect(
      resolvePulseContentTransitionKey({
        kind: "operatorPicker",
        placementKey: "wc:01:CT-35",
        branch: "01",
      }),
    ).toBe("operator:picker:01:wc:01:CT-35");
    expect(
      resolvePulseContentTransitionKey({
        kind: "operatorDevice",
        deviceId: "dev-1",
        branch: "01",
        placementKey: "wc:01:CT-35",
      }),
    ).toBe("operator:device:01:dev-1");
  });
});
