import { describe, expect, it } from "vitest";

import { ProductionPulseRequestError } from "../api/httpClient";
import {
  isApiUnavailableError,
  isDeviceConnectivityError,
  isDeviceConnectivityErrorCode,
  resolveDeviceActionError,
} from "./apiErrors";

describe("apiErrors", () => {
  it("recognizes device connectivity codes", () => {
    expect(isDeviceConnectivityErrorCode("network_error")).toBe(true);
    expect(isDeviceConnectivityErrorCode("validation_error")).toBe(false);
  });

  it("classifies 422 device connectivity using API message as-is", () => {
    const err = new ProductionPulseRequestError(
      "Mensagem canônica da API.",
      422,
      "timeout",
    );
    expect(isDeviceConnectivityError(err)).toBe(true);
    expect(resolveDeviceActionError(err, "fallback")).toEqual({
      kind: "device",
      message: "Mensagem canônica da API.",
    });
  });

  it("classifies legacy 502 with device code as device error", () => {
    const err = new ProductionPulseRequestError("Timeout no device.", 502, "timeout");
    expect(isDeviceConnectivityError(err)).toBe(true);
  });

  it("classifies gateway 502 without device code as infra", () => {
    const err = new ProductionPulseRequestError(
      "API Pulso de Produção indisponível.",
      502,
    );
    expect(isDeviceConnectivityError(err)).toBe(false);
    expect(isApiUnavailableError(err)).toBe(true);
    expect(resolveDeviceActionError(err, "fallback")).toEqual({
      kind: "infra",
      message: "API Pulso de Produção indisponível.",
    });
  });
});
