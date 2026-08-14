import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { NativeCheckboxControl } from "./NativeCheckboxControl";

afterEach(cleanup);

describe("NativeCheckboxControl hintPlacement", () => {
  it("mantém hint inline por default", () => {
    render(
      <NativeCheckboxControl
        checked={false}
        onChange={vi.fn()}
        label="Comparar"
        hint="Texto longo de ajuda."
      />,
    );
    expect(screen.getByText("Texto longo de ajuda.")).toBeTruthy();
    const root = document.querySelector(".delpi-ui-native-checkbox");
    expect(root?.getAttribute("data-hint-placement")).toBe("inline");
  });

  it("usa HelpTooltip quando hintPlacement=tooltip", () => {
    render(
      <NativeCheckboxControl
        checked={false}
        onChange={vi.fn()}
        label="Tendência"
        hint="Regressão linear sobre a série atual."
        hintPlacement="tooltip"
        hintAriaLabel="Ajuda: tendência"
      />,
    );
    expect(screen.queryByText("Regressão linear sobre a série atual.")).toBeNull();
    expect(screen.getByLabelText("Ajuda: tendência")).toBeTruthy();
    const root = document.querySelector(".delpi-ui-native-checkbox");
    expect(root?.getAttribute("data-hint-placement")).toBe("tooltip");
    expect(document.querySelector(".delpi-ui-native-checkbox__hint")).toBeNull();
  });
});
