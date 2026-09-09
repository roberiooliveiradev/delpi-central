import { describe, expect, it } from "vitest";

import { buildFieldKeyMapRows } from "./fieldKeyMap";

describe("fieldKeyMap", () => {
  it("mapeia cabeçalho humanizado para key técnica", () => {
    expect(
      buildFieldKeyMapRows([
        { key: "nome_operador", label: "Operador" },
        { key: "eficiencia_percentual", label: "Eficiência (%)" },
      ]),
    ).toEqual([
      ["Cabeçalho", "Campo técnico"],
      ["Operador", "nome_operador"],
      ["Eficiência (%)", "eficiencia_percentual"],
    ]);
  });
});
