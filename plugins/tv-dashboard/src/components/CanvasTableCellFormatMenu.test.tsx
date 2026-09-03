import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CanvasTableCellFormatMenu } from "./CanvasTableCellFormatMenu";

afterEach(() => cleanup());

describe("CanvasTableCellFormatMenu", () => {
  function renderMenu(overrides: Partial<Parameters<typeof CanvasTableCellFormatMenu>[0]> = {}) {
    const props = {
      onAlign: vi.fn(),
      onVerticalAlign: vi.fn(),
      onToggleWrap: vi.fn(),
      onSetNowrap: vi.fn(),
      onColorChange: vi.fn(),
      onBackgroundChange: vi.fn(),
      onNoFill: vi.fn(),
      ...overrides,
    };
    render(<CanvasTableCellFormatMenu {...props} />);
    return props;
  }

  it("Centro chama onAlign(center)", () => {
    const props = renderMenu();
    fireEvent.click(screen.getByRole("menuitemradio", { name: /Centro/i }));
    expect(props.onAlign).toHaveBeenCalledWith("center");
  });

  it("Meio chama onVerticalAlign(middle)", () => {
    const props = renderMenu({ verticalAlign: "top" });
    fireEvent.click(screen.getByRole("menuitemradio", { name: /^Meio$/i }));
    expect(props.onVerticalAlign).toHaveBeenCalledWith("middle");
  });

  it("Quebrar chama onToggleWrap", () => {
    const props = renderMenu({ whiteSpace: "pre-wrap" });
    fireEvent.click(screen.getByRole("menuitemcheckbox", { name: /Quebrar/i }));
    expect(props.onToggleWrap).toHaveBeenCalled();
  });
});
