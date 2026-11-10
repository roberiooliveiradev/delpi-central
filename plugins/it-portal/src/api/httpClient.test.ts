import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, HTTP_ERROR_MESSAGES, apiGet, apiPost, apiUrl, configureHttpClient } from "./httpClient";

function jsonResponse(status: number, body: unknown) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("apiUrl", () => {
  it("targets only the portal BFF and skips empty params", () => {
    expect(apiUrl("/servers", { q: "", unit_code: "01", page: 2, archived: undefined })).toBe(
      "/apps/it-portal-api/servers?unit_code=01&page=2",
    );
  });

  it("repeats array params", () => {
    expect(apiUrl("/action-plans", { status: ["pending", "in_progress"] })).toBe(
      "/apps/it-portal-api/action-plans?status=pending&status=in_progress",
    );
  });
});

describe("request", () => {
  it("sends bearer token and caller header, unwrapping the envelope", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse(200, { success: true, message: "ok", data: { a: 1 } }));
    vi.stubGlobal("fetch", fetchMock);
    configureHttpClient(() => "token-123");

    await expect(apiGet("/apps/it-portal-api/dashboard")).resolves.toEqual({ a: 1 });
    const headers = fetchMock.mock.calls[0][1].headers as Record<string, string>;
    expect(headers.Authorization).toBe("Bearer token-123");
    expect(headers["X-Delpi-Caller-App"]).toBe("it-portal");
  });

  it("maps validation envelope to field errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(422, {
          success: false,
          message: "Dados inválidos.",
          data: { error: { code: "invalid_request", details: { fields: { hostname: "Hostname inválido." } } } },
        }),
      ),
    );
    const error = (await apiPost("/apps/it-portal-api/servers", {}).catch((e) => e)) as ApiError;
    expect(error).toBeInstanceOf(ApiError);
    expect(error.status).toBe(422);
    expect(error.code).toBe("invalid_request");
    expect(error.fieldErrors).toEqual({ hostname: "Hostname inválido." });
  });

  it("does not leak middleware english detail or gateway HTML", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(403, { detail: "Forbidden" })));
    await expect(apiGet("/x")).rejects.toMatchObject({ status: 403, message: HTTP_ERROR_MESSAGES[403] });

    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("<html>Bad Gateway</html>", { status: 502 })));
    await expect(apiGet("/x")).rejects.toMatchObject({ status: 502, message: HTTP_ERROR_MESSAGES.gateway });
  });

  it("reports network failure as status 0", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));
    await expect(apiGet("/x")).rejects.toMatchObject({ status: 0, code: "network_error" });
  });
});
