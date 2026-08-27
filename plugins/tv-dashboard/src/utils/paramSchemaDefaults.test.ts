import { describe, expect, it } from "vitest";

import {
  isOptionalParamSpec,
  shouldApplyCatalogDefaultParam,
  shouldApplySchemaDefault,
} from "./paramSchemaDefaults";

describe("paramSchemaDefaults", () => {
  it("trata ausência de optional como opcional", () => {
    expect(isOptionalParamSpec({})).toBe(true);
    expect(isOptionalParamSpec({ optional: true })).toBe(true);
    expect(isOptionalParamSpec({ optional: false })).toBe(false);
  });

  it("não aplica schema.default em filtros opcionais (enum, bool, int)", () => {
    expect(
      shouldApplySchemaDefault("group_by", {
        optional: true,
        default: "customer",
        enum: ["none", "customer"],
      }),
    ).toBe(false);
    expect(
      shouldApplySchemaDefault("only_positive", { optional: true, default: true }),
    ).toBe(false);
    expect(
      shouldApplySchemaDefault("page", { optional: true, default: 1 }),
    ).toBe(false);
  });

  it("aplica schema.default só em obrigatórios", () => {
    expect(
      shouldApplySchemaDefault("granularity", {
        optional: false,
        default: "day",
        enum: ["day", "week"],
      }),
    ).toBe(true);
  });

  it("defaultParams não força chave opcional do schema", () => {
    expect(
      shouldApplyCatalogDefaultParam("sort", {
        optional: true,
        default: "stock_value_desc",
        enum: ["stock_value_desc"],
      }),
    ).toBe(false);
    expect(shouldApplyCatalogDefaultParam("periodDays", undefined)).toBe(false);
    expect(shouldApplyCatalogDefaultParam("fixedKnob", undefined)).toBe(true);
  });
});
