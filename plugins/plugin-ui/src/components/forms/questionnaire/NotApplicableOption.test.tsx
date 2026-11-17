import { cleanup, fireEvent, render } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { NotApplicableOption } from "./NotApplicableOption";

afterEach(cleanup);

describe("NotApplicableOption", () => {
  it("renderiza um radio do grupo com o label visível como nome acessível", () => {
    const { getByRole } = render(
      <NotApplicableOption name="q1" label="Não se aplica" />,
    );
    const radio = getByRole("radio", {
      name: "Não se aplica",
    }) as HTMLInputElement;
    expect(radio.type).toBe("radio");
    expect(radio.name).toBe("q1");
    expect(radio.checked).toBe(false);
  });

  it("checked reflete o estado; clicar desmarcada chama onChange", () => {
    const onChange = vi.fn();
    const { getByRole, rerender } = render(
      <NotApplicableOption
        name="q1"
        label="Não se aplica"
        checked={false}
        onChange={onChange}
      />,
    );
    const radio = getByRole("radio") as HTMLInputElement;
    fireEvent.click(radio);
    expect(onChange).toHaveBeenCalledTimes(1);

    rerender(
      <NotApplicableOption
        name="q1"
        label="Não se aplica"
        checked
        onChange={onChange}
      />,
    );
    expect((getByRole("radio") as HTMLInputElement).checked).toBe(true);
  });

  it("invalid aplica o modificador e aria-invalid", () => {
    const { container, getByRole } = render(
      <NotApplicableOption name="q1" label="Não se aplica" invalid />,
    );
    expect(container.firstElementChild!.className).toContain(
      "delpi-ui-form-na--invalid",
    );
    expect(getByRole("radio").getAttribute("aria-invalid")).toBe("true");
  });

  it("dual-class: prefixo do consumidor + classe canônica", () => {
    const { container } = render(
      <NotApplicableOption name="q1" label="Não se aplica" prefix="puc" />,
    );
    const root = container.firstElementChild!;
    expect(root.className).toContain("delpi-ui-form-na");
    expect(root.className).toContain("puc-form-na");
  });
});
