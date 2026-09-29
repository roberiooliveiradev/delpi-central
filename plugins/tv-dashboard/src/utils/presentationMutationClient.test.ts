import { describe, expect, it } from "vitest";

import { splitBlockForAck } from "./presentationMutationClient";
import { buildExpressionParamValue } from "./paramExpressions";

const EXPR = buildExpressionParamValue({
  kind: "identifier",
  value: "today",
});

const SOURCE_BLOCK = {
  id: "src-1",
  type: "data_source",
  dataBinding: {
    operationId: "op_x",
    params: {
      branch: "01",
      start_date: EXPR,
    },
    displayMode: "kpi",
  },
};

describe("splitBlockForAck", () => {
  it("separa ExpressionSpec de scalar params", () => {
    const { block, expressionSet } = splitBlockForAck(SOURCE_BLOCK);
    expect(expressionSet).toEqual({ start_date: EXPR });
    const binding = block.dataBinding as { params: Record<string, unknown> };
    expect(binding.params).toEqual({ branch: "01" });
    // demais campos preservados
    expect(block.id).toBe("src-1");
    expect((block.dataBinding as { operationId: string }).operationId).toBe("op_x");
  });

  it("bloco sem expression passa intacto (expressionSet vazio)", () => {
    const { block, expressionSet } = splitBlockForAck({
      id: "b2",
      dataBinding: { params: { branch: "01" } },
    });
    expect(expressionSet).toEqual({});
    expect(block).toEqual({ id: "b2", dataBinding: { params: { branch: "01" } } });
  });

  it("bloco sem dataBinding/params passa intacto", () => {
    const plain = { id: "t1", type: "text", content: "oi" };
    const { block, expressionSet } = splitBlockForAck(plain);
    expect(block).toEqual(plain);
    expect(expressionSet).toEqual({});
  });

  it("não muta o bloco original", () => {
    const clone = structuredClone(SOURCE_BLOCK);
    splitBlockForAck(SOURCE_BLOCK);
    expect(SOURCE_BLOCK).toEqual(clone);
  });
});
