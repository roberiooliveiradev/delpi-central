import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, CONTROLLERSHIP_FINANCE_API_BASE } from "./httpClient";
import { getViewerContext } from "./viewerContextApi";

const fetchMock = vi.fn();

vi.stubGlobal("fetch", fetchMock);

afterEach(() => {
  fetchMock.mockReset();
});

function okEnvelope(data: unknown) {
  return new Response(
    JSON.stringify({ success: true, message: "OK", data }),
    { status: 200, headers: { "Content-Type": "application/json" } },
  );
}

describe("viewerContextApi", () => {
  it("chama a BFF do produto — nunca Core nem api-delpi", async () => {
    fetchMock.mockResolvedValueOnce(
      okEnvelope({
        firstName: "Ana",
        capabilities: { access: true, manage: false },
      }),
    );
    const ctx = await getViewerContext();
    expect(ctx).toEqual({
      firstName: "Ana",
      displayName: null,
      capabilities: { access: true, manage: false },
    });
    const url = fetchMock.mock.calls[0][0] as string;
    expect(url).toBe(`${CONTROLLERSHIP_FINANCE_API_BASE}/viewer-context`);
    expect(url).not.toContain("core-api");
    expect(url).not.toContain("api-delpi");
  });

  it("tolerância a payload parcial — defaults seguros", async () => {
    fetchMock.mockResolvedValueOnce(okEnvelope({}));
    const ctx = await getViewerContext();
    expect(ctx).toEqual({
      firstName: null,
      displayName: null,
      capabilities: { access: false, manage: false },
    });
  });

  it("propaga ApiError com status 403", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "Forbidden" }), { status: 403 }),
    );
    await expect(getViewerContext()).rejects.toMatchObject({
      status: 403,
    });
  });

  it("propaga ApiError com status 503", async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "Authorization service unavailable" }), {
        status: 503,
      }),
    );
    await expect(getViewerContext()).rejects.toBeInstanceOf(ApiError);
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify({ detail: "x" }), { status: 503 }),
    );
    await expect(getViewerContext()).rejects.toMatchObject({ status: 503 });
  });
});
