// @vitest-environment happy-dom
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { ParamExpressionSupport } from "../hooks/useParamExpressionCapability";
import { buildExpressionParamValue } from "../utils/paramExpressions";
import { DataParamFields, type DataParamSchema } from "./DataParamFields";

afterEach(() => cleanup());

const SCHEMA: DataParamSchema = {
  start_date: { type: "string", format: "date", label: "Início" },
  end_date: { type: "string", format: "date", label: "Fim" },
  branch: { type: "string", enum: ["01", "02"] },
};

const SUPPORT: ParamExpressionSupport = {
  enabled: true,
  loading: false,
  functions: [
    {
      name: "Date.AddMonths",
      kind: "scalar",
      signature: "Date.AddMonths(value, months) as date",
      parameters: ["value", "months"],
    },
  ],
  registryVersion: "1",
};

const EXPR = buildExpressionParamValue({
  kind: "identifier",
  value: "today",
});

function modeChips(container: HTMLElement) {
  return container.querySelectorAll(".td-data-param-mode");
}

describe("DataParamFields — expression capability gating", () => {
  it("sem capability nenhum chip de modo aparece", () => {
    const { container } = render(
      <DataParamFields schema={SCHEMA} values={{}} onChange={vi.fn()} />,
    );
    expect(modeChips(container)).toHaveLength(0);
  });

  it("com capability, params elegíveis mostram chips Valor fixo|Expressão", () => {
    const { container } = render(
      <DataParamFields
        schema={SCHEMA}
        values={{}}
        expressionSupport={SUPPORT}
        onChange={vi.fn()}
      />,
    );
    expect(modeChips(container).length).toBe(3);
    expect(screen.getAllByRole("button", { name: "Expressão" }).length).toBe(3);
  });

  it("expressionAllowed=false no schema esconde o modo para aquele param", () => {
    const { container } = render(
      <DataParamFields
        schema={{ ...SCHEMA, end_date: { ...SCHEMA.end_date, expressionAllowed: false } }}
        values={{}}
        expressionSupport={SUPPORT}
        onChange={vi.fn()}
      />,
    );
    expect(modeChips(container)).toHaveLength(2);
  });

  it("param de path nunca mostra modo expressão", () => {
    const { container } = render(
      <DataParamFields
        schema={{ ...SCHEMA, start_date: { ...SCHEMA.start_date, in: "path" } }}
        values={{}}
        expressionSupport={SUPPORT}
        onChange={vi.fn()}
      />,
    );
    expect(modeChips(container)).toHaveLength(2);
  });

  it("fixedQueryParam nunca mostra modo expressão", () => {
    const { container } = render(
      <DataParamFields
        schema={SCHEMA}
        values={{}}
        expressionSupport={SUPPORT}
        fixedQueryParams={{ branch: "01" }}
        onChange={vi.fn()}
      />,
    );
    // branch sai do visibleParamSchema? Não — schema direto; predicate nega.
    expect(modeChips(container)).toHaveLength(2);
  });
});

describe("DataParamFields — preset × expressão (conflito deliberado)", () => {
  it("trocar para Expressão em start_date limpa dateRangePreset no mesmo patch", () => {
    const onChange = vi.fn();
    render(
      <DataParamFields
        schema={SCHEMA}
        values={{ dateRangePreset: "this_month" }}
        expressionSupport={SUPPORT}
        onChange={onChange}
      />,
    );
    // start_date sem valor → switch direto (sem confirmação).
    fireEvent.click(screen.getAllByRole("button", { name: "Expressão" })[0]);
    expect(onChange).toHaveBeenCalledTimes(1);
    const updates = onChange.mock.calls[0][0];
    expect(updates.dateRangePreset).toBe("");
    expect(updates.start_date).toEqual(
      buildExpressionParamValue({ kind: "identifier", value: "today" }),
    );
  });

  it("voltar a um preset relativo limpa as chaves do par de datas (inclui expressões)", () => {
    const onChange = vi.fn();
    render(
      <DataParamFields
        schema={SCHEMA}
        values={{ start_date: EXPR, end_date: EXPR, dateRangePreset: "" }}
        expressionSupport={SUPPORT}
        onChange={onChange}
      />,
    );
    const presetTrigger = screen.getByRole("button", { name: "Período relativo" });
    fireEvent.click(presetTrigger);
    const option = screen
      .getAllByRole("listbox")
      .flatMap((list) => Array.from(list.querySelectorAll("button")))
      .find((button) => /Este mês|This month|mês/i.test(button.textContent ?? ""));
    expect(option).toBeTruthy();
    fireEvent.click(option!);
    const updates = onChange.mock.calls.at(-1)![0];
    expect(updates.start_date).toBe("");
    expect(updates.end_date).toBe("");
  });

  it("expressão→valor fixo pede confirmação; Cancelar preserva o AST (cenário E)", () => {
    const onChange = vi.fn();
    render(
      <DataParamFields
        schema={SCHEMA}
        values={{ start_date: EXPR }}
        expressionSupport={SUPPORT}
        onChange={onChange}
      />,
    );
    fireEvent.click(
      screen.getAllByRole("button", { name: "Valor fixo" })[0]!,
    );
    // ConfirmModal abre — nada foi gravado ainda.
    expect(screen.getByText("Voltar para valor fixo?")).toBeTruthy();
    expect(onChange).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
    expect(onChange).not.toHaveBeenCalled();
    // Cartão-resumo da expressão continua intacto.
    expect(document.querySelector(".td-expression-summary")).toBeTruthy();
  });

  it("expressão→valor fixo confirmado grava o valor vazio (cenário E)", () => {
    const onChange = vi.fn();
    render(
      <DataParamFields
        schema={SCHEMA}
        values={{ start_date: EXPR }}
        expressionSupport={SUPPORT}
        onChange={onChange}
      />,
    );
    fireEvent.click(
      screen.getAllByRole("button", { name: "Valor fixo" })[0]!,
    );
    fireEvent.click(screen.getByRole("button", { name: "Usar valor fixo" }));
    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange.mock.calls[0][0].start_date).toBe("");
  });

  it("valor fixo→expressão com literal gravado pede confirmação e abre o drawer", () => {
    const onChange = vi.fn();
    const onEditExpression = vi.fn();
    render(
      <DataParamFields
        schema={SCHEMA}
        values={{ start_date: "2024-01-01" }}
        expressionSupport={SUPPORT}
        onChange={onChange}
        onEditExpression={onEditExpression}
      />,
    );
    fireEvent.click(
      screen.getAllByRole("button", { name: "Expressão" })[0]!,
    );
    expect(screen.getByText("Trocar para expressão?")).toBeTruthy();
    expect(onChange).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Trocar para expressão" }));
    expect(onChange).toHaveBeenCalledTimes(1);
    // Spec inicial «hoje» + drawer aberto para o mesmo param.
    expect(onChange.mock.calls[0][0].start_date).toEqual(EXPR);
    expect(onEditExpression).toHaveBeenCalledTimes(1);
    expect(onEditExpression.mock.calls[0][0].paramKey).toBe("start_date");
  });

  it("expressão persistida sem capability renderiza read-only preservada", () => {
    render(
      <DataParamFields
        schema={SCHEMA}
        values={{ start_date: EXPR }}
        onChange={vi.fn()}
      />,
    );
    expect(screen.getByRole("status").textContent).toMatch(/edição indisponível/i);
    expect(document.body.textContent).toContain('"identifier"');
  });
});
