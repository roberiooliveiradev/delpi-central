import { describe, expect, it } from "vitest";

import { resolveDataCellSemantics } from "./dataCellSemantics";

describe("resolveDataCellSemantics", () => {
  it.each([
    [null, "null", "null"],
    [undefined, "null", "null"],
    ["", "empty", "vazio"],
    [0, "value", "0"],
    [false, "value", "false"],
  ] as const)("classifica %p como %s", (value, kind, displayText) => {
    expect(resolveDataCellSemantics(value)).toMatchObject({ kind, displayText });
  });

  it("distingue campo ausente de valor nulo", () => {
    expect(resolveDataCellSemantics(undefined, { present: false })).toMatchObject({
      kind: "missing",
      displayText: "ausente",
      copyText: "ausente",
    });
  });

  it("preserva erro estruturado sem renderizar object Object", () => {
    expect(
      resolveDataCellSemantics({
        error: { code: "m.invalid_cast", message: "Texto não é número." },
      }),
    ).toMatchObject({
      kind: "error",
      displayText: "error",
      copyText: "#ERROR:m.invalid_cast",
      ariaLabel: "Erro: Texto não é número.",
      title: "Texto não é número.",
    });
  });

  it("serializa objetos válidos de forma legível", () => {
    expect(resolveDataCellSemantics({ a: 1 }).displayText).toBe('{"a":1}');
  });
});
