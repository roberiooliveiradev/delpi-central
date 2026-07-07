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

  it("liga hint ao hover do próprio texto do rótulo", () => {
    render(<FieldLabel label="Duração" hint="Tempo em segundos." />);
    const labelText = screen.getByText("Duração");
    expect(labelText.className).toContain("delpi-ui-field-label__text");
    expect(labelText.getAttribute("aria-describedby")).toBeTruthy();
  });
});
