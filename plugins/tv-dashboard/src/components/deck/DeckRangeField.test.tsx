import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DeckRangeField } from "./DeckRangeField";

afterEach(() => {
  cleanup();
});

describe("DeckRangeField (alias RangeField)", () => {
  it("reexporta RangeField do plugin-ui", () => {
    const onChange = vi.fn();
    render(
      <DeckRangeField id="td-x" label="X px" value={10} min={0} max={100} onChange={onChange} />,
    );
    fireEvent.change(screen.getByLabelText("X px"), { target: { value: "42" } });
    expect(onChange).toHaveBeenCalledWith(42);
    expect(screen.getByLabelText("X px (digitar)").className).toContain("delpi-ui-range-field__input");
  });
});
