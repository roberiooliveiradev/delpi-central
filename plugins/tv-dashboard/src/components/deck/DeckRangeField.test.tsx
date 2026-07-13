import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DeckRangeField } from "./DeckRangeField";

afterEach(() => {
  cleanup();
});

describe("DeckRangeField", () => {
  it("permite digitar o valor no input numérico", () => {
    const onChange = vi.fn();
    render(
      <DeckRangeField
        id="td-x"
        label="X px"
        value={100}
        min={0}
        max={1920}
        onChange={onChange}
      />,
    );
    const input = screen.getByLabelText("X px (digitar)");
    fireEvent.focus(input);
    fireEvent.change(input, { target: { value: "250.5" } });
    fireEvent.blur(input);
    expect(onChange).toHaveBeenCalledWith(250.5);
  });

  it("slider continua aplicando valor", () => {
    const onChange = vi.fn();
    render(
      <DeckRangeField id="td-y" label="Y px" value={10} min={0} max={100} onChange={onChange} />,
    );
    fireEvent.change(screen.getByLabelText("Y px"), { target: { value: "42" } });
    expect(onChange).toHaveBeenCalledWith(42);
  });
});
