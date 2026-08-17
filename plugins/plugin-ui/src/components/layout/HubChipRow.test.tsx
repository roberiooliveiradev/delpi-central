import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { HubChipRow, hubChipRowBemClasses } from "./HubChipRow";

afterEach(() => {
  cleanup();
});

describe("HubChipRow", () => {
  it("renderiza label, children e aria-label com dual-class", () => {
    const { container } = render(
      <HubChipRow
        classNames={hubChipRowBemClasses("cm")}
        label="Favoritos"
        aria-label="Faixa de favoritos"
      >
        <button type="button">Minhas tarefas</button>
      </HubChipRow>,
    );
    expect(screen.getByText("Favoritos")).toBeTruthy();
    expect(screen.getByRole("group", { name: "Faixa de favoritos" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Minhas tarefas" })).toBeTruthy();
    expect(container.querySelector(".delpi-ui-hub-chip-row")).toBeTruthy();
    expect(container.querySelector(".cm-hub-chip-row")).toBeTruthy();
  });
});
