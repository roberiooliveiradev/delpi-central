import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { FieldLabel } from "./FieldLabel";

describe("FieldLabel", () => {
  it("renderiza label com texto", () => {
    render(<FieldLabel label="Período" />);
    expect(screen.getByText("Período")).toBeTruthy();
  });

  it("associa htmlFor ao label", () => {
    render(<FieldLabel label="Título" htmlFor="titulo" />);
    const label = screen.getByText("Título").closest("label");
    expect(label?.getAttribute("for")).toBe("titulo");
  });

  it("exibe gatilho de ajuda quando hint é informado", () => {
    render(<FieldLabel label="Duração" hint="Tempo em segundos." />);
    expect(screen.getByRole("button", { name: "Ajuda: Duração" })).toBeTruthy();
  });
});
