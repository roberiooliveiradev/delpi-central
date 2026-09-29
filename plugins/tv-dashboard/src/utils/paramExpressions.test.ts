import { describe, expect, it } from "vitest";

import type { ParamExpressionAst } from "@delpi/tv-dashboard-presentation";

import {
  PARAM_REF_PREFIX,
  PARAMETER_EXPRESSION_NODE_KINDS,
  buildExpressionParamValue,
  expressionAstDepth,
  expressionAstIncomplete,
  expressionAstNodeCount,
  isParamExpressionValue,
  isSupportedExpressionNode,
  paramAllowsExpression,
  paramFormatToReturnTypes,
  paramTypeToReturnTypes,
  parseFunctionSignature,
  readExpressionAst,
} from "./paramExpressions";

const MTD_START_AST: ParamExpressionAst = {
  kind: "call",
  value: "Date.StartOfMonth",
  children: [
    {
      kind: "call",
      value: "Date.AddMonths",
      children: [
        { kind: "identifier", value: "today" },
        { kind: "literal", value: -12 },
      ],
    },
  ],
};

const MTD_END_AST: ParamExpressionAst = {
  kind: "call",
  value: "Date.AddMonths",
  children: [
    { kind: "identifier", value: "today" },
    { kind: "literal", value: -12 },
  ],
};

describe("isParamExpressionValue / readExpressionAst", () => {
  it("reconhece o marker wire canônico", () => {
    const spec = buildExpressionParamValue(MTD_END_AST);
    expect(isParamExpressionValue(spec)).toBe(true);
    expect(readExpressionAst(spec)).toEqual(MTD_END_AST);
  });

  it("rejeita scalars, arrays e objetos sem marker", () => {
    expect(isParamExpressionValue("2026-09-01")).toBe(false);
    expect(isParamExpressionValue(42)).toBe(false);
    expect(isParamExpressionValue(null)).toBe(false);
    expect(isParamExpressionValue([1, 2])).toBe(false);
    expect(isParamExpressionValue({ kind: "call" })).toBe(false);
    expect(isParamExpressionValue({ expression: "not-an-object" })).toBe(false);
  });

  it("readExpressionAst devolve null para marker sem AST", () => {
    expect(readExpressionAst({ expression: { version: 1 } })).toBeNull();
  });
});

describe("buildExpressionParamValue round-trip", () => {
  it("preserva AST byte/semantic no ExpressionSpec v1", () => {
    const spec = buildExpressionParamValue(MTD_START_AST);
    expect(spec).toEqual({
      expression: { version: 1, expression: MTD_START_AST },
    });
    // hydrate → re-serialize = mesmo AST (invariante de round-trip §21)
    expect(readExpressionAst(spec)).toEqual(MTD_START_AST);
    expect(buildExpressionParamValue(readExpressionAst(spec)!)).toEqual(spec);
  });

  it("hidrata nested call + identifier + literal sem perda", () => {
    const spec = buildExpressionParamValue(MTD_START_AST);
    const hydrated = readExpressionAst(spec);
    expect(hydrated?.value).toBe("Date.StartOfMonth");
    expect(hydrated?.children?.[0]?.value).toBe("Date.AddMonths");
    expect(hydrated?.children?.[0]?.children?.[0]).toEqual({
      kind: "identifier",
      value: "today",
    });
    expect(hydrated?.children?.[0]?.children?.[1]).toEqual({
      kind: "literal",
      value: -12,
    });
  });
});

describe("paramAllowsExpression", () => {
  const field = { in: "query", expressionAllowed: true };

  it("permite param de query declarado", () => {
    expect(paramAllowsExpression("start_date", field)).toBe(true);
  });

  it("nega quando expressionAllowed=false", () => {
    expect(paramAllowsExpression("x", { ...field, expressionAllowed: false })).toBe(false);
  });

  it("nega param de path", () => {
    expect(paramAllowsExpression("id", { in: "path" })).toBe(false);
  });

  it("nega fixedQueryParam", () => {
    expect(paramAllowsExpression("fixed", field, new Set(["fixed"]))).toBe(false);
  });

  it("nega param fora do schema", () => {
    expect(paramAllowsExpression("ghost", undefined)).toBe(false);
  });
});

describe("AST metrics / completeness", () => {
  it("conta profundidade e nós do nested call", () => {
    expect(expressionAstDepth(MTD_START_AST)).toBe(3);
    expect(expressionAstNodeCount(MTD_START_AST)).toBe(4);
    expect(expressionAstDepth(null)).toBe(0);
  });

  it("detecta nós incompletos (call sem função / arg vazio)", () => {
    expect(expressionAstIncomplete(MTD_START_AST)).toBe(false);
    expect(expressionAstIncomplete({ kind: "call", value: "" })).toBe(true);
    expect(
      expressionAstIncomplete({
        kind: "call",
        value: "Date.AddMonths",
        children: [{ kind: "identifier", value: "today" }, { kind: "literal" }],
      }),
    ).toBe(true);
    expect(expressionAstIncomplete({ kind: "identifier", value: "" })).toBe(true);
    expect(
      expressionAstIncomplete({ kind: "if", children: [{ kind: "literal", value: 1 }] }),
    ).toBe(true);
  });

  it("suporta apenas kinds PARAMETER-phase", () => {
    for (const kind of PARAMETER_EXPRESSION_NODE_KINDS) {
      expect(isSupportedExpressionNode({ kind })).toBe(true);
    }
    // DERIVED-only nunca entra no editor de param.
    for (const kind of ["field", "record", "recordField", "each", "type"]) {
      expect(isSupportedExpressionNode({ kind })).toBe(false);
    }
  });
});

describe("parseFunctionSignature", () => {
  it("extrai args + optional + return type", () => {
    const parsed = parseFunctionSignature(
      "Date.AddDays(value as date, count as number) as date",
    );
    expect(parsed.args).toEqual(["value as date", "count as number"]);
    expect(parsed.optionalFrom).toBe(2);
    expect(parsed.returnType).toBe("date");
  });

  it("marca sufixo optional", () => {
    const parsed = parseFunctionSignature("Text.Format(fmt, optional arg1) as text");
    expect(parsed.args).toEqual(["fmt", "arg1"]);
    expect(parsed.optionalFrom).toBe(1);
    expect(parsed.returnType).toBe("text");
  });

  it("signature vazia/malformada não quebra", () => {
    expect(parseFunctionSignature(null)).toEqual({
      args: [],
      optionalFrom: 0,
      returnType: null,
    });
  });
});

describe("type-aware authoring hints", () => {
  it("mapeia tipos do schema para retornos esperados", () => {
    expect(paramTypeToReturnTypes("number")).toEqual(new Set(["number"]));
    expect(paramTypeToReturnTypes("boolean")).toEqual(new Set(["logical", "boolean"]));
    expect(paramTypeToReturnTypes("string")).toBeNull();
    expect(paramFormatToReturnTypes("date")).toEqual(new Set(["date"]));
    expect(paramFormatToReturnTypes(undefined)).toBeNull();
  });

  it("param ref prefix canônico", () => {
    expect(PARAM_REF_PREFIX).toBe("param.");
  });
});
