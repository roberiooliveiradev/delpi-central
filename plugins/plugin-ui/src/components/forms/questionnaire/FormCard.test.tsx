import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { FormCard } from "./FormCard";

afterEach(cleanup);

describe("FormCard", () => {
  it("renderiza div por padrão com classes dual", () => {
    const { container } = render(
      <FormCard prefix="puc">conteúdo</FormCard>,
    );
    const card = container.firstElementChild!;
    expect(card.tagName).toBe("DIV");
    expect(card.className).toContain("puc-form-card");
    expect(card.className).toContain("delpi-ui-form-card");
    expect(card.textContent).toBe("conteúdo");
  });

  it("renderiza fieldset quando as='fieldset' e repassa atributos", () => {
    const { container } = render(
      <FormCard as="fieldset" aria-describedby="err-1">
        x
      </FormCard>,
    );
    const card = container.firstElementChild!;
    expect(card.tagName).toBe("FIELDSET");
    expect(card.getAttribute("aria-describedby")).toBe("err-1");
  });

  it("aplica tone invalid", () => {
    const { container } = render(<FormCard tone="invalid">x</FormCard>);
    const card = container.firstElementChild!;
    expect(card.className).toContain("delpi-ui-form-card--tone-invalid");
  });
});
