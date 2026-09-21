import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { QuickPeriodSelector } from "./QuickPeriodSelector";

afterEach(() => {
  cleanup();
});

describe("QuickPeriodSelector", () => {
  it("marca o preset ativo com aria-pressed e chama onChange", () => {
    const onChange = vi.fn();
    render(
      <QuickPeriodSelector
        prefix="cm"
        value="this_month"
        onChange={onChange}
        hint="Atalhos de período."
        idPrefix="test-period"
      />,
    );

    const month = screen.getByRole("button", { name: "Este mês" });
    expect(month.getAttribute("aria-pressed")).toBe("true");

    const today = screen.getByRole("button", { name: "Hoje" });
    expect(today.getAttribute("aria-pressed")).toBe("false");
    fireEvent.click(today);
    expect(onChange).toHaveBeenCalledWith("today");
  });

  it("expõe Personalizado como botão real", () => {
    render(<QuickPeriodSelector value="custom" onChange={vi.fn()} />);
    const custom = screen.getByRole("button", { name: "Personalizado" });
    expect(custom.tagName).toBe("BUTTON");
    expect(custom.getAttribute("aria-pressed")).toBe("true");
  });
});
