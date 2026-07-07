import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { FormActions, formActionsPacClasses } from "./FormActions";
import { FormGrid, formGridPacClasses } from "./FormGrid";

afterEach(() => {
  cleanup();
});

describe("FormGrid", () => {
  it("renderiza grade com classe BEM", () => {
    const { container } = render(
      <FormGrid classNames={formGridPacClasses("pac")}>
        <span>Campo</span>
      </FormGrid>,
    );

    expect(container.querySelector(".pac-form-grid")).toBeTruthy();
    expect(screen.getByText("Campo")).toBeTruthy();
  });
});

describe("FormActions", () => {
  it("aplica modificador end", () => {
    const { container } = render(
      <FormActions align="end" classNames={formActionsPacClasses("pac")}>
        <button type="button">Salvar</button>
      </FormActions>,
    );

    const root = container.firstElementChild;
    expect(root?.className).toContain("pac-form-actions");
    expect(root?.className).toContain("pac-form-actions--end");
  });
});
