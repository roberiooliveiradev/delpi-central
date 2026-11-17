import { cleanup, render } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { FormLogo } from "./FormLogo";

afterEach(cleanup);

describe("FormLogo", () => {
  it("renderiza selo + img com alt e tamanho padrão md", () => {
    const { container } = render(
      <FormLogo src="/logo.svg" alt="Marca" prefix="puc" />,
    );
    const seal = container.firstElementChild!;
    expect(seal.className).toContain("delpi-ui-form-logo");
    expect(seal.className).toContain("delpi-ui-form-logo--md");
    expect(seal.className).toContain("puc-form-logo");

    const img = seal.querySelector("img")!;
    expect(img.getAttribute("src")).toBe("/logo.svg");
    expect(img.getAttribute("alt")).toBe("Marca");
    expect(img.className).toContain("delpi-ui-form-logo__img");
  });

  it.each(["sm", "md", "lg"] as const)("aplica modificador de tamanho %s", (size) => {
    const { container } = render(
      <FormLogo src="/x.svg" alt="x" size={size} />,
    );
    expect(container.firstElementChild!.className).toContain(
      `delpi-ui-form-logo--${size}`,
    );
  });
});
