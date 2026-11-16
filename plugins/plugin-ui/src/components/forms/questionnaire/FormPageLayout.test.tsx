import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { FormPageLayout } from "./FormPageLayout";

describe("FormPageLayout", () => {
  it("aplica a variante compact por padrão com classes dual", () => {
    const { container } = render(
      <FormPageLayout prefix="puc">
        <div>filho</div>
      </FormPageLayout>,
    );
    const root = container.firstElementChild!;
    expect(root.className).toContain("puc-form-page");
    expect(root.className).toContain("delpi-ui-form-page");
    expect(root.className).toContain("delpi-ui-form-page--band-compact");
    expect(root.className).toContain("puc-form-page--band-compact");

    const band = root.querySelector(".delpi-ui-form-page__band")!;
    expect(band).toBeTruthy();
    expect(band.className).toContain("puc-form-page__band");
    expect(band.getAttribute("aria-hidden")).toBe("true");

    const column = root.querySelector(".delpi-ui-form-page__column")!;
    expect(column.className).toContain("puc-form-page__column");
    expect(column.textContent).toBe("filho");
  });

  it("aplica a variante tall", () => {
    const { container } = render(
      <FormPageLayout band="tall">x</FormPageLayout>,
    );
    const root = container.firstElementChild!;
    expect(root.className).toContain("delpi-ui-form-page--band-tall");
    expect(root.className).not.toContain("band-compact");
  });

  it("mescla className do consumidor", () => {
    const { container } = render(
      <FormPageLayout className="extra">x</FormPageLayout>,
    );
    expect(container.firstElementChild!.className).toContain("extra");
  });
});
