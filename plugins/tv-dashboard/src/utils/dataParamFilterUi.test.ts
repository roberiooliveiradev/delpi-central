import { describe, expect, it } from "vitest";

import {
  DIVERGED_FILTER_SELECT_VALUE,
  buildFilterSelectOptions,
  canClearFilterValue,
  normalizeFilterSelectChange,
  resolveBranchEmptyLabel,
  resolveFilterClearLabel,
  resolveFilterLayer,
  resolveFilterSelectValue,
  resolveFilterTextPlaceholder,
} from "./dataParamFilterUi";

const labels = {
  clear: "Limpar filtro",
  unset: "Não definido (usa a fonte)",
  diverged: "Valores diferentes",
  allBranches: "Todas as filiais",
};

describe("dataParamFilterUi", () => {
  it("resolveFilterLayer: multi explícito; hydrate false ⇒ aggregate", () => {
    expect(resolveFilterLayer("multi", false)).toBe("multi");
    expect(resolveFilterLayer(undefined, false)).toBe("aggregate");
    expect(resolveFilterLayer(undefined, true)).toBe("source");
  });

  it("clear label nunca é «Valores diferentes»", () => {
    expect(resolveFilterClearLabel("multi", labels)).toBe("Limpar filtro");
    expect(resolveFilterClearLabel("source", labels)).toBe("Limpar filtro");
    expect(resolveFilterClearLabel("aggregate", labels)).toBe(
      "Não definido (usa a fonte)",
    );
    expect(resolveFilterClearLabel("source", labels, { inherited: true })).toBe(
      "Herdado do slide",
    );
  });

  it("divergência usa sentinel para o select poder escolher Limpar", () => {
    expect(resolveFilterSelectValue("this_week", true)).toBe(DIVERGED_FILTER_SELECT_VALUE);
    expect(resolveFilterSelectValue("this_week", false)).toBe("this_week");
    expect(resolveFilterSelectValue("", true)).toBe(DIVERGED_FILTER_SELECT_VALUE);
  });

  it("opções: status divergente + Limpar + domínio", () => {
    const options = buildFilterSelectOptions(
      [
        { value: "01", label: "Filial 01" },
        { value: "02", label: "Filial 02" },
      ],
      {
        clearLabel: "Limpar filtro",
        diverged: true,
        divergedLabel: "Valores diferentes",
      },
    );
    expect(options.map((item) => item.value)).toEqual([
      DIVERGED_FILTER_SELECT_VALUE,
      "",
      "01",
      "02",
    ]);
    expect(options.find((item) => item.value === "")?.label).toBe("Limpar filtro");
    expect(options.find((item) => item.value === DIVERGED_FILTER_SELECT_VALUE)?.label).toBe(
      "Valores diferentes",
    );
  });

  it("normalize ignora reescolha do status divergente", () => {
    expect(normalizeFilterSelectChange(DIVERGED_FILTER_SELECT_VALUE)).toBeNull();
    expect(normalizeFilterSelectChange("")).toBe("");
    expect(normalizeFilterSelectChange("01")).toBe("01");
  });

  it("× de limpar aparece também quando divergente (sem valor único)", () => {
    expect(canClearFilterValue({ diverged: true, hasStoredValue: false })).toBe(true);
    expect(canClearFilterValue({ diverged: false, hasStoredValue: false })).toBe(false);
    expect(canClearFilterValue({ diverged: false, hasStoredValue: true })).toBe(true);
    expect(
      canClearFilterValue({ diverged: true, hasStoredValue: true, locked: true }),
    ).toBe(false);
  });

  it("Filial opcional usa «Todas as filiais» quando consolidado é permitido", () => {
    expect(
      resolveBranchEmptyLabel("source", {
        allowConsolidated: true,
        labels,
      }),
    ).toBe("Todas as filiais");
    expect(
      resolveBranchEmptyLabel("aggregate", {
        allowConsolidated: true,
        labels,
      }),
    ).toBe("Não definido (usa a fonte)");
    expect(
      resolveBranchEmptyLabel("source", {
        allowConsolidated: false,
        labels,
      }),
    ).toBe("Limpar filtro");
  });
});
