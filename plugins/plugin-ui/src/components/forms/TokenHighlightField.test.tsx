import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { useState } from "react";

import {
  createDashboardTokenHighlightField,
  splitTokenHighlightSegments,
  tokenHighlightFieldBemClasses,
  TokenHighlightField,
} from "./TokenHighlightField";

const classes = tokenHighlightFieldBemClasses("dm");
const TOKENS = ["{cliente}", "{data}"];

afterEach(() => {
  cleanup();
});

function marksIn(container: HTMLElement): HTMLElement[] {
  return Array.from(
    container.querySelectorAll<HTMLElement>(".delpi-ui-token-highlight-field__mark"),
  );
}

describe("splitTokenHighlightSegments", () => {
  it("divide ocorrências exatas, inclusive no início e no fim", () => {
    const segments = splitTokenHighlightSegments(
      "{cliente} confirmou em {data} fim {data}",
      TOKENS,
    );
    expect(segments).toEqual([
      { text: "{cliente}", token: true },
      { text: " confirmou em ", token: false },
      { text: "{data}", token: true },
      { text: " fim ", token: false },
      { text: "{data}", token: true },
    ]);
  });

  it("não destaca marcador parcial nem fora da lista", () => {
    const segments = splitTokenHighlightSegments(
      "{client}e {outro} {dataa}",
      TOKENS,
    );
    expect(segments.filter((segment) => segment.token)).toEqual([]);
  });

  it("prefere o token mais longo quando há prefixo compartilhado", () => {
    const segments = splitTokenHighlightSegments("{cliente_nome}", [
      "{cliente}",
      "{cliente_nome}",
    ]);
    expect(segments).toEqual([{ text: "{cliente_nome}", token: true }]);
  });

  it("valor vazio e lista vazia não quebram", () => {
    expect(splitTokenHighlightSegments("", TOKENS)).toEqual([]);
    expect(splitTokenHighlightSegments("texto", [])).toEqual([
      { text: "texto", token: false },
    ]);
    expect(splitTokenHighlightSegments("texto", [""])).toEqual([
      { text: "texto", token: false },
    ]);
  });
});

describe("TokenHighlightField", () => {
  it("renderiza input sem multiline e textarea com multiline, com label ligado pelo id", () => {
    const { unmount } = render(
      <TokenHighlightField
        id="thf-subject"
        label="Assunto"
        value=""
        onChange={() => undefined}
        tokens={TOKENS}
        classNames={classes}
      />,
    );
    const input = screen.getByLabelText("Assunto");
    expect(input.tagName).toBe("INPUT");
    expect(input.className).toContain("delpi-ui-native-control");
    unmount();

    render(
      <TokenHighlightField
        id="thf-body"
        label="Mensagem"
        value=""
        onChange={() => undefined}
        tokens={TOKENS}
        multiline
        rows={6}
        classNames={classes}
      />,
    );
    const textarea = screen.getByLabelText("Mensagem");
    expect(textarea.tagName).toBe("TEXTAREA");
    expect(textarea.getAttribute("rows")).toBe("6");
  });

  it("digitação e colagem chamam onChange com o valor exato e o destaque acompanha", () => {
    function Host() {
      const [value, setValue] = useState("");
      return (
        <TokenHighlightField
          id="thf-live"
          label="Mensagem"
          value={value}
          onChange={setValue}
          tokens={TOKENS}
          multiline
          classNames={classes}
        />
      );
    }
    const { container } = render(<Host />);
    const field = screen.getByLabelText("Mensagem");

    fireEvent.change(field, { target: { value: "Olá {cliente}, reunião {data}." } });
    expect(field).toHaveProperty("value", "Olá {cliente}, reunião {data}.");
    expect(marksIn(container).map((mark) => mark.textContent)).toEqual([
      "{cliente}",
      "{data}",
    ]);
  });

  it("só marca ocorrências exatas; parcial e fora da lista ficam fora", () => {
    const { container } = render(
      <TokenHighlightField
        id="thf-exact"
        label="Mensagem"
        value="{cliente} {clientee} {outro} x{data} {data}"
        onChange={() => undefined}
        tokens={TOKENS}
        classNames={classes}
      />,
    );
    expect(marksIn(container).map((mark) => mark.textContent)).toEqual([
      "{cliente}",
      "{data}",
      "{data}",
    ]);
  });

  it("camada é aria-hidden; campo mantém nome acessível; aria-* e inputRef repassados", () => {
    let ref: HTMLElement | null = null;
    const { container } = render(
      <TokenHighlightField
        id="thf-a11y"
        label="Assunto"
        value="{cliente}"
        onChange={() => undefined}
        tokens={TOKENS}
        classNames={classes}
        inputRef={(element) => {
          ref = element;
        }}
        aria-describedby="externo-desc"
        aria-details="externo-details"
      />,
    );

    const backdrop = container.querySelector(
      ".delpi-ui-token-highlight-field__backdrop",
    );
    expect(backdrop?.getAttribute("aria-hidden")).toBe("true");

    const field = screen.getByLabelText("Assunto");
    expect(field.getAttribute("aria-describedby")).toContain("externo-desc");
    expect(field.getAttribute("aria-details")).toBe("externo-details");
    expect(ref).toBe(field);
  });

  it("disabled desabilita o controle e marca o stack; error vira role=alert + aria-invalid + describedby", () => {
    const { container, unmount } = render(
      <TokenHighlightField
        id="thf-disabled"
        label="Mensagem"
        value=""
        onChange={() => undefined}
        tokens={TOKENS}
        multiline
        disabled
        classNames={classes}
      />,
    );
    const field = screen.getByLabelText("Mensagem");
    expect(field).toHaveProperty("disabled", true);
    expect(
      container.querySelector(
        ".delpi-ui-token-highlight-field__stack[data-disabled]",
      ),
    ).toBeTruthy();
    unmount();

    render(
      <TokenHighlightField
        id="thf-error"
        label="Mensagem"
        value=""
        onChange={() => undefined}
        tokens={TOKENS}
        multiline
        error="Informe a mensagem"
        classNames={classes}
      />,
    );
    const errored = screen.getByLabelText("Mensagem");
    const alert = screen.getByRole("alert");
    expect(alert.textContent).toBe("Informe a mensagem");
    expect(errored.getAttribute("aria-invalid")).toBe("true");
    expect(errored.getAttribute("aria-describedby")).toBe("thf-error-error");
  });

  it("fábrica liga classes duplas {prefix}- e delpi-ui-", () => {
    const Bound = createDashboardTokenHighlightField({ prefix: "cm" });
    const { container } = render(
      <Bound
        id="thf-bound"
        label="Assunto"
        value="{cliente}"
        onChange={() => undefined}
        tokens={TOKENS}
      />,
    );
    const root = container.querySelector(
      ".cm-token-highlight-field.delpi-ui-token-highlight-field",
    );
    expect(root).toBeTruthy();
    expect(
      container.querySelector(
        ".cm-token-highlight-field__mark.delpi-ui-token-highlight-field__mark",
      ),
    ).toBeTruthy();
  });
});
