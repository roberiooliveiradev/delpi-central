import { describe, expect, it } from "vitest";

import { ProductionPulseRequestError } from "../api/httpClient";
import {
  isOperationalNoticeOnly,
  resolveProductionPulseError,
} from "./apiErrors";

describe("resolveProductionPulseError", () => {
  it("maps openTargetExists to a single notice-shaped payload", () => {
    const resolved = resolveProductionPulseError(
      new ProductionPulseRequestError(
        "O dispositivo já possui uma atualização OTA em andamento.",
        409,
        "openTargetExists",
      ),
    );
    expect(resolved.surface).toBe("notice");
    expect(resolved.title).toBe("Atualização já em andamento");
    expect(resolved.message).toContain("já possui");
    expect(resolved.actionLabel).toBe("Ver atualização");
    expect(resolved.code).toBe("openTargetExists");
    expect(isOperationalNoticeOnly(resolved)).toBe(true);
  });

  it("does not treat operational OTA errors as structural StateBox", () => {
    const resolved = resolveProductionPulseError(
      new ProductionPulseRequestError("x", 422, "noEligibleDevices"),
    );
    expect(resolved.surface).toBe("notice");
    expect(isOperationalNoticeOnly(resolved)).toBe(true);
  });

  it("maps API unavailable to structural", () => {
    const resolved = resolveProductionPulseError(
      new ProductionPulseRequestError("down", 503, "api_unavailable"),
    );
    expect(resolved.surface).toBe("structural");
  });
});
