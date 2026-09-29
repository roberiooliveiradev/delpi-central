import { afterEach, describe, expect, it, vi } from "vitest";

import { configureHttpClient, httpGet } from "./httpClient";

afterEach(() => vi.unstubAllGlobals());

describe("Delpi MES HTTP client", () => {
  it("uses host JWT, caller id and unwraps the envelope", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ success: true, message: "OK", data: { branch: "01" } }), { status: 200, headers: { "content-type": "application/json" } }));
    vi.stubGlobal("fetch", fetchMock);
    configureHttpClient(() => "host-token");
    await expect(httpGet<{ branch: string }>("/monitoring?branch=01")).resolves.toEqual({ branch: "01" });
    const [, options] = fetchMock.mock.calls[0];
    expect(options.headers.Authorization).toBe("Bearer host-token");
    expect(options.headers["X-Delpi-Caller-App"]).toBe("delpi-mes");
  });

  it("forwards AbortSignal and exposes a safe error", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ success: false, message: "Sem permissão", data: null }), { status: 403 }));
    vi.stubGlobal("fetch", fetchMock);
    const controller = new AbortController();
    await expect(httpGet("/monitoring?branch=01", { signal: controller.signal })).rejects.toMatchObject({ status: 403, message: "Sem permissão" });
    expect(fetchMock.mock.calls[0][1].signal).toBe(controller.signal);
  });
});
