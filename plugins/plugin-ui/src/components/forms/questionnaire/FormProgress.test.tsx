import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { FormProgress } from "./FormProgress";

afterEach(cleanup);

describe("FormProgress", () => {
  it("expõe progressbar com aria-valuenow parcial e rótulo opcional", () => {
    render(
      <FormProgress
        done={3}
        total={12}
        ariaLabel="Progresso"
        label="3 de 12"
        prefix="puc"
      />,
    );
    const bar = screen.getByRole("progressbar");
    expect(bar.getAttribute("aria-valuemin")).toBe("0");
    expect(bar.getAttribute("aria-valuemax")).toBe("100");
    expect(bar.getAttribute("aria-valuenow")).toBe("25");
    expect(bar.getAttribute("aria-label")).toBe("Progresso");
    expect(bar.className).toContain("delpi-ui-form-progress__track");
    expect(screen.getByText("3 de 12").className).toContain(
      "delpi-ui-form-progress__label",
    );
    expect(bar.querySelector(".delpi-ui-form-progress__fill")).toBeTruthy();
  });

  it("aria-valuenow 0 no início e 100 ao concluir", () => {
    const { rerender } = render(
      <FormProgress done={0} total={12} ariaLabel="p" />,
    );
    expect(screen.getByRole("progressbar").getAttribute("aria-valuenow")).toBe(
      "0",
    );
    rerender(<FormProgress done={12} total={12} ariaLabel="p" />);
    expect(screen.getByRole("progressbar").getAttribute("aria-valuenow")).toBe(
      "100",
    );
  });

  it("total 0 resulta em 0 (sem NaN/Infinity)", () => {
    render(<FormProgress done={3} total={0} ariaLabel="p" />);
    expect(screen.getByRole("progressbar").getAttribute("aria-valuenow")).toBe(
      "0",
    );
  });
});
