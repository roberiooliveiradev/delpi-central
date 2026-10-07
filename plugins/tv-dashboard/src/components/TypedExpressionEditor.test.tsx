// @vitest-environment happy-dom
import { useState } from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { ParamExpressionSpec } from "@delpi/tv-dashboard-presentation";

import type { MFunctionCatalogItem } from "../api/tvDashboardApi";
import type { ParamExpressionSupport } from "../hooks/useParamExpressionCapability";
import {
  buildExpressionParamValue,
  readExpressionAst,
} from "../utils/paramExpressions";
import { TypedExpressionEditor } from "./TypedExpressionEditor";

afterEach(() => cleanup());

const FUNCTIONS: MFunctionCatalogItem[] = [
  {
    name: "Date.StartOfMonth",
    kind: "scalar",
    signature: "Date.StartOfMonth(value) as date",
    description: "Primeiro dia do mês",
    parameters: ["value"],
  },
  {
    name: "Date.AddMonths",
    kind: "scalar",
    signature: "Date.AddMonths(value, months) as date",
    description: "Soma meses",
    parameters: ["value", "months"],
  },
  {
    name: "Text.Upper",
    kind: "scalar",
    signature: "Text.Upper(value) as text",
    parameters: ["value"],
  },
];

const SUPPORT: ParamExpressionSupport = {
  enabled: true,
  loading: false,
  functions: FUNCTIONS,
  registryVersion: "1",
};

const MTD_START = buildExpressionParamValue({
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
});

/** Abre o select custom e clica na opção pelo texto. */
function chooseOption(trigger: HTMLElement, label: string | RegExp) {
  fireEvent.click(trigger);
  const option = screen
    .getAllByRole("listbox")
    .flatMap((list) => Array.from(list.querySelectorAll("button")))
    .find((button) =>
      typeof label === "string" ? button.textContent === label : label.test(button.textContent ?? ""),
    );
  expect(option, `opção ${label}`).toBeTruthy();
  fireEvent.click(option!);
}

describe("TypedExpressionEditor — hydration", () => {
  it("renderiza nested call MTD-year-back completa (função/ref/literal)", () => {
    render(
      <TypedExpressionEditor value={MTD_START} onChange={vi.fn()} support={SUPPORT} />,
    );
    const triggers = screen.getAllByRole("button", { name: "Função" });
    const labels = triggers.map((t) => t.textContent ?? "");
    // Label amigável + nome canônico persistido (§ friendly labels)
    expect(labels.join(" ")).toContain("Início do mês");
    expect(labels.join(" ")).toContain("Date.StartOfMonth");
    expect(labels.join(" ")).toContain("Adicionar meses");
    expect(labels.join(" ")).toContain("Date.AddMonths");
    // identifier "today" hidrata na referência
    const refTrigger = screen.getByRole("button", { name: "Referência" });
    expect(refTrigger.textContent).toContain("Hoje");
    // literal -12 hidrata no input numérico
    const literal = screen.getByPlaceholderText("Ex.: -12") as HTMLInputElement;
    expect(literal.value).toBe("-12");
  });

  it("ExpressionSpec malformado mostra hint sem quebrar", () => {
    render(
      <TypedExpressionEditor
        value={{ expression: { version: 1, expression: null as never } }}
        onChange={vi.fn()}
        support={SUPPORT}
      />,
    );
    expect(screen.getByRole("alert").textContent).toMatch(/inválido/i);
  });

  it("nó fora do vocabulário (DERIVED) fica read-only e preserva JSON", () => {
    const spec = buildExpressionParamValue({ kind: "field", value: "x" });
    render(
      <TypedExpressionEditor value={spec} onChange={vi.fn()} support={SUPPORT} />,
    );
    expect(screen.getByRole("status").textContent).toMatch(/não suportada/i);
    expect(document.body.textContent).toContain('"field"');
  });
});

describe("TypedExpressionEditor — authoring", () => {
  it("seleção de função do catálogo emite call com slots de requiredArgs", () => {
    const onChange = vi.fn();
    render(
      <TypedExpressionEditor
        value={buildExpressionParamValue({ kind: "call", value: "" })}
        onChange={onChange}
        support={SUPPORT}
      />,
    );
    chooseOption(
      screen.getByRole("button", { name: "Função" }),
      /Adicionar meses \(Date\.AddMonths\)/,
    );
    const emitted = readExpressionAst(onChange.mock.calls[0][0]);
    expect(emitted).toEqual({
      kind: "call",
      value: "Date.AddMonths",
      children: [{ kind: "literal" }, { kind: "literal" }],
    });
  });

  it("edição de literal numérico emite literal tipado", () => {
    const onChange = vi.fn();
    function Harness() {
      const [v, setV] = useState<ParamExpressionSpec>(
        buildExpressionParamValue({
          kind: "call",
          value: "Date.AddMonths",
          children: [
            { kind: "identifier", value: "today" },
            { kind: "literal" },
          ],
        }),
      );
      return (
        <TypedExpressionEditor
          value={v}
          onChange={(next) => {
            onChange(next);
            setV(next);
          }}
          support={SUPPORT}
        />
      );
    }
    render(<Harness />);
    // Literal unset → escolhe tipo Número → input numérico aparece.
    chooseOption(
      screen.getByRole("button", { name: "Tipo do literal" }),
      "Número",
    );
    fireEvent.change(screen.getByPlaceholderText("Ex.: -12"), {
      target: { value: "-12" },
    });
    const emitted = readExpressionAst(onChange.mock.calls.at(-1)![0]);
    expect(emitted?.children?.[1]).toEqual({ kind: "literal", value: -12 });
  });

  it("troca de tipo do nó para referência + seleção 'Hoje' emite identifier", () => {
    const onChange = vi.fn();
    render(
      <TypedExpressionEditor
        value={buildExpressionParamValue({ kind: "literal", value: "" })}
        onChange={onChange}
        support={SUPPORT}
      />,
    );
    chooseOption(screen.getByRole("button", { name: "Tipo do nó" }), "Referência");
    let emitted = readExpressionAst(onChange.mock.calls.at(-1)![0]);
    expect(emitted).toEqual({ kind: "identifier", value: "today" });
  });

  it("refs param.<key> aparecem no seletor de referência", () => {
    render(
      <TypedExpressionEditor
        value={buildExpressionParamValue({ kind: "identifier", value: "param.branch" })}
        onChange={vi.fn()}
        support={SUPPORT}
        refParamKeys={[{ key: "branch", label: "Filial" }]}
      />,
    );
    const refTrigger = screen.getByRole("button", { name: "Referência" });
    expect(refTrigger.textContent).toContain("Filial");
  });

  it("refs input.<key> do slide hidratam e podem ser escolhidas", () => {
    const onChange = vi.fn();
    render(
      <TypedExpressionEditor
        value={buildExpressionParamValue({ kind: "identifier", value: "today" })}
        onChange={onChange}
        support={SUPPORT}
        refInputKeys={[{ key: "meeting_day", label: "Dia da reunião" }]}
      />,
    );
    chooseOption(screen.getByRole("button", { name: "Referência" }), "Variável Dia da reunião");
    expect(readExpressionAst(onChange.mock.calls.at(-1)![0])).toEqual({
      kind: "identifier",
      value: "input.meeting_day",
    });
  });

  it("sem refInputKeys (ex.: programação) não oferece variáveis e preserva ref existente", () => {
    const onChange = vi.fn();
    render(
      <TypedExpressionEditor
        value={buildExpressionParamValue({ kind: "identifier", value: "input.meeting_day" })}
        onChange={onChange}
        support={SUPPORT}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Referência" }));
    const labels = screen
      .getAllByRole("listbox")
      .flatMap((list) => Array.from(list.querySelectorAll("button")))
      .map((button) => button.textContent ?? "");
    expect(labels.some((label) => label.startsWith("Variável"))).toBe(false);
    expect(onChange).not.toHaveBeenCalled();
  });
});
