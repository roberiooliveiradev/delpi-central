import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  createDashboardFilterRulesBuilder,
  createDashboardSortLevelsBuilder,
  createDashboardToolbarPopover,
  type DashboardFilterFieldDescriptor,
  type DashboardFilterRule,
  type DashboardSortLevel,
} from "./DashboardListTools";

const SORT_LABELS = {
  ariaLabel: "Ordenação",
  fieldHint: "Campo da ordenação.",
  directionLabel: "Direção",
  directionHint: "Direção do nível.",
  levelHint: "Prioridade do nível.",
  levelAriaLabel: (level: number) => `Nível ${level}`,
  removeLevelHint: "Remove o nível.",
  removeLevelAriaLabel: (level: number) => `Remover nível ${level}`,
  addLevelHint: "Adiciona nível.",
  addLevelLabel: "Adicionar nível",
  addLevelAriaLabel: "Adicionar nível de ordenação",
  applyHint: "Aplica a ordenação.",
  applyLabel: "Aplicar",
  applyAriaLabel: "Aplicar ordenação",
  directionAscLabel: "Crescente",
  directionDescLabel: "Decrescente",
};

const FILTER_LABELS = {
  ariaLabel: "Filtros",
  fieldLabel: "Campo",
  fieldHint: "Campo do critério.",
  operatorHint: "Operador do critério.",
  valueLabel: "Valor",
  valueHint: "Valor do critério.",
  removeRuleHint: "Remove o critério.",
  removeRuleAriaLabel: "Remover critério",
  addRuleHint: "Adiciona critério.",
  addRuleLabel: "Adicionar critério",
  addRuleAriaLabel: "Adicionar critério",
  clearHint: "Limpa critérios.",
  clearLabel: "Limpar",
  clearAriaLabel: "Limpar critérios",
  applyHint: "Aplica filtros.",
  applyLabel: "Aplicar",
  applyAriaLabel: "Aplicar filtros",
};

const FIELDS: DashboardFilterFieldDescriptor[] = [
  {
    key: "status",
    label: "Status",
    operator: "eq",
    input: "select",
    options: [
      { value: "open", label: "Aberto" },
      { value: "done", label: "Concluído" },
    ],
  },
  {
    key: "subject",
    label: "Assunto",
    operator: "contains",
    input: "text",
  },
];

afterEach(() => {
  cleanup();
});

describe("createDashboardToolbarPopover", () => {
  const Popover = createDashboardToolbarPopover({ prefix: "delpi-ui" });

  it("abre o painel ancorado e fecha pelo close do render-prop", () => {
    render(
      <Popover
        label="Filtros"
        panelTitle="Filtrar lista"
        panelHint="Combine critérios."
        wide
      >
        {(close) => (
          <button type="button" onClick={close}>
            fechar
          </button>
        )}
      </Popover>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Filtros" }));
    expect(screen.getByText("Filtrar lista")).toBeTruthy();
    expect(screen.getByText("Combine critérios.")).toBeTruthy();
    const trigger = screen.getByRole("button", { name: "Filtros" });
    expect(trigger.getAttribute("aria-expanded")).toBe("true");

    fireEvent.click(screen.getByRole("button", { name: "fechar" }));
    expect(trigger.getAttribute("aria-expanded")).toBe("false");
  });
});

describe("createDashboardSortLevelsBuilder", () => {
  const SortBuilder = createDashboardSortLevelsBuilder({
    prefix: "delpi-ui",
    labels: SORT_LABELS,
  });
  const options = [
    { value: "createdAt", label: "Abertura" },
    { value: "status", label: "Status" },
  ];

  it("adiciona nível até o teto e aplica", () => {
    const levels: DashboardSortLevel[] = [
      { field: "createdAt", direction: "desc" },
    ];
    const onChange = vi.fn();
    const onApply = vi.fn();
    render(
      <SortBuilder
        levels={levels}
        options={options}
        onChange={onChange}
        onApply={onApply}
      />,
    );

    fireEvent.click(
      screen.getByRole("button", { name: "Adicionar nível de ordenação" }),
    );
    expect(onChange).toHaveBeenCalledWith([
      { field: "createdAt", direction: "desc" },
      { field: "status", direction: "asc" },
    ]);

    fireEvent.click(screen.getByRole("button", { name: "Aplicar ordenação" }));
    expect(onApply).toHaveBeenCalledTimes(1);
  });

  it("oculta remover quando há um único nível", () => {
    render(
      <SortBuilder
        levels={[{ field: "createdAt", direction: "desc" }]}
        options={options}
        onChange={() => undefined}
        onApply={() => undefined}
      />,
    );
    expect(
      screen.queryByRole("button", { name: "Remover nível 1" }),
    ).toBeNull();
  });
});

describe("createDashboardFilterRulesBuilder", () => {
  const FilterBuilder = createDashboardFilterRulesBuilder({
    prefix: "delpi-ui",
    labels: FILTER_LABELS,
  });

  it("adiciona critério a partir do catálogo e aplica", () => {
    const rules: DashboardFilterRule[] = [];
    const onChange = vi.fn();
    const onApply = vi.fn();
    render(
      <FilterBuilder
        rules={rules}
        fields={FIELDS}
        onChange={onChange}
        onApply={onApply}
        onClear={() => undefined}
        createRuleId={() => "rule-test"}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Adicionar critério" }));
    expect(onChange).toHaveBeenCalledWith([
      { id: "rule-test", field: "status", operator: "eq", value: "" },
    ]);

    fireEvent.click(screen.getByRole("button", { name: "Aplicar filtros" }));
    expect(onApply).toHaveBeenCalledTimes(1);
  });

  it("remove critério e limpa pelo onClear", () => {
    const onChange = vi.fn();
    const onClear = vi.fn();
    render(
      <FilterBuilder
        rules={[
          { id: "r1", field: "status", operator: "eq", value: "open" },
        ]}
        fields={FIELDS}
        onChange={onChange}
        onApply={() => undefined}
        onClear={onClear}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Remover critério" }));
    expect(onChange).toHaveBeenCalledWith([]);

    fireEvent.click(screen.getByRole("button", { name: "Limpar critérios" }));
    expect(onClear).toHaveBeenCalledTimes(1);
  });

  it("mostra o rótulo do operador do campo", () => {
    render(
      <FilterBuilder
        rules={[
          { id: "r1", field: "subject", operator: "contains", value: "abc" },
        ]}
        fields={FIELDS}
        onChange={() => undefined}
        onApply={() => undefined}
        onClear={() => undefined}
      />,
    );
    expect(screen.getByText("contém")).toBeTruthy();
  });
});
