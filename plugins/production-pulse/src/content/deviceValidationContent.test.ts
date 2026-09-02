import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  LIVE_UI_REFRESH_MIN_MS,
  NAME_MAX_LENGTH,
  POLL_INTERVAL_DEFAULT_MS,
  POLL_INTERVAL_MAX_MS,
  POLL_INTERVAL_MIN_MS,
} from "./deviceValidationContent";

const here = dirname(fileURLToPath(import.meta.url));
const apiContentPath = join(
  here,
  "../../../../production-pulse-api/production_pulse_app/content/device_validation_content.json",
);

describe("deviceValidationContent", () => {
  it("espelha limites de pollIntervalMs da API", () => {
    const apiContent = JSON.parse(readFileSync(apiContentPath, "utf8")) as {
      limits?: {
        pollIntervalMs?: { min?: number; max?: number; default?: number };
        liveUiRefreshMs?: { min?: number };
        nameMaxLength?: number;
      };
    };
    expect(POLL_INTERVAL_MIN_MS).toBe(apiContent.limits?.pollIntervalMs?.min);
    expect(POLL_INTERVAL_MAX_MS).toBe(apiContent.limits?.pollIntervalMs?.max);
    expect(POLL_INTERVAL_DEFAULT_MS).toBe(apiContent.limits?.pollIntervalMs?.default);
    expect(LIVE_UI_REFRESH_MIN_MS).toBe(apiContent.limits?.liveUiRefreshMs?.min);
    expect(NAME_MAX_LENGTH).toBe(apiContent.limits?.nameMaxLength);
  });
});
