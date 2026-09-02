import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { DEVICE_CONNECTIVITY_ERROR_CODES } from "../content/deviceApiMessages";

describe("deviceApiMessages sync", () => {
  it("mirrors production-pulse-api deviceConnectivity.codes", () => {
    const here = dirname(fileURLToPath(import.meta.url));
    const jsonPath = resolve(
      here,
      "../../../../production-pulse-api/production_pulse_app/content/device_api_messages.json",
    );
    const catalog = JSON.parse(readFileSync(jsonPath, "utf8")) as {
      deviceConnectivity?: { codes?: string[] };
    };
    const apiCodes = [...(catalog.deviceConnectivity?.codes ?? [])].sort();
    const mfeCodes = [...DEVICE_CONNECTIVITY_ERROR_CODES].sort();
    expect(mfeCodes).toEqual(apiCodes);
  });
});
