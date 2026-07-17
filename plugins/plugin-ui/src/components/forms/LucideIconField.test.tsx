import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { LucideIconField } from "./LucideIconField";

describe("LucideIconField", () => {
  it("abre picker ao clicar no trigger", () => {
    const onChange = vi.fn();

    render(
      <LucideIconField
        value="Star"
        defaultIcon="Star"
        nameFormat="pascal"
        onChange={onChange}
        ariaLabel="Escolher ícone"
      />,
    );

    expect(screen.queryByPlaceholderText(/buscar/i)).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "Escolher ícone" }));

    expect(screen.getByPlaceholderText(/buscar/i)).toBeTruthy();
  });
});
