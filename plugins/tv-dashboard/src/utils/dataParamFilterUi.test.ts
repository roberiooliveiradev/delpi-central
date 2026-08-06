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
  unset: "Não definido aqui",
  diverged: "Valores diferentes",
  allBranches: "Todas as filiais",
};

describe("dataParamFilterUi", () => {
  it("resolveFilterLayer: multi explícito; hydrate false ⇒ aggregate", () => {
    expect(resolveFilterLayer("multi", false)).toBe("multi");
    expect(resolveFilterLayer(undefined, false)).toBe("aggregate");
    expect(resolveFilterLayer(undefined, true)).toBe("source");
  });

  it("opção vazia padronizada «Não definido aqui» em todas as camadas", () => {
    expect(resolveFilterClearLabel("multi", labels)).toBe("Não definido aqui");
    expect(resolveFilterClearLabel("source", labels)).toBe("Não definido aqui");
    expect(resolveFilterClearLabel("aggregate", labels)).toBe("Não definido aqui");
    expect(resolveFilterClearLabel("source", labels, { inherited: true })).toBe(
      "Herdado do slide",
    );
  });

  it("divergência usa sentinel para o select poder escolher Não definido", () => {
    expect(resolveFilterSelectValue("this_week", true)).toBe(DIVERGED_FILTER_SELECT_VALUE);
    expect(resolveFilterSelectValue("this_week", false)).toBe("this_week");
    expect(resolveFilterSelectValue("", true)).toBe(DIVERGED_FILTER_SELECT_VALUE);
  });

  it("opções: status divergente + Não definido + domínio", () => {
    const options = buildFilterSelectOptions(
      [
        { value: "01", label: "Filial 01" },
        { value: "02", label: "Filial 02" },
      ],
      {
        clearLabel: "Não definido aqui",
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
    expect(options.find((item) => item.value === "")?.label).toBe("Não definido aqui");
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

  it("Filial: opção vazia é «Não definido aqui» (consolidado fica em all)", () => {
    expect(
      resolveBranchEmptyLabel("source", {
        allowConsolidated: true,
        labels,
      }),
    ).toBe("Não definido aqui");
    expect(
      resolveBranchEmptyLabel("aggregate", {
        allowConsolidated: true,
        labels,
      }),
    ).toBe("Não definido aqui");
    expect(
      resolveBranchEmptyLabel("multi", {
        allowConsolidated: false,
        labels,
      }),
    ).toBe("Não definido aqui");
    expect(
      resolveBranchEmptyLabel("source", {
        allowConsolidated: true,
        inherited: true,
        labels,
      }),
    ).toBe("Herdado do slide");
  });

  it("placeholder de text usa «Não definido aqui» em source e aggregate", () => {
    expect(
      resolveFilterTextPlaceholder(
        { diverged: false, aggregateLayer: false, inherited: false },
        labels,
      ),
    ).toBe("Não definido aqui");
    expect(
      resolveFilterTextPlaceholder(
        { diverged: false, aggregateLayer: true, inherited: false },
        labels,
      ),
    ).toBe("Não definido aqui");
  });
});
