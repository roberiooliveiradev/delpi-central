import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { QuantityInput } from "./QuantityInput";

afterEach(() => {
  cleanup();
});

describe("QuantityInput", () => {
  it("mostra quantidade com 3 casas decimais", () => {
    render(
      <QuantityInput value={0.25} onChange={() => undefined} ariaLabel="Quantidade a faturar" />,
    );
    expect((screen.getByLabelText("Quantidade a faturar") as HTMLInputElement).value).toBe(
      "0,250",
    );
  });

  it("interpreta vírgula e limita ao máximo", () => {
    const onChange = vi.fn();
    render(
      <QuantityInput
        value={0.25}
        max={0.25}
        onChange={onChange}
        ariaLabel="Quantidade a faturar"
      />,
    );
    fireEvent.change(screen.getByLabelText("Quantidade a faturar"), {
      target: { value: "0,251" },
    });
    expect(onChange).toHaveBeenCalledWith(0.25);
  });
});
