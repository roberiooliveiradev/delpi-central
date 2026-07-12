import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ComboboxNumberControl } from "./ComboboxNumberControl";

afterEach(() => {
  cleanup();
});

describe("ComboboxNumberControl", () => {
  it("permite digitar e confirma no blur com clamp", () => {
    const onChange = vi.fn();
    const { container } = render(
      <ComboboxNumberControl
        value={16}
        options={[12, 16, 24]}
        clamp={(n) => Math.min(24, Math.max(12, Math.round(n)))}
        aria-label="Tamanho"
        onChange={onChange}
      />,
    );

    const input = container.querySelector(".delpi-ui-combobox-number__input");
    expect(input).toBeTruthy();
    fireEvent.change(input!, { target: { value: "20" } });
    fireEvent.blur(input!);

    expect(onChange).toHaveBeenCalledWith(20);
  });

  it("escolhe valor da lista", () => {
    const onChange = vi.fn();
    render(
      <ComboboxNumberControl
        value={16}
        options={[12, 16, 24]}
        aria-label="Tamanho"
        onChange={onChange}
      />,
    );

    fireEvent.mouseDown(screen.getByRole("button", { name: /lista/i }));
    fireEvent.mouseDown(screen.getByRole("option", { name: "24" }));

    expect(onChange).toHaveBeenCalledWith(24);
  });

  it("reverte draft inválido no blur", () => {
    const onChange = vi.fn();
    const { container } = render(
      <ComboboxNumberControl
        value={18}
        options={[12, 18]}
        aria-label="Tamanho"
        onChange={onChange}
      />,
    );

    const input = container.querySelector(".delpi-ui-combobox-number__input");
    expect(input).toBeTruthy();
    fireEvent.change(input!, { target: { value: "abc" } });
    fireEvent.blur(input!);

    expect(onChange).not.toHaveBeenCalled();
    expect((input as HTMLInputElement).value).toBe("18");
  });
});
