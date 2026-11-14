import { afterEach, describe, expect, it, vi } from "vitest";
import {
  createPrcFlag,
  deletePrcFlag,
  fetchPrcFlags,
  fetchPrcQueue,
  prcAction,
  prcIntakeSubmit,
  prcUpdateDraft,
  resolvePrcFlag,
} from "./api/productRegistrationApi";
import { PRC_EVENT_LABELS } from "./prcCopy";
import {
  buildPrcQueueUrl,
  parsePrcQueueUrl,
  parsePrcTab,
  prcQueueStateForStatusFilter,
  prcQueueStatusFilterValue,
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
      view: "",
      status: "submitted",
      type: "create",
      search: "abc",
      page: 3,
      sortBy: "",
      sortDir: "desc",
    });
  });

  it("ignores invalid type and page", () => {
    expect(parsePrcQueueUrl("?type=foo&page=-2")).toEqual({
      view: "",
      status: "",
      type: "",
      search: "",
      page: 1,
      sortBy: "",
      sortDir: "desc",
    });
  });

  it("view=pending → preset serializado na URL", () => {
    const state = parsePrcQueueUrl("?view=pending");
    expect(state.view).toBe("pending");
    expect(
      buildPrcQueueUrl("/apps/engineering", { ...state, view: "pending" }),
    ).toBe("/apps/engineering/product-registration?view=pending");
    /* valor arbitrário não vira preset */
    expect(parsePrcQueueUrl("?view=foo").view).toBe("");
  });

  it("status filter group: view=pending seleciona 'pending'", () => {
    expect(
      prcQueueStatusFilterValue(parsePrcQueueUrl("?view=pending")),
    ).toBe("pending");
    /* status explícito prevalece sobre o preset na seleção exibida */
    expect(
      prcQueueStatusFilterValue(
        parsePrcQueueUrl("?view=pending&status=completed"),
      ),
    ).toBe("completed");
    expect(prcQueueStatusFilterValue(parsePrcQueueUrl(""))).toBe("");
    expect(
      prcQueueStatusFilterValue(parsePrcQueueUrl("?status=submitted")),
    ).toBe("submitted");
  });

  it("status filter group: transições de estado (§41)", () => {
    const pending = parsePrcQueueUrl("?view=pending&page=3&type=create");
    /* Pendentes → mantém preset, remove status, reseta página */
    const toPending = prcQueueStateForStatusFilter(
      parsePrcQueueUrl("?status=completed"), "pending",
    );
    expect(toPending).toMatchObject({ view: "pending", status: "", page: 1 });
    /* Todos → remove view e status, preserva demais filtros */
    const toAll = prcQueueStateForStatusFilter(pending, "");
    expect(toAll).toMatchObject({
      view: "", status: "", type: "create", page: 1,
    });
    /* status específico → remove preset, fixa status, reseta página */
    const toSubmitted = prcQueueStateForStatusFilter(pending, "submitted");
    expect(toSubmitted).toMatchObject({
      view: "", status: "submitted", page: 1,
    });
    expect(
      buildPrcQueueUrl("/apps/engineering", toSubmitted),
    ).toBe(
      "/apps/engineering/product-registration?status=submitted&type=create",
    );
    /* URL serializada re-parseia com a mesma seleção */
    expect(
      prcQueueStatusFilterValue(
        parsePrcQueueUrl("?status=completed"),
      ),
    ).toBe("completed");
  });

  it("builds queue url omitting defaults", () => {
    expect(
      buildPrcQueueUrl("/apps/engineering", {
        view: "",
        status: "in_progress",
        type: "",
        search: "",
        page: 1,
        sortBy: "",
        sortDir: "desc",
      }),
    ).toBe("/apps/engineering/product-registration?status=in_progress");
  });

  it("parses detail tab with fallback to ficha técnica", () => {
    expect(parsePrcTab("?tab=verification")).toBe("verification");
    expect(parsePrcTab("?tab=bogus")).toBe("draft");
    expect(parsePrcTab("")).toBe("draft");
    /* deep link legado `?tab=overview` → Ficha técnica, sem erro. */
    expect(parsePrcTab("?tab=overview")).toBe("draft");
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

  it("sends complete action with expectedVersion and Idempotency-Key", async () => {
    await prcAction(
      REQUEST_ID,
      "complete",
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
      `/requests/${REQUEST_ID}/actions/complete`,
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

  it("lists and mutates attendance flags with Idempotency-Key", async () => {
    await fetchPrcFlags(REQUEST_ID, { status: "OPEN", page: 1 });
    const [listUrl] = vi.mocked(fetch).mock.calls[0] as [string];
    expect(listUrl).toContain(`/requests/${REQUEST_ID}/flags`);
    expect(listUrl).toContain("status=OPEN");

    await createPrcFlag(
      REQUEST_ID,
      {
        title: "Revisar descrição",
        description: "Confirmar com solicitante.",
        subject: "FIELD",
        targetPath: "description",
      },
      "flag-idem-1",
    );
    const [, createInit] = vi.mocked(fetch).mock.calls[1] as [
      string,
      RequestInit,
    ];
    expect(createInit.method).toBe("POST");
    expect(
      (createInit.headers as Record<string, string>)["Idempotency-Key"],
    ).toBe("flag-idem-1");

    await resolvePrcFlag(
      REQUEST_ID,
      "flag-1",
      { expectedVersion: 1 },
      "flag-res",
    );
    const [resolveUrl] = vi.mocked(fetch).mock.calls[2] as [string];
    expect(resolveUrl).toContain("/flags/flag-1/actions/resolve");

    await deletePrcFlag(REQUEST_ID, "flag-1", 2, "flag-del");
    const [deleteUrl, deleteInit] = vi.mocked(fetch).mock.calls[3] as [
      string,
      RequestInit,
    ];
    expect(deleteUrl).toContain("expectedVersion=2");
    expect(deleteInit.method).toBe("DELETE");
  });
});

describe("PRC_EVENT_LABELS D16", () => {
  it("labels flag lifecycle events", () => {
    expect(PRC_EVENT_LABELS["flag.created"]).toMatch(/Bandeira/);
    expect(PRC_EVENT_LABELS["flag.deleted"]).toMatch(/exclu/);
  });
});
