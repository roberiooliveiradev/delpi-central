import { afterEach, describe, expect, it, vi } from "vitest";
import {
  fetchPrcQueue,
  prcAction,
  prcIntakeSubmit,
  prcUpdateDraft,
} from "./api/productRegistrationApi";
import {
  buildPrcQueueUrl,
  parsePrcQueueUrl,
  parsePrcTab,
  resolvePrcPath,
} from "./prcNavigate";

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

  it("resolves create wizard on /new", () => {
    expect(resolvePrcPath("product-registration/new")).toEqual({
      page: "create",
    });
  });

  it("falls back to queue on malformed id", () => {
    expect(resolvePrcPath("product-registration/abc")).toEqual({
      page: "queue",
    });
  });
});

describe("prcNavigate url state", () => {
  it("parses queue filters from search", () => {
    expect(
      parsePrcQueueUrl("?status=submitted&type=create&search=abc&page=3"),
    ).toEqual({
      status: "submitted",
      type: "create",
      search: "abc",
      page: 3,
    });
  });

  it("ignores invalid type and page", () => {
    expect(parsePrcQueueUrl("?type=foo&page=-2")).toEqual({
      status: "",
      type: "",
      search: "",
      page: 1,
    });
  });

  it("builds queue url omitting defaults", () => {
    expect(
      buildPrcQueueUrl("/apps/engineering", {
        status: "in_progress",
        type: "",
        search: "",
        page: 1,
      }),
    ).toBe("/apps/engineering/product-registration?status=in_progress");
  });

  it("parses detail tab with fallback to overview", () => {
    expect(parsePrcTab("?tab=verification")).toBe("verification");
    expect(parsePrcTab("?tab=bogus")).toBe("overview");
    expect(parsePrcTab("")).toBe("overview");
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

  it("sends action with expectedVersion and Idempotency-Key", async () => {
    await prcAction(
      REQUEST_ID,
      "verify-and-complete",
      {
        expectedVersion: 3,
        officialCode: "001234",
      },
      "idem-abc",
    );
    const [url, init] = vi.mocked(fetch).mock.calls[0] as [
      string,
      RequestInit,
    ];
    expect(url).toContain(
      `/requests/${REQUEST_ID}/actions/verify-and-complete`,
    );
    expect(
      (init.headers as Record<string, string>)["Idempotency-Key"],
    ).toBe("idem-abc");
  });

  it("submits intake create with Idempotency-Key header", async () => {
    await prcIntakeSubmit(
      {
        source: "portal-engineering",
        requestType: "create",
        productType: "raw_material",
        schemaVersion: 1,
        requestedData: { description: "X" },
      },
      "idem-intake",
    );
    const [url, init] = vi.mocked(fetch).mock.calls[0] as [
      string,
      RequestInit,
    ];
    expect(url).toContain("/product-registration/intake/requests");
    expect(init.method).toBe("POST");
    expect(
      (init.headers as Record<string, string>)["Idempotency-Key"],
    ).toBe("idem-intake");
    expect(JSON.parse(String(init.body)).requestType).toBe("create");
  });
});
