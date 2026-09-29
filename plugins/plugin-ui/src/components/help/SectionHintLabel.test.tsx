import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { SectionHintLabel } from "./SectionHintLabel";

afterEach(() => {
  cleanup();
});

describe("SectionHintLabel", () => {
  it("usa o próprio rótulo como trigger — sem botão «?»", () => {
    const { container } = render(
      <SectionHintLabel label="Achados" hint="Observações registradas na análise." />,
    );

    const labelEl = container.querySelector(".delpi-ui-section-hint-label");
    expect(labelEl).toBeTruthy();
    expect(labelEl?.textContent).toBe("Achados");
    // Nenhum trigger-ícone: o help nasce do span focável.
    expect(container.querySelector(".delpi-ui-help-tooltip__trigger")).toBeNull();
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("rótulo é focável por teclado e abre o balão no focus/hover", () => {
    const { container } = render(
      <SectionHintLabel label="Hipóteses" hint="Explicações propostas." />,
    );

    const labelEl = container.querySelector<HTMLElement>(".delpi-ui-section-hint-label");
    expect(labelEl?.getAttribute("tabindex")).toBe("0");

    fireEvent.mouseEnter(container.querySelector(".delpi-ui-help-tooltip--wrap")!);
    expect(screen.getByRole("tooltip", { hidden: true }).textContent).toBe(
      "Explicações propostas.",
    );
  });
});
