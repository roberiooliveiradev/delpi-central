import { describe, expect, it } from "vitest";

import { buildIdeaMonthFilter, detectIdeaMonthFilter } from "./ideaMonthFilter";

describe("filtro mensal de ideias do Kaizometro", () => {
  it.each([
    ["2026-08", "2026-08-31"],
    ["2026-09", "2026-09-30"],
    ["2026-02", "2026-02-28"],
    ["2024-02", "2024-02-29"],
  ])("filtra o mes completo %s pela data de recebimento", (month, dateEnd) => {
    const filters = buildIdeaMonthFilter(month);
    expect(filters).toEqual({
      dateFields: ["recebimento"],
      dateStart: `${month}-01`,
      dateEnd,
    });
    expect(detectIdeaMonthFilter(filters)).toBe(month);
  });

  it.each(["", "2026-00", "2026-13", "2026-1", "invalido"])(
    "limpa o filtro quando o mes nao e valido (%s)",
    (month) => {
      expect(buildIdeaMonthFilter(month)).toEqual({
        dateFields: [],
        dateStart: "",
        dateEnd: "",
      });
    },
  );

  it("nao marca um mes quando a coluna de data ou o intervalo foi alterado", () => {
    expect(detectIdeaMonthFilter({
      dateFields: ["criacao"],
      dateStart: "2026-08-01",
      dateEnd: "2026-08-31",
    })).toBe("");
    expect(detectIdeaMonthFilter({
      dateFields: ["recebimento"],
      dateStart: "2026-08-02",
      dateEnd: "2026-08-31",
    })).toBe("");
    expect(detectIdeaMonthFilter({
      dateFields: ["recebimento"],
      dateStart: "2026-08-01",
      dateEnd: "2026-08-15",
    })).toBe("");
    expect(detectIdeaMonthFilter({
      dateFields: ["recebimento", "criacao"],
      dateStart: "2026-08-01",
      dateEnd: "2026-08-31",
    })).toBe("");
  });
});
