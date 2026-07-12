import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { RibbonColorPicker } from "./RibbonColorPicker";

describe("RibbonColorPicker", () => {
  it("aplica --ribbon e className extras no gatilho, não no popover", () => {
    const { container } = render(
      <RibbonColorPicker
        label="Cor da série"
        value="#089bdb"
        onChange={() => undefined}
        className="delpi-ui-color-picker-trigger--inline"
      />,
    );

    const trigger = container.querySelector(".delpi-ui-color-picker-trigger");
    expect(trigger?.className).toContain("delpi-ui-color-picker-trigger--ribbon");
    expect(trigger?.className).toContain("delpi-ui-color-picker-trigger--inline");

    fireEvent.click(screen.getByRole("button", { name: "Cor da série" }));
    const popover = document.querySelector(".delpi-ui-color-picker");
    expect(popover).toBeTruthy();
    expect(popover?.className).not.toContain("delpi-ui-color-picker-trigger--inline");
    expect(popover?.className).not.toContain("delpi-ui-color-picker-trigger--ribbon");
  });
});
