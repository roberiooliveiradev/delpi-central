import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import {
  DEVICE_FORM_VALIDATION_ERROR_CODES,
  DEVICE_FORM_VALIDATION_MESSAGES,
  POLL_INTERVAL_MAX_SECONDS,
  POLL_INTERVAL_MIN_SECONDS,
} from "./deviceValidationContent";

describe("deviceValidationContent sync", () => {
  it("mirrors production-pulse-api device_validation_content.json limits and patterns", () => {
    const here = dirname(fileURLToPath(import.meta.url));
    const apiJsonPath = resolve(
      here,
      "../../../../production-pulse-api/production_pulse_app/content/device_validation_content.json",
    );
    const mfeJsonPath = resolve(here, "./device_validation_content.json");
    const apiContent = JSON.parse(readFileSync(apiJsonPath, "utf8")) as {
      limits?: { pollIntervalSeconds?: { min?: number; max?: number }; nameMaxLength?: number };
      patterns?: { ipv4?: string };
      validBranches?: string[];
    };
    const mfeContent = JSON.parse(readFileSync(mfeJsonPath, "utf8")) as typeof apiContent;

    expect(mfeContent).toEqual(apiContent);
    expect(POLL_INTERVAL_MIN_SECONDS).toBe(apiContent.limits?.pollIntervalSeconds?.min);
    expect(POLL_INTERVAL_MAX_SECONDS).toBe(apiContent.limits?.pollIntervalSeconds?.max);
  });

  it("mirrors production-pulse-api validation error messages used by the form", () => {
    const here = dirname(fileURLToPath(import.meta.url));
    const apiMessagesPath = resolve(
      here,
      "../../../../production-pulse-api/production_pulse_app/content/device_api_messages.json",
    );
    const catalog = JSON.parse(readFileSync(apiMessagesPath, "utf8")) as {
      validationErrors?: Record<string, string>;
    };
    const apiMessages = catalog.validationErrors ?? {};

    for (const code of DEVICE_FORM_VALIDATION_ERROR_CODES) {
      expect(DEVICE_FORM_VALIDATION_MESSAGES[code]).toBe(apiMessages[code]);
    }
  });
});
