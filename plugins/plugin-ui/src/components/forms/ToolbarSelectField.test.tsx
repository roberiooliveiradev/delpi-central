import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ToolbarSelectField } from "./ToolbarSelectField";

afterEach(() => {
  cleanup();
});

describe("ToolbarSelectField", () => {
  it("renderiza label e trigger compacto", () => {
    render(
      <ToolbarSelectField
        label="Série"
        value=""
        options={[{ value: "a", label: "Opção A" }]}
        onChange={vi.fn()}
        placeholderOption="Todos"
      />,
    );

    expect(screen.getByText("Série")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Série" })).toBeTruthy();
    expect(screen.getByText("Todos")).toBeTruthy();
  });
});
