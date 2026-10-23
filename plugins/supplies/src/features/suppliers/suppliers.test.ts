import { describe, expect, it } from "vitest";

import {
  buildSupplierCreatePath,
  buildSupplierDetailPath,
  resolvePluginRoute,
} from "../../app/pluginRoutes";
import {
  mapSuppliersFetchError,
  SUPPLIERS_CONTENT,
  supplierFieldMaxLengthHint,
  supplierSectionDescriptions,
} from "./content";
import {
  deriveProtheusCityCode,
  isCompletePostalCode,
  normalizePostalDigits,
  reconcileMunicipality,
} from "./postalAddress";
import { catalogDisplayText } from "./supplierCatalogs";
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
  type SupplierExtendedFieldKey,
} from "./types";

/** Draft vazio dos 29 campos estendidos E3 — preenchido sob demanda. */
const EMPTY_E3_DRAFT: Pick<SupplierCreateDraft, SupplierExtendedFieldKey> = {
  address_number: "",
  po_box: "",
  icms_contributor: "",
  simples_nacional: "",
  cnae_code: "",
  legal_entity_type: "",
  simp_regime_code: "",
  pb_regime_code: "",
  inss_withholding: "",
  iss_withholding: "",
  csll_withholding: "",
  cofins_withholding: "",
  pis_withholding: "",
  irf_calculation: "",
  inp_calculation: "",
  tax_group_code: "",
  commercial_contact_name: "",
  fax: "",
  website: "",
  responsible_name: "",
  risk_code: "",
  swift_code: "",
  purchase_price_table_code: "",
  carrier_code: "",
  segment_code: "",
  administrator_code: "",
  linked_customer_code: "",
  linked_customer_store: "",
  linked_employee_code: "",
};

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
    ...EMPTY_E3_DRAFT,
    cnae_code: "6201501",
    address_number: "385",
    linked_customer_code: "000123",
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
        // X4.FIELDS.E5 — 26 campos PUT-homologados em DELPI_TST01
        "legal_entity_type",
        "address_number",
        "po_box",
        "commercial_contact_name",
        "responsible_name",
        "fax",
        "website",
        "icms_contributor",
        "simples_nacional",
        "cnae_code",
        "pb_regime_code",
        "tax_group_code",
        "inss_withholding",
        "iss_withholding",
        "csll_withholding",
        "cofins_withholding",
        "pis_withholding",
        "irf_calculation",
        "inp_calculation",
        "purchase_price_table_code",
        "risk_code",
        "swift_code",
        "carrier_code",
        "segment_code",
        "administrator_code",
        "linked_employee_code",
        // X4.FIELDS.E6 — reteste TST01 homologou regime SIMPA e par
        // cliente vinculado (loja + companion code injetado no backend)
        "simp_regime_code",
        "linked_customer_store",
      ].sort(),
    );
    const editable = SUPPLIER_FIELD_REGISTRY.filter((f) => f.put === "editable");
    expect(
      editable.every(
        (f) =>
          f.evidence === "put-contract" ||
          f.evidence === "po-decision" ||
          f.evidence === "put-homologated",
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

describe('E7 — helps funcionais com referência TOTVS', () => {
  const FORBIDDEN =
    /contrato REST|API REST|payload|BFF|DTO|serializer|backend|field mapping|contrato de integração|normalizado/i;

  it('every registry help carries a verified TOTVS physical reference', () => {
    for (const spec of SUPPLIER_FIELD_REGISTRY) {
      expect(
        spec.help,
        `help sem referência TOTVS em ${spec.key}`,
      ).toMatch(/\(TOTVS: [A-Z0-9_.+ ]+\)/);
    }
  });

  it('no help exposes implementation jargon', () => {
    for (const spec of SUPPLIER_FIELD_REGISTRY) {
      expect(spec.help, `jargão técnico em ${spec.key}`).not.toMatch(FORBIDDEN);
    }
  });

  it('create and edit sections share the same registry help source', () => {
    const createKeys = new Set(
      SUPPLIER_CREATE_SECTIONS.flatMap((s) => s.fields.map((f) => f.key)),
    );
    const formKeys = new Set(
      SUPPLIER_FORM_SECTIONS.flatMap((s) => s.fields.map((f) => f.key)),
    );
    for (const key of createKeys) {
      const spec = SUPPLIER_FIELD_REGISTRY.find((f) => f.key === key)!;
      expect(spec.help).toBeTruthy();
    }
    for (const key of formKeys) {
      const spec = SUPPLIER_FIELD_REGISTRY.find((f) => f.key === key)!;
      expect(spec.help).toBeTruthy();
    }
  });
});

describe('F5-UX-R2 — CNPJ/CPF primeiro', () => {
  it('tax_id is the first identification field in the shared form sections', () => {
    const section = SUPPLIER_FORM_SECTIONS.find(
      (s) => s.id === 'identification',
    )!;
    expect(section.fields[0].key).toBe('tax_id');
    expect(section.fields.map((f) => f.key).slice(0, 4)).toEqual([
      'tax_id',
      'person_type',
      'supplier_code',
      'supplier_store',
    ]);
  });

  it('tax_id is the first identification field in the create sections', () => {
    const section = SUPPLIER_CREATE_SECTIONS.find(
      (s) => s.id === 'identification',
    )!;
    expect(section.fields[0].key).toBe('tax_id');
    // CREATE não renderiza supplier_code (gerado pelo ERP).
    expect(section.fields.map((f) => f.key).slice(0, 3)).toEqual([
      'tax_id',
      'person_type',
      'supplier_store',
    ]);
  });

  it('keeps the field unique per section (no duplicated tax_id)', () => {
    const keys = SUPPLIER_FORM_SECTIONS.flatMap((s) =>
      s.fields.map((f) => f.key),
    );
    expect(new Set(keys).size).toBe(keys.length);
  });
});

describe('F5-UX-R2 — cobertura de Help contextual', () => {
  it('every registry field carries a specific, non-empty help text', () => {
    for (const spec of SUPPLIER_FIELD_REGISTRY) {
      expect(spec.help, ).toBeTruthy();
      expect(spec.help!.trim().length).toBeGreaterThanOrEqual(30);
      // Não é placeholder genérico nem repetição crua do label.
      expect(spec.help!.trim()).not.toBe(spec.label);
      expect(spec.help).not.toMatch(/^(ajuda|help|todo|tbd)[.!]?$/i);
    }
  });

  it('protected fields (código, loja, CNPJ/CPF) also carry help', () => {
    for (const key of ['supplier_code', 'supplier_store', 'tax_id'] as const) {
      const spec = SUPPLIER_FIELD_REGISTRY.find((f) => f.key === key)!;
      expect(spec.put).toBe('protected');
      expect(spec.help).toBeTruthy();
    }
  });
});

describe('F5-UX-R2 — CNPJ/CPF primeiro', () => {
  it('tax_id is the first identification field in the shared form sections', () => {
    const section = SUPPLIER_FORM_SECTIONS.find(
      (s) => s.id === 'identification',
    )!;
    expect(section.fields[0].key).toBe('tax_id');
    expect(section.fields.map((f) => f.key).slice(0, 4)).toEqual([
      'tax_id',
      'person_type',
      'supplier_code',
      'supplier_store',
    ]);
  });

  it('tax_id is the first identification field in the create sections', () => {
    const section = SUPPLIER_CREATE_SECTIONS.find(
      (s) => s.id === 'identification',
    )!;
    expect(section.fields[0].key).toBe('tax_id');
    // CREATE não renderiza supplier_code (gerado pelo ERP).
    expect(section.fields.map((f) => f.key).slice(0, 3)).toEqual([
      'tax_id',
      'person_type',
      'supplier_store',
    ]);
  });

  it('keeps the field unique per section (no duplicated tax_id)', () => {
    const keys = SUPPLIER_FORM_SECTIONS.flatMap((s) =>
      s.fields.map((f) => f.key),
    );
    expect(new Set(keys).size).toBe(keys.length);
  });
});

describe('F5-UX-R2 — cobertura de Help contextual', () => {
  it('every registry field carries a specific, non-empty help text', () => {
    for (const spec of SUPPLIER_FIELD_REGISTRY) {
      expect(spec.help, `help ausente em ${spec.key}`).toBeTruthy();
      expect(spec.help!.trim().length).toBeGreaterThanOrEqual(30);
      // Não é placeholder genérico nem repetição crua do label.
      expect(spec.help!.trim()).not.toBe(spec.label);
      expect(spec.help).not.toMatch(/^(ajuda|help|todo|tbd)[.!]?$/i);
    }
  });

  it('protected fields (código, loja, CNPJ/CPF) also carry help', () => {
    for (const key of ['supplier_code', 'supplier_store', 'tax_id'] as const) {
      const spec = SUPPLIER_FIELD_REGISTRY.find((f) => f.key === key)!;
      expect(spec.put).toBe('protected');
      expect(spec.help).toBeTruthy();
    }
  });
});

describe('F5-UX-R3 — metadados de catálogo TOTVS', () => {
  const CATALOGED: Record<string, string> = {
    state: 'states',
    country_code: 'countries',
    bacen_country_code: 'bacen-countries',
    payment_condition_code: 'payment-conditions',
    payment_method_code: 'payment-methods',
    financial_nature_code: 'financial-natures',
    accounting_account: 'accounting-accounts',
    city: 'municipalities',
    // X4.FIELDS.E6 — referências cadastrais Protheus
    carrier_code: 'carriers',
    segment_code: 'segments',
    administrator_code: 'administrators',
    linked_employee_code: 'employees',
    purchase_price_table_code: 'price-tables',
    linked_customer_code: 'customers',
    linked_customer_store: 'customers',
  };

  it('every cataloged field references a known BFF catalog kind', () => {
    const kinds = new Set(Object.values(CATALOGED));
    for (const spec of SUPPLIER_FIELD_REGISTRY) {
      if (spec.catalog) {
        expect(kinds).toContain(spec.catalog);
      }
    }
    for (const [field, kind] of Object.entries(CATALOGED)) {
      const spec = SUPPLIER_FIELD_REGISTRY.find((f) => f.key === field)!;
      expect(spec.catalog, `catálogo ausente em ${field}`).toBe(kind);
    }
  });

  it('municipalities catalog depends on state (UF) and never fires unfiltered', () => {
    const city = SUPPLIER_FIELD_REGISTRY.find((f) => f.key === 'city')!;
    expect(city.catalog).toBe('municipalities');
    expect(city.catalogDependsOn).toBe('state');
  });

  it('city_code is derived from the municipality pick (single source of truth)', () => {
    const code = SUPPLIER_FIELD_REGISTRY.find((f) => f.key === 'city_code')!;
    expect(code.catalogDerivedFrom).toBe('city');
    expect(code.catalog).toBeUndefined();
  });

  it('catalog selection still stores the contracted code, not the label', () => {
    // O draft guarda `spec.key → code`; labels nunca entram no payload.
    const spec = SUPPLIER_FIELD_REGISTRY.find(
      (f) => f.key === 'payment_condition_code',
    )!;
    const draft = {
      supplier_store: "01",
      person_type: "J",
      tax_id: "00000000000191",
      supplier_name: "FORNECEDOR TESTE",
      supplier_short_name: "FORN TESTE",
      address: "RUA X",
      district: "CENTRO",
      postal_code: "89120000",
      state: "SC",
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
      payment_condition_code: "001",
      payment_method_code: "01",
      accounting_account: "00000000",
      financial_nature_code: "0000",
      ...EMPTY_E3_DRAFT,
    };
    const body = buildCreateFornecedor(draft);
    expect(body.payment_condition_code).toBe('001');
    expect(spec.maxLength).toBe(3);
  });

  it('no field became multiselect — all catalog specs keep single code value', () => {
    for (const spec of SUPPLIER_FIELD_REGISTRY.filter((f) => f.catalog)) {
      expect(typeof spec.maxLength).toBe('number');
      // Cardinalidade 1 comprovada: campo escalar no payload POST.
      expect(spec.post).toBe(true);
    }
  });
});


describe('F5-UX-R3.1 — fallback honesto de descrição de catálogo', () => {
  it('nunca exibe "codigo · codigo" quando a descrição está ausente', () => {
    expect(catalogDisplayText('166', '')).toBe('166');
    expect(catalogDisplayText('166', null)).toBe('166');
    expect(catalogDisplayText('166', '166')).toBe('166');
    expect(catalogDisplayText('166', '7 DIAS')).toBe('7 DIAS · 166');
  });
});

describe('F5-UX-R4 — consulta de CEP e conciliação CC2', () => {
  it('normaliza CEP com e sem máscara para 8 dígitos', () => {
    expect(normalizePostalDigits('01310-100')).toBe('01310100');
    expect(normalizePostalDigits('89120000')).toBe('89120000');
    expect(isCompletePostalCode('01310-100')).toBe(true);
    expect(isCompletePostalCode('01310')).toBe(false);
  });

  it('deriva CC2_CODMUN dos 5 últimos dígitos do IBGE', () => {
    expect(deriveProtheusCityCode('3550308')).toBe('50308');
    expect(deriveProtheusCityCode('4218202')).toBe('18202');
    expect(deriveProtheusCityCode('')).toBe('');
    expect(deriveProtheusCityCode('123')).toBe('');
  });

  it('concilia município pelo código derivado do IBGE dentro da UF', async () => {
    const fetcher = async (_k: 'municipalities', o: { state?: string }) => ({
      items:
        o.state === 'SP'
          ? [{ code: '50308', label: 'SAO PAULO', disabled: false }]
          : [],
    });
    const out = await reconcileMunicipality('SP', '3550308', 'São Paulo', fetcher);
    expect(out).toEqual({
      status: 'matched',
      code: '50308',
      label: 'SAO PAULO',
    });
  });

  it('concilia pelo nome normalizado quando o IBGE não casa', async () => {
    const fetcher = async (_k: 'municipalities', o: { query?: string }) => ({
      items:
        o.query === '10001'
          ? []
          : [
              { code: '10001', label: 'LUIZ ALVES', disabled: false },
              { code: '10002', label: 'OUTRO', disabled: false },
            ],
    });
    const out = await reconcileMunicipality(
      'SC',
      '9999999',
      'Luiz Alves',
      fetcher,
    );
    expect(out).toEqual({
      status: 'matched',
      code: '10001',
      label: 'LUIZ ALVES',
    });
  });

  it('devolve múltiplos candidatos para escolha — nunca escolhe sozinho', async () => {
    const fetcher = async () => ({
      items: [
        { code: '11111', label: 'CENTRO DO NORTE', disabled: false },
        { code: '22222', label: 'CENTRO SUL', disabled: false },
      ],
    });
    const out = await reconcileMunicipality('SC', '', 'Centro', fetcher);
    expect(out.status).toBe('multiple');
  });

  it('sem correspondência não inventa código', async () => {
    const fetcher = async () => ({ items: [] });
    const out = await reconcileMunicipality('SC', '', 'Nada', fetcher);
    expect(out.status).toBe('unmatched');
  });
});

describe('X4.FIELDS.E3 — 29 campos homologados em E2', () => {
  const E3_KEYS = Object.keys(EMPTY_E3_DRAFT) as SupplierExtendedFieldKey[];
  /** E6: único campo sem PUT — upstream ignora A2_CLIENTE em update
   *  (companion imutável; loja via par composto é editável). */
  const E6_PENDING = ['linked_customer_code'] as const;

  it('registra os 29 campos criáveis — evidência por estado de PUT', () => {
    expect(E3_KEYS).toHaveLength(29);
    for (const key of E3_KEYS) {
      const spec = SUPPLIER_FIELD_REGISTRY.find((f) => f.key === key);
      expect(spec, key).toBeDefined();
      expect(spec!.post).toBe(true);
      expect(spec!.evidence, key).toBe(
        (E6_PENDING as readonly string[]).includes(key)
          ? 'post-matrix'
          : 'put-homologated',
      );
    }
  });

  it('E6: os 28 campos PUT-homologados viram editáveis na ficha E14', () => {
    const proven = E3_KEYS.filter(
      (key) => !(E6_PENDING as readonly string[]).includes(key),
    );
    expect(proven).toHaveLength(28);
    for (const key of proven) {
      const spec = SUPPLIER_FIELD_REGISTRY.find((f) => f.key === key)!;
      expect(spec.put, key).toBe('editable');
      expect(SUPPLIER_PUT_EDITABLE_KEYS).toContain(key);
    }
  });

  it('E6: o código do cliente vinculado permanece readonly (imutável upstream)', () => {
    for (const key of E6_PENDING) {
      const spec = SUPPLIER_FIELD_REGISTRY.find((f) => f.key === key)!;
      expect(spec.put, key).toBe('readonly');
      expect(SUPPLIER_PUT_EDITABLE_KEYS).not.toContain(key);
    }
  });

  it('E6: a loja do cliente vinculado forma par composto com o código', () => {
    const store = SUPPLIER_FIELD_REGISTRY.find(
      (f) => f.key === 'linked_customer_store',
    )!;
    expect(store.catalog).toBe('customers');
    expect(store.catalogCodeParam).toBe('linked_customer_code');
    expect(store.catalogValueField).toBe('store');
    const code = SUPPLIER_FIELD_REGISTRY.find(
      (f) => f.key === 'linked_customer_code',
    )!;
    expect(code.catalog).toBe('customers');
    expect(code.catalogPairField).toBe('linked_customer_store');
  });

  it('distribui os campos pelas seções canônicas — nunca um bloco único', () => {
    const sections = new Set(
      E3_KEYS.map(
        (key) => SUPPLIER_FIELD_REGISTRY.find((f) => f.key === key)!.section,
      ),
    );
    expect(sections).toEqual(
      new Set(['identification', 'address', 'contact', 'fiscal', 'purchasing']),
    );
  });

  it('encaminha os campos preenchidos no payload POST e omite vazios', () => {
    const body = buildCreateFornecedor({
      ...EMPTY_E3_DRAFT,
      supplier_store: '01',
      person_type: 'J',
      tax_id: '00000000000191',
      supplier_name: 'FORNECEDOR TESTE',
      supplier_short_name: 'FORN TESTE',
      address: 'RUA X',
      district: 'CENTRO',
      postal_code: '89120000',
      state: 'SC',
      city: 'TIMBO',
      city_code: '18202',
      area_code: '',
      phone: '',
      contact_name: '',
      email: '',
      state_registration: '',
      municipal_registration: '',
      country_code: '',
      bacen_country_code: '01058',
      rohs_indicator: 'N',
      payment_condition_code: '010',
      payment_method_code: '01',
      accounting_account: '00000000',
      financial_nature_code: '0000',
      cnae_code: '6201501',
      address_number: '385',
      linked_customer_code: '000123',
    });
    expect(body.cnae_code).toBe('6201501');
    expect(body.address_number).toBe('385');
    expect(body.linked_customer_code).toBe('000123');
    expect(body.po_box).toBeUndefined();
    expect(body.fax).toBeUndefined();
  });

  it('draft de edição carrega campos homologados e ignora o código imutável', () => {
    const detail = {
      sections: {
        fiscal: { cnae_code: '6201501', simp_regime_code: '1' },
        purchasing: {
          linked_customer_code: '000123',
          linked_customer_store: '01',
        },
        contact: { commercial_contact_name: 'MARIA' },
      },
    } as unknown as SupplierDetail;
    const draft = draftFromDetail(detail);
    // PUT comprovado → valores carregados no draft de edição.
    expect(draft.cnae_code).toBe('6201501');
    expect(draft.commercial_contact_name).toBe('MARIA');
    // E6: simp_regime_code e linked_customer_store homologados.
    expect(draft.simp_regime_code).toBe('1');
    expect(draft.linked_customer_store).toBe('01');
    // Código do cliente: imutável upstream → fora do draft e do PUT.
    for (const key of E6_PENDING) {
      expect(
        (draft as Record<string, string>)[key],
        key,
      ).toBeUndefined();
    }
  });
});

describe('S10 — hierarquia de ajuda hero/seção/campo', () => {
  const SECTION_IDS = [
    'identification',
    'address',
    'contact',
    'fiscal',
    'purchasing',
  ] as const;

  it('five sections have distinct, non-empty functional descriptions', () => {
    const values = SECTION_IDS.map((id) => supplierSectionDescriptions[id]);
    for (const v of values) {
      expect(v.trim().length).toBeGreaterThanOrEqual(30);
    }
    expect(new Set(values).size).toBe(SECTION_IDS.length);
  });

  it('section descriptions do not contain the removed generic form help', () => {
    const generic =
      'Todos os campos do contrato de cadastro';
    for (const id of SECTION_IDS) {
      expect(supplierSectionDescriptions[id]).not.toContain(generic);
    }
  });

  it('section ids cover both create and edit section sets (single source)', () => {
    const createIds = SUPPLIER_CREATE_SECTIONS.map((s) => s.id);
    const formIds = SUPPLIER_FORM_SECTIONS.map((s) => s.id);
    for (const id of createIds) {
      expect(supplierSectionDescriptions).toHaveProperty(id);
    }
    for (const id of formIds) {
      expect(supplierSectionDescriptions).toHaveProperty(id);
    }
  });

  it('create hero is create-specific and never promises enabled writes', () => {
    expect(SUPPLIERS_CONTENT.createTitle).toBe('Novo fornecedor');
    expect(SUPPLIERS_CONTENT.createDescription).toContain('CNPJ');
    expect(SUPPLIERS_CONTENT.createDescription).toContain('revise');
    expect(SUPPLIERS_CONTENT.createDescription).not.toMatch(
      /já está liberado|pode ser gravado agora|escrita habilitada/i,
    );
    expect(SUPPLIERS_CONTENT.createDescription).toContain(
      'quando autorizado',
    );
  });

  it('edit hero guidance is edit-specific and never promises enabled writes', () => {
    expect(SUPPLIERS_CONTENT.editModeTitle).toBe('Editando fornecedor');
    expect(SUPPLIERS_CONTENT.editHint).toContain('protegidos');
    expect(SUPPLIERS_CONTENT.editHint).toContain('revise');
    expect(SUPPLIERS_CONTENT.editHint).not.toMatch(
      /já está liberado|pode ser gravado agora|escrita habilitada/i,
    );
    // Hero de edição não replica o texto de criação.
    expect(SUPPLIERS_CONTENT.editHint).not.toBe(
      SUPPLIERS_CONTENT.createDescription,
    );
  });

  it('no UX text exposes the old technical length phrasing', () => {
    expect(
      supplierFieldMaxLengthHint(50),
    ).toBe('Máximo de 50 caracteres.');
    const allTexts = [
      ...Object.values(SUPPLIERS_CONTENT),
      ...Object.values(supplierSectionDescriptions),
    ];
    for (const t of allTexts) {
      expect(t).not.toContain('contrato de integração');
      expect(t).not.toMatch(/\bDTO\b|\bBFF\b|serializer/i);
    }
  });
});
