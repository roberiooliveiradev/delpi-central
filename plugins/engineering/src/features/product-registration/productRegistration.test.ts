import { afterEach, describe, expect, it, vi } from "vitest";
import { resolvePrcPath } from "./ProductRegistrationFeature";
import {
  fetchPrcQueue,
  prcAction,
  prcUpdateDraft,
} from "./api/productRegistrationApi";

const REQUEST_ID = "11111111-2222-3333-4444-555555555555";

vi.stubGlobal(
  "fetch",
  vi.fn(
    async () =>
      new Response(
        JSON.stringify({ success: true, message: "ok", data: {} }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
  ),
);

afterEach(() => {
  vi.mocked(fetch).mockClear();
});

describe("resolvePrcPath", () => {
  it("resolves queue root", () => {
    expect(resolvePrcPath("product-registration")).toEqual({
      page: "queue",
    });
  });

  it("resolves detail by uuid deep-link", () => {
    expect(
      resolvePrcPath(`product-registration/${REQUEST_ID}`),
    ).toEqual({ page: "detail", requestId: REQUEST_ID });
  });

  it("falls back to queue on malformed id", () => {
    expect(resolvePrcPath("product-registration/abc")).toEqual({
      page: "queue",
    });
  });
});

describe("productRegistrationApi", () => {
  it("fetches queue with filters", async () => {
    await fetchPrcQueue({ status: "submitted", page: 1 });
    const [url] = vi.mocked(fetch).mock.calls[0] as [string];
    expect(url).toContain(
      "/apps/engineering-api/v1/product-registration/requests",
    );
    expect(url).toContain("status=submitted");
  });

  it("sends draft patch with expectedVersion", async () => {
    await prcUpdateDraft(REQUEST_ID, {
      expectedVersion: 2,
      changes: [
        { path: "description", proposedValue: "X", reason: "r" },
      ],
    });
    const [url, init] = vi.mocked(fetch).mock.calls[0] as [
      string,
      RequestInit,
    ];
    expect(url).toContain(`/requests/${REQUEST_ID}/draft`);
    expect(init.method).toBe("PATCH");
  });

  it("sends action with expectedVersion", async () => {
    await prcAction(REQUEST_ID, "verify-and-complete", {
      expectedVersion: 3,
      officialCode: "001234",
    });
    const [url] = vi.mocked(fetch).mock.calls[0] as [string];
    expect(url).toContain(
      `/requests/${REQUEST_ID}/actions/verify-and-complete`,
    );
  });
});
