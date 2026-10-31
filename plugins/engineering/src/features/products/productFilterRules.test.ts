import { describe, expect, it } from "vitest";

import type { ProductsListUrlState } from "./productRoutes";
import {
  applyRulesToListState,
  FIELD_ORDER,
  firstAvailableField,
  isValidRule,
  rulesFromListState,
  type ProductFilterRule,
} from "./productFilterRules";

const BASE: ProductsListUrlState = {
  code: "",
  description: "",
  customer_reference: "",
  subgroup: "",
  groups: [],
  types: [],
  sort: null,
  direction: "asc",
  page: 1,
};

describe("rulesFromListState", () => {
  it("estado limpo não gera critérios", () => {
    expect(rulesFromListState(BASE)).toEqual([]);
  });

  it("uma regra por campo preenchido — quick e avançado no mesmo modelo", () => {
    const rules = rulesFromListState({
      ...BASE,
      code: "90",
      description: "ANEL",
      customer_reference: "REF-1",
      subgroup: "02",
      groups: ["3019", "3020"],
      types: ["PA"],
    });
    expect(rules).toEqual([
      { field: "code", text: "90", values: [] },
      { field: "description", text: "ANEL", values: [] },
      { field: "groups", text: "", values: ["3019", "3020"] },
      { field: "types", text: "", values: ["PA"] },
      { field: "customer_reference", text: "REF-1", values: [] },
      { field: "subgroup", text: "02", values: [] },
    ]);
  });

  it("espaços em branco não contam como filtro aplicado", () => {
    expect(rulesFromListState({ ...BASE, code: "   " })).toEqual([]);
  });
});

describe("applyRulesToListState", () => {
  it("reseta campos sem critério e preserva sort/page", () => {
    const next = applyRulesToListState(
      {
        ...BASE,
        code: "11",
        groups: ["3019"],
        sort: "code",
        direction: "desc",
        page: 3,
      },
      [{ field: "subgroup", text: "02", values: [] }],
    );
    expect(next).toEqual({
      ...BASE,
      code: "",
      groups: [],
      subgroup: "02",
      sort: "code",
      direction: "desc",
      page: 3,
    });
  });

  it("multiselect replica a lista de valores (sem alias compartilhado)", () => {
    const values = ["3019", "3020"];
    const next = applyRulesToListState(BASE, [
      { field: "groups", text: "", values },
    ]);
    expect(next.groups).toEqual(values);
    expect(next.groups).not.toBe(values);
  });

  it("aplica todos os campos suportados", () => {
    const next = applyRulesToListState(BASE, [
      { field: "code", text: "100", values: [] },
      { field: "description", text: "CABO", values: [] },
      { field: "customer_reference", text: "REF", values: [] },
      { field: "subgroup", text: " 02 ", values: [] },
      { field: "groups", text: "", values: ["9026"] },
      { field: "types", text: "", values: ["MP", "PI"] },
    ]);
    expect(next.code).toBe("100");
    expect(next.description).toBe("CABO");
    expect(next.customer_reference).toBe("REF");
    expect(next.subgroup).toBe("02");
    expect(next.groups).toEqual(["9026"]);
    expect(next.types).toEqual(["MP", "PI"]);
  });
});

describe("isValidRule", () => {
  it("texto vazio e seleção vazia são inválidos", () => {
    expect(isValidRule({ field: "code", text: " ", values: [] })).toBe(false);
    expect(isValidRule({ field: "groups", text: "", values: [] })).toBe(false);
  });

  it("texto preenchido ou valor selecionado são válidos", () => {
    expect(isValidRule({ field: "code", text: "1", values: [] })).toBe(true);
    expect(
      isValidRule({ field: "types", text: "", values: ["PA"] }),
    ).toBe(true);
  });
});

describe("firstAvailableField", () => {
  it("retorna o primeiro campo não utilizado na ordem do catálogo", () => {
    const rules: ProductFilterRule[] = [
      { field: "code", text: "1", values: [] },
    ];
    expect(firstAvailableField(rules)).toBe("description");
  });

  it("esgotado o catálogo retorna ao primeiro campo", () => {
    const rules: ProductFilterRule[] = FIELD_ORDER.map((field) => ({
      field,
      text: "x",
      values: [],
    }));
    expect(firstAvailableField(rules)).toBe(FIELD_ORDER[0]);
  });
});

describe("roundtrip estado ↔ critérios", () => {
  it("aplicar os critérios derivados do estado devolve o mesmo estado", () => {
    const state: ProductsListUrlState = {
      ...BASE,
      code: "30",
      description: "ANEL",
      customer_reference: "R1",
      subgroup: "02",
      groups: ["3019"],
      types: ["MP", "PA"],
      sort: "code",
      direction: "desc",
      page: 2,
    };
    expect(applyRulesToListState(state, rulesFromListState(state))).toEqual(
      state,
    );
  });
});
