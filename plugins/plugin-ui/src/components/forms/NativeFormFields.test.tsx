import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { formFieldShellKaizenClasses } from "./FormFieldShell";
import { NativeTextField } from "./NativeFormFields";

afterEach(() => {
  cleanup();
});

describe("NativeTextField", () => {
  it("renderiza shell kaizen com input nativo", () => {
    const { container } = render(
      <NativeTextField
        id="kz-title"
        label="Título"
        hint="Nome da melhoria"
        value="Teste"
        onChange={() => undefined}
        classNames={formFieldShellKaizenClasses("kz")}
      />,
    );

    expect(container.querySelector(".kz-field")).toBeTruthy();
    const input = screen.getByLabelText("Título");
    expect(input).toBeTruthy();
    expect(input.className).toContain("delpi-ui-native-control");
    expect(screen.getByDisplayValue("Teste")).toBeTruthy();
  });

  it("aplica span wide", () => {
    const { container } = render(
      <NativeTextField
        id="kz-desc"
        label="Descrição"
        span
        value=""
        onChange={() => undefined}
        classNames={formFieldShellKaizenClasses("kz")}
      />,
    );

    expect(container.querySelector(".kz-span-2")).toBeTruthy();
  });

  it("aceita type datetime-local", () => {
    render(
      <NativeTextField
        id="ca-start"
        label="Início"
        type="datetime-local"
        value="2026-07-08T10:00"
        onChange={() => undefined}
        classNames={formFieldShellKaizenClasses("ca")}
      />,
    );

    const input = screen.getByLabelText("Início");
    expect(input.getAttribute("type")).toBe("datetime-local");
    expect(screen.getByDisplayValue("2026-07-08T10:00")).toBeTruthy();
  });

  it("renderiza afterControl após o input", () => {
    const { container } = render(
      <NativeTextField
        id="dm-peca"
        label="Peça"
        value=""
        onChange={() => undefined}
        afterControl={<span className="dm-field__error">Obrigatório</span>}
        classNames={formFieldShellKaizenClasses("dm")}
      />,
    );

    expect(container.querySelector(".dm-field__error")?.textContent).toBe("Obrigatório");
  });

  it("renderiza beforeControl dentro do controlWrapper", () => {
    const { container } = render(
      <NativeTextField
        id="a5s-responsible"
        label="Responsável"
        value=""
        onChange={() => undefined}
        beforeControl={<span className="a5s-nc-input-wrap__icon">icon</span>}
        controlWrapperClassName="a5s-nc-input-wrap"
        classNames={formFieldShellKaizenClasses("a5s")}
      />,
    );

    expect(container.querySelector(".a5s-nc-input-wrap")).toBeTruthy();
    expect(container.querySelector(".a5s-nc-input-wrap__icon")).toBeTruthy();
  });

  it("respeita readOnly e onBlur", () => {
    let blurred = false;
    render(
      <NativeTextField
        id="td-public"
        label="Link"
        value="https://example"
        onChange={() => undefined}
        readOnly
        onBlur={() => {
          blurred = true;
        }}
        classNames={formFieldShellKaizenClasses("td")}
      />,
    );

    const input = screen.getByLabelText("Link");
    expect(input.hasAttribute("readOnly")).toBe(true);
    input.focus();
    input.blur();
    expect(blurred).toBe(true);
  });
});
