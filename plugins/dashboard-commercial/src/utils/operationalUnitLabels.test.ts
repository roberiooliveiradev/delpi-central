import { describe, expect, it } from "vitest";

import {
  formatOperationalUnitCode,
  normalizeOperationalUnitCode,
} from "./operationalUnitLabels";
import { parseCommercialBranchCsv } from "./commercialClientFilters";
import { buildCommercialDetailPath } from "../constants/routes";

describe("operationalUnitLabels", () => {
  it("formata código para rótulo na UI", () => {
    expect(formatOperationalUnitCode("01")).toBe("Santa Catarina");
    expect(formatOperationalUnitCode("02")).toBe("Espírito Santo");
  });

  it("normaliza rótulo de volta ao código TOTVS", () => {
    expect(normalizeOperationalUnitCode("Santa Catarina")).toBe("01");
    expect(normalizeOperationalUnitCode("espírito santo")).toBe("02");
    expect(normalizeOperationalUnitCode("01")).toBe("01");
  });
});

describe("commercial branch URL", () => {
  it("parseia branch legível na query como código", () => {
    expect(parseCommercialBranchCsv("Santa Catarina")).toEqual(["01"]);
  });

  it("monta detalhe da OV com branch numérico e revision", () => {
    const path = buildCommercialDetailPath("000120", {
      dateStart: "2026-05-01",
      dateEnd: "2026-05-31",
      competence: "2026-05",
      branches: [],
      customerSegment: "",
      proposalBranch: "01",
      revision: "0",
    });

    expect(path).toContain("/ov/000120?");
    expect(path).toContain("branch=01");
    expect(path).toContain("revision=0");
  });
});
