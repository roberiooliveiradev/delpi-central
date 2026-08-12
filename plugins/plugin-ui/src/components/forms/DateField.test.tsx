import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DateField, dateFieldBemClasses } from "./DateField";

afterEach(() => {
  cleanup();
});

describe("DateField", () => {
  it("renderiza input date com rótulo e dispara onChange", () => {
    const onChange = vi.fn();
    render(
      <DateField
        id="test-date"
        label="Data implantação"
        value="2026-06-15"
        onChange={onChange}
        classNames={dateFieldBemClasses("kz")}
      />,
    );

    const input = screen.getByLabelText("Data implantação") as HTMLInputElement;
    expect(input.type).toBe("date");
    expect(input.value).toBe("2026-06-15");
    expect(input.closest(".delpi-ui-filter-box")).toBeTruthy();
    expect(input.className).toContain("kz-field__control");

    fireEvent.change(input, { target: { value: "2026-07-01" } });
    expect(onChange).toHaveBeenCalledWith("2026-07-01");
  });

  it("aceita type=month para competência YYYY-MM", () => {
    const onChange = vi.fn();
    render(
      <DateField
        id="test-competence"
        label="Competência"
        type="month"
        value="2026-08"
        onChange={onChange}
        classNames={dateFieldBemClasses("cm")}
      />,
    );

    const input = screen.getByLabelText("Competência") as HTMLInputElement;
    expect(input.type).toBe("month");
    expect(input.value).toBe("2026-08");

    fireEvent.change(input, { target: { value: "2026-07" } });
    expect(onChange).toHaveBeenCalledWith("2026-07");
  });
});
