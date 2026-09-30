import { afterEach, describe, expect, it, vi } from "vitest";

import {
  createDowntimeReason,
  listDowntimeReasons,
  setDowntimeReasonActive,
  updateDowntimeReason,
} from "./downtimeReasonsApi";
import { configureHttpClient } from "./httpClient";

const ok = (data: unknown) =>
  new Response(JSON.stringify({ success: true, message: "OK", data }), {
    status: 200,
    headers: { "content-type": "application/json" },
  });

afterEach(() => vi.unstubAllGlobals());

describe("downtimeReasonsApi", () => {
  it("lists the global catalog without a branch parameter", async () => {
    const fetchMock = vi.fn().mockResolvedValue(ok({ items: [] }));
    vi.stubGlobal("fetch", fetchMock);
    configureHttpClient(() => undefined);
    await expect(listDowntimeReasons()).resolves.toEqual({ items: [] });
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe("/apps/delpi-mes-api/registrations/downtime-reasons");
    expect(url).not.toContain("branch");
    expect(options.method).toBe("GET");
  });

  it("creates a reason with the create-only body", async () => {
    const fetchMock = vi.fn().mockResolvedValue(ok({ code: "material_shortage" }));
    vi.stubGlobal("fetch", fetchMock);
    const payload = {
      code: "material_shortage",
      label: "Falta de material",
      category: "material",
      requiresNote: false,
      sortOrder: 10,
    };
    await createDowntimeReason(payload);
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe("/apps/delpi-mes-api/registrations/downtime-reasons");
    expect(options.method).toBe("POST");
    const body = JSON.parse(options.body as string) as Record<string, unknown>;
    expect(body).toEqual(payload);
    expect(body).not.toHaveProperty("active");
    expect(body).not.toHaveProperty("defaultPlanned");
    expect(body).not.toHaveProperty("defaultCountsAsAvailabilityLoss");
  });

  it("updates a reason without code or active in the body", async () => {
    const fetchMock = vi.fn().mockResolvedValue(ok({ code: "material_shortage" }));
    vi.stubGlobal("fetch", fetchMock);
    const payload = { label: "Falta de material", category: "material", requiresNote: true, sortOrder: 12 };
    await updateDowntimeReason("material_shortage", payload);
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe("/apps/delpi-mes-api/registrations/downtime-reasons/material_shortage");
    expect(options.method).toBe("PUT");
    const body = JSON.parse(options.body as string) as Record<string, unknown>;
    expect(body).toEqual(payload);
    expect(body).not.toHaveProperty("code");
    expect(body).not.toHaveProperty("active");
    expect(body).not.toHaveProperty("createdAt");
    expect(body).not.toHaveProperty("updatedAt");
  });

  it("patches only the active flag on a URL-encoded code", async () => {
    const fetchMock = vi.fn().mockResolvedValue(ok({ code: "other" }));
    vi.stubGlobal("fetch", fetchMock);
    await setDowntimeReasonActive("other reason", false);
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe("/apps/delpi-mes-api/registrations/downtime-reasons/other%20reason/active");
    expect(options.method).toBe("PATCH");
    expect(JSON.parse(options.body as string)).toEqual({ active: false });
  });
});
