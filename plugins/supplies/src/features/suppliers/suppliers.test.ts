import { describe, expect, it } from "vitest";

import {
  buildSupplierCreatePath,
  buildSupplierDetailPath,
  resolvePluginRoute,
} from "../../app/pluginRoutes";
import {
  mapSuppliersFetchError,
  SUPPLIERS_CONTENT,
} from "./content";
import {
  buildCreateFornecedor,
  buildUpdateFornecedor,
  buildUrlSearch,
  classifyWriteOutcome,
  createDefaultQuery,
  diffEditableFields,
  draftFromDetail,
  formatTaxIdMasked,
  getSupplierFieldValue,
  groupChangesBySection,
  hasActiveFilters,
  isSupplierFieldAvailable,
  parseQueryFromSearch,
  personTypeLabel,
} from "./query";
import {
  SUPPLIER_CREATE_SECTIONS,
  SUPPLIER_FIELD_REGISTRY,
  SUPPLIER_FORM_SECTIONS,
  SUPPLIER_PUT_EDITABLE_KEYS,
  type SupplierCreateDraft,
  type SupplierDetail,
} from "./types";

describe("supplier routes", () => {
  it("resolves the suppliers list", () => {
    expect(resolvePluginRoute("/apps/supplies/suppliers").view).toBe("suppliers");
  });

  it("resolves supplier create before detail", () => {
    const route = resolvePluginRoute("/apps/supplies/suppliers/new");
    expect(route.view).toBe("supplier_create");
  });

  it("resolves supplier detail with code/store preserving leading zeros", () => {
    const route = resolvePluginRoute("/apps/supplies/suppliers/001234/01");
    expect(route.view).toBe("supplier_detail");
    expect(route.supplierCode).toBe("001234");
    expect(route.supplierStore).toBe("01");
    expect(buildSupplierDetailPath("001234", "01")).toBe(
      "/apps/supplies/suppliers/001234/01",
    );
    expect(buildSupplierCreatePath()).toBe("/apps/supplies/suppliers/new");
  });

  it("rejects non-numeric detail segments", () => {
    expect(resolvePluginRoute("/apps/supplies/suppliers/abc/01").view).toBe(
      "not_found",
    );
  });
});

describe("suppliers query", () => {
  it("round-trips search params through the URL", () => {
    const parsed = parseQueryFromSearch("?query=ferro&state=SC&blocked=1&page=3&page_size=50");
    expect(parsed.query).toBe("ferro");
    expect(parsed.state).toBe("SC");
    expect(parsed.blocked).toBe("1");
    expect(parsed.page).toBe(3);
    expect(parsed.page_size).toBe(50);
    expect(buildUrlSearch(parsed)).toBe("?query=ferro&state=SC&blocked=1&page=3&page_size=50");
  });

  it("sanitizes invalid values to defaults", () => {
    const parsed = parseQueryFromSearch("?blocked=yes&page=-2&page_size=7");
    expect(parsed).toEqual(createDefaultQuery());
    expect(hasActiveFilters(parsed)).toBe(false);
    expect(buildUrlSearch(parsed)).toBe("");
  });
});

describe("supplier edit diff", () => {
  const detail: SupplierDetail = {
    supplier_id: "00246901",
    supplier_code: "002469",
    supplier_store: "01",
    blocked: false,
    tax_id: "00000000000191",
    tax_id_masked: false,
    sections: {
      identification: {
        supplier_name: "DELPI",
        supplier_short_name: "DELPI",
        person_type: "J",
      },
      address: { city: "TIMBO", state: "SC" },
      contact: { email: "a@b.com" },
    },
  };

  it("detects a single changed field", () => {
    const draft = draftFromDetail(detail);
    draft.supplier_name = "DELPI NOVA";
    const diff = diffEditableFields(detail, draft);
    expect(diff).toEqual([
      { field: "supplier_name", before: "DELPI", after: "DELPI NOVA" },
    ]);
  });

  it("detects changes across multiple sections in one PUT", () => {
    const draft = draftFromDetail(detail);
    draft.supplier_name = "A";
    draft.city = "BLUMENAU";
    draft.email = "novo@b.com";
    const diff = diffEditableFields(detail, draft);
    expect(diff.map((c) => c.field).sort()).toEqual([
      "city",
      "email",
      "supplier_name",
    ]);
  });

  it("returns empty when nothing changed", () => {
    expect(diffEditableFields(detail, draftFromDetail(detail))).toEqual([]);
  });

  it("never diffs protected/readonly fields", () => {
    const fields = diffEditableFields(detail, {
      ...draftFromDetail(detail),
    }).map((c) => c.field);
    expect(fields).not.toContain("tax_id");
    expect(fields).not.toContain("supplier_store");
    expect(fields).not.toContain("supplier_code");
  });
});

describe("supplier create payload", () => {
  const fullDraft: SupplierCreateDraft = {
    supplier_store: "01",
    person_type: "J",
    tax_id: "00000000000191",
    supplier_name: "FORNECEDOR TESTE",
    supplier_short_name: "FORN TESTE",
    address: "RUA X",
    district: "CENTRO",
    postal_code: "89120000",
    state: "sc",
    city: "TIMBO",
    city_code: "18202",
    area_code: "047",
    phone: "99999",
    contact_name: "CONTATO",
    email: "a@b.com",
    state_registration: "123",
    municipal_registration: "",
    country_code: "105",
    bacen_country_code: "01058",
    rohs_indicator: "n",
    payment_condition_code: "010",
    payment_method_code: "01",
    accounting_account: "00000000",
    financial_nature_code: "0000",
  };

  it("sends all filled contract fields preserving leading zeros", () => {
    const body = buildCreateFornecedor(fullDraft);
    expect(body.supplier_store).toBe("01");
    expect(body.tax_id).toBe("00000000000191");
    expect(body.postal_code).toBe("89120000");
    expect(body.city_code).toBe("18202");
    expect(body.bacen_country_code).toBe("01058");
    expect(body.payment_condition_code).toBe("010");
    expect(body.financial_nature_code).toBe("0000");
  });

  it("omits empty fields and uppercases enums/state", () => {
    const body = buildCreateFornecedor(fullDraft);
    expect(body.municipal_registration).toBeUndefined();
    expect(body.state).toBe("SC");
    expect(body.person_type).toBe("J");
    expect(body.rohs_indicator).toBe("N");
    expect(body.codusr).toBeUndefined();
  });

  it("covers every contract POST field exactly once across sections", () => {
    const keys = SUPPLIER_CREATE_SECTIONS.flatMap((s) =>
      s.fields.map((f) => f.key),
    );
    expect(new Set(keys).size).toBe(keys.length);
    expect(new Set(keys)).toEqual(
      new Set(Object.keys(fullDraft) as (keyof SupplierCreateDraft)[]),
    );
  });

  it("marks only supplier_store as required", () => {
    const required = SUPPLIER_CREATE_SECTIONS.flatMap((s) => s.fields).filter(
      (f) => f.required,
    );
    expect(required.map((f) => f.key)).toEqual(["supplier_store"]);
  });
});

describe("shared field registry (F3.1 create/edit parity)", () => {
  it("edit sections contain all POST fields plus system identity", () => {
    const formKeys = SUPPLIER_FORM_SECTIONS.flatMap((s) =>
      s.fields.map((f) => f.key),
    );
    const createKeys = SUPPLIER_CREATE_SECTIONS.flatMap((s) =>
      s.fields.map((f) => f.key),
    );
    expect(new Set(formKeys)).toEqual(new Set([...createKeys, "supplier_code"]));
    expect(new Set(formKeys).size).toBe(formKeys.length);
  });

  it("keeps the same section order and ids as the create form", () => {
    expect(SUPPLIER_FORM_SECTIONS.map((s) => s.id)).toEqual(
      SUPPLIER_CREATE_SECTIONS.map((s) => s.id),
    );
  });

  it("allows PUT for all cadastral fields except document and identity", () => {
    expect([...SUPPLIER_PUT_EDITABLE_KEYS].sort()).toEqual(
      [
        "person_type",
        "supplier_name",
        "supplier_short_name",
        "address",
        "district",
        "postal_code",
        "state",
        "city",
        "city_code",
        "area_code",
        "phone",
        "contact_name",
        "email",
        "state_registration",
        "municipal_registration",
        "country_code",
        "bacen_country_code",
        "rohs_indicator",
        "payment_condition_code",
        "payment_method_code",
        "accounting_account",
        "financial_nature_code",
      ].sort(),
    );
    const editable = SUPPLIER_FIELD_REGISTRY.filter((f) => f.put === "editable");
    expect(
      editable.every(
        (f) => f.evidence === "put-contract" || f.evidence === "po-decision",
      ),
    ).toBe(true);
  });

  it("marks document and identity fields as protected (never editable)", () => {
    for (const key of ["supplier_code", "supplier_store", "tax_id"] as const) {
      expect(
        SUPPLIER_FIELD_REGISTRY.find((f) => f.key === key)?.put,
      ).toBe("protected");
    }
    const code = SUPPLIER_FIELD_REGISTRY.find((f) => f.key === "supplier_code");
    expect(code?.post).toBe(false);
    expect(code?.evidence).toBe("system");
  });
});

describe("GET to form mapping", () => {
  const detail: SupplierDetail = {
    supplier_id: "00246901",
    supplier_code: "002469",
    supplier_store: "01",
    blocked: false,
    tax_id: "***********",
    tax_id_masked: true,
    sections: {
      identification: {
        supplier_code: "002469",
        supplier_store: "01",
        supplier_name: "RODRIGUES KANNENBERG",
        supplier_short_name: "RODRIGUES KANNENBERG",
        person_type: "J",
      },
      address: { postal_code: "08910000", state: "SC" },
    },
  };
  const spec = (key: string) =>
    SUPPLIER_FIELD_REGISTRY.find((f) => f.key === key)!;

  it("maps identity fields from top-level code/store", () => {
    expect(getSupplierFieldValue(detail, spec("supplier_code"))).toBe("002469");
    expect(getSupplierFieldValue(detail, spec("supplier_store"))).toBe("01");
  });

  it("maps section fields preserving leading zeros", () => {
    expect(getSupplierFieldValue(detail, spec("postal_code"))).toBe("08910000");
    expect(getSupplierFieldValue(detail, spec("supplier_name"))).toBe(
      "RODRIGUES KANNENBERG",
    );
  });

  it("maps tax_id through the masked projection (CPF never shown)", () => {
    expect(getSupplierFieldValue(detail, spec("tax_id"))).toBe("••••••");
  });

  it("returns empty string for fields absent from the GET payload", () => {
    expect(getSupplierFieldValue(detail, spec("city"))).toBe("");
    expect(getSupplierFieldValue(detail, spec("email"))).toBe("");
  });
});

describe("supplier update payload", () => {
  it("sends only the fields that actually changed", () => {
    const body = buildUpdateFornecedor([
      { field: "supplier_name", after: "NOVO NOME" },
    ]);
    expect(body).toEqual({ supplier_name: "NOVO NOME" });
    expect(body.supplier_short_name).toBeUndefined();
  });

  it("supports multiple changed fields in one PUT", () => {
    const body = buildUpdateFornecedor([
      { field: "supplier_name", after: "A" },
      { field: "supplier_short_name", after: "B" },
    ]);
    expect(body).toEqual({ supplier_name: "A", supplier_short_name: "B" });
  });
});

describe("write outcome classification", () => {
  it("never equates acknowledged with persisted", () => {
    expect(classifyWriteOutcome({ acknowledged: true }, 200)).toBe("acknowledged");
    expect(
      classifyWriteOutcome({ acknowledged: true, persistence_proven: true }, 200),
    ).toBe("persistence_confirmed");
  });

  it("classifies gate-off as write_disabled", () => {
    expect(
      classifyWriteOutcome(
        { outcome: "write_disabled", code: "PROTHEUS_SUPPLIER_UPDATE_DISABLED" },
        503,
      ),
    ).toBe("write_disabled");
    expect(
      classifyWriteOutcome(
        { code: "PROTHEUS_SUPPLIER_CREATE_DISABLED" },
        503,
      ),
    ).toBe("write_disabled");
  });

  it("classifies rejection and indeterminate outcomes", () => {
    expect(classifyWriteOutcome(undefined, 422)).toBe("rejected");
    expect(classifyWriteOutcome({}, 504)).toBe("indeterminate");
    expect(classifyWriteOutcome(undefined, undefined)).toBe("indeterminate");
  });
});

describe("fetch error mapping", () => {
  it("shows the permission message only for the BFF supplies.access denial", () => {
    expect(mapSuppliersFetchError("Forbidden", "forbidden")).toBe(
      SUPPLIERS_CONTENT.errorForbidden,
    );
  });

  it("does not claim a missing permission on upstream S2S denials", () => {
    expect(mapSuppliersFetchError("Forbidden", "S2S_SCOPE_DENIED")).toBe(
      SUPPLIERS_CONTENT.error,
    );
    expect(mapSuppliersFetchError("Forbidden", "upstream_forbidden")).toBe(
      SUPPLIERS_CONTENT.error,
    );
  });

  it("keeps the message heuristic when no typed code is present", () => {
    expect(mapSuppliersFetchError("Forbidden")).toBe(
      SUPPLIERS_CONTENT.errorForbidden,
    );
    expect(mapSuppliersFetchError("unexpected")).toBe(SUPPLIERS_CONTENT.error);
  });
});

describe("supplier field grid spans", () => {
  it("declares a valid 12-col span for every field", () => {
    for (const spec of SUPPLIER_FIELD_REGISTRY) {
      expect(spec.span).toBeGreaterThanOrEqual(2);
      expect(spec.span).toBeLessThanOrEqual(12);
      expect(Number.isInteger(spec.span)).toBe(true);
    }
  });

  it("keeps long fields wide and short fields narrow", () => {
    const span = (key: string) =>
      SUPPLIER_FIELD_REGISTRY.find((f) => f.key === key)!.span;
    expect(span("supplier_name")).toBe(6);
    expect(span("address")).toBe(6);
    expect(span("supplier_code")).toBe(2);
    expect(span("supplier_store")).toBe(2);
    expect(span("state")).toBe(2);
  });
});

describe("review grouping", () => {
  const detail: SupplierDetail = {
    supplier_id: "00246901",
    supplier_code: "002469",
    supplier_store: "01",
    blocked: false,
    tax_id: null,
    tax_id_masked: true,
    sections: {
      identification: { supplier_name: "A" },
      address: { city: "TIMBO" },
      contact: { email: "a@b.com" },
    },
  };

  it("groups changes under their registry sections in canonical order", () => {
    const draft = draftFromDetail(detail);
    draft.supplier_name = "B";
    draft.city = "BLUMENAU";
    draft.email = "x@y.com";
    const groups = groupChangesBySection(diffEditableFields(detail, draft));
    expect(groups.map((g) => g.section)).toEqual([
      "identification",
      "address",
      "contact",
    ]);
    expect(groups[0].changes[0].field).toBe("supplier_name");
  });
});

describe("field availability (R3 empty vs unavailable)", () => {
  const detail: SupplierDetail = {
    supplier_id: "00246901",
    supplier_code: "002469",
    supplier_store: "01",
    blocked: false,
    tax_id: null,
    tax_id_masked: true,
    sections: {
      identification: { supplier_name: "DELPI" },
      address: { city: "" },
    },
  };
  const spec = (key: string) =>
    SUPPLIER_FIELD_REGISTRY.find((f) => f.key === key)!;

  it("marks present-but-empty keys as available (não informado)", () => {
    expect(isSupplierFieldAvailable(detail, spec("city"))).toBe(true);
  });

  it("marks keys absent from the payload as unavailable", () => {
    expect(isSupplierFieldAvailable(detail, spec("email"))).toBe(false);
    expect(isSupplierFieldAvailable(detail, spec("district"))).toBe(false);
  });

  it("identity fields are always available", () => {
    expect(isSupplierFieldAvailable(detail, spec("supplier_code"))).toBe(true);
    expect(isSupplierFieldAvailable(detail, spec("supplier_store"))).toBe(true);
  });
});

describe("grid section assignment (R2)", () => {
  it("keeps country_code in the address section, distinct from BACEN", () => {
    const country = SUPPLIER_FIELD_REGISTRY.find(
      (f) => f.key === "country_code",
    )!;
    const bacen = SUPPLIER_FIELD_REGISTRY.find(
      (f) => f.key === "bacen_country_code",
    )!;
    expect(country.section).toBe("address");
    expect(bacen.section).toBe("fiscal");
    expect(country.key).not.toBe(bacen.key);
  });
});

describe("accounting account contract (R4)", () => {
  it("A2_CONTA accepts up to 20 chars — 11 digits is contract-valid", () => {
    const spec = SUPPLIER_FIELD_REGISTRY.find(
      (f) => f.key === "accounting_account",
    )!;
    expect(spec.maxLength).toBe(20);
    expect(spec.put).toBe("editable");
    expect("21101559000".length).toBeLessThanOrEqual(spec.maxLength);
  });
});

describe("person type label", () => {
  it("maps known codes to short labels", () => {
    expect(personTypeLabel("J")).toBe("Jurídica");
    expect(personTypeLabel("f")).toBe("Física");
    expect(personTypeLabel("X")).toBe("Outros");
  });

  it("returns empty for missing or unknown values", () => {
    expect(personTypeLabel(null)).toBe("");
    expect(personTypeLabel("")).toBe("");
    expect(personTypeLabel("Z")).toBe("");
  });
});

describe("tax id masking", () => {
  it("formats a CNPJ when not masked", () => {
    expect(formatTaxIdMasked("01234567000199", false)).toBe("01.234.567/0001-99");
  });

  it("never renders masked CPF digits", () => {
    expect(formatTaxIdMasked("***********", true)).toBe("••••••");
    expect(formatTaxIdMasked(null, true)).toBe("—");
  });
});
