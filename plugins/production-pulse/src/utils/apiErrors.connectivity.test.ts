import { describe, expect, it } from "vitest";

import { ProductionPulseRequestError } from "../api/httpClient";
import { isDeviceConnectivityError } from "./apiErrors";

describe("device connectivity error classification", () => {
  it("treats 422 timeout as connectivity", () => {
    const err = new ProductionPulseRequestError("Dispositivo sem resposta.", 422, "timeout");
    expect(isDeviceConnectivityError(err)).toBe(true);
  });

  it("treats 422 network_error as connectivity", () => {
    const err = new ProductionPulseRequestError("Falha de rede.", 422, "network_error");
    expect(isDeviceConnectivityError(err)).toBe(true);
  });

  it("does not treat validation_error as connectivity", () => {
    const err = new ProductionPulseRequestError("Inválido.", 422, "validation_error");
    expect(isDeviceConnectivityError(err)).toBe(false);
  });

  it("does not treat infra 503 as connectivity", () => {
    const err = new ProductionPulseRequestError("Indisponível.", 503, "unavailable");
    expect(isDeviceConnectivityError(err)).toBe(false);
  });
});
