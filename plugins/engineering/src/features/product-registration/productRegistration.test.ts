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
  EMPTY_PRC_QUEUE_URL,
  parsePrcProductRevision,
  parsePrcProductTab,
  parsePrcQueueUrl,
  parsePrcTab,
  prcProductHref,
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

  it("resolves tracked product deep-link", () => {
    expect(
      resolvePrcPath(`product-registration/products/${REQUEST_ID}`),
    ).toEqual({ page: "product", recordId: REQUEST_ID });
  });

  it("falls back to queue on malformed product id", () => {
    expect(
      resolvePrcPath("product-registration/products/abc"),
    ).toEqual({ page: "queue" });
  });
});

describe("prcNavigate url state", () => {
  it("parses queue filters from search", () => {
    expect(
      parsePrcQueueUrl("?status=submitted&type=create&search=abc&page=3"),
    ).toEqual({
      ...EMPTY_PRC_QUEUE_URL,
      status: "submitted",
      type: "create",
      search: "abc",
      page: 3,
    });
  });

  it("ignores invalid type and page", () => {
    expect(parsePrcQueueUrl("?type=foo&page=-2")).toEqual(
      EMPTY_PRC_QUEUE_URL,
    );
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
        ...EMPTY_PRC_QUEUE_URL,
        status: "in_progress",
      }),
    ).toBe("/apps/engineering/product-registration?status=in_progress");
  });

  it("parses products area and flag filter from search", () => {
    const state = parsePrcQueueUrl(
      "?area=products&flagState=open&search=trafo&page=2",
    );
    expect(state.area).toBe("products");
    expect(state.flagState).toBe("open");
    expect(state.search).toBe("trafo");
    expect(state.page).toBe(2);
  });

  it("serializes products area and flag filter in queue url", () => {
    expect(
      buildPrcQueueUrl("/apps/engineering", {
        ...EMPTY_PRC_QUEUE_URL,
        area: "products",
        flagState: "none",
        sortBy: "lastEvolution",
        sortDir: "asc",
      }),
    ).toBe(
      "/apps/engineering/product-registration?area=products&flagState=none&sortBy=lastEvolution&sortDir=asc",
    );
  });

  it("accepts all five product sort keys and canonical default dir", () => {
    const state = parsePrcQueueUrl(
      "?area=products&sortBy=openFlags&sortDir=asc",
    );
    expect(state.sortBy).toBe("openFlags");
    expect(state.sortDir).toBe("asc");
    expect(
      parsePrcQueueUrl("?area=products&sortBy=version").sortBy,
    ).toBe("version");
    /* sortDir ausente → direção canônica do campo (code=asc,
     * version/openFlags/lastEvolution=desc). */
    expect(
      parsePrcQueueUrl("?area=products&sortBy=code").sortDir,
    ).toBe("asc");
    expect(
      parsePrcQueueUrl("?area=products&sortBy=version").sortDir,
    ).toBe("desc");
    /* campo fora da whitelist cai no estado vazio; sortDir de
     * solicitações não vaza para produtos. */
    const bad = parsePrcQueueUrl(
      "?area=products&sortBy=createdAt&sortDir=asc",
    );
    expect(bad.sortBy).toBe("");
    expect(
      parsePrcQueueUrl("?sortBy=version&sortDir=asc").sortBy,
    ).toBe("");
  });

  it("parses product tab and revision with safe fallbacks", () => {
    expect(parsePrcProductTab("?tab=versions")).toBe("versions");
    expect(parsePrcProductTab("?tab=bogus")).toBe("sheet");
    expect(parsePrcProductTab("")).toBe("sheet");
    expect(parsePrcProductRevision("?rev=3")).toBe(3);
    expect(parsePrcProductRevision("?rev=0")).toBeNull();
    expect(parsePrcProductRevision("?rev=abc")).toBeNull();
    expect(parsePrcProductRevision("")).toBeNull();
  });

  it("builds product href with tab and revision", () => {
    expect(
      prcProductHref("/apps/engineering", REQUEST_ID, {
        tab: "versions",
      }),
    ).toBe(
      `/apps/engineering/product-registration/products/${REQUEST_ID}?tab=versions`,
    );
    expect(
      prcProductHref("/apps/engineering", REQUEST_ID, { rev: 2 }),
    ).toBe(
      `/apps/engineering/product-registration/products/${REQUEST_ID}?rev=2`,
    );
    expect(prcProductHref("/apps/engineering", REQUEST_ID, {})).toBe(
      `/apps/engineering/product-registration/products/${REQUEST_ID}`,
    );
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
