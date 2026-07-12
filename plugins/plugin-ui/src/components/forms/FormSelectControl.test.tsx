import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { FormSelectControl } from "./FormSelectControl";

describe("FormSelectControl", () => {
  it("abre painel custom no portal e dispara onChange", () => {
    const values: string[] = [];
    render(
      <FormSelectControl
        ariaLabel="Formato"
        value="auto"
        onChange={(value) => values.push(value)}
        options={[
          { value: "auto", label: "Automático" },
          { value: "number", label: "Número" },
        ]}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Formato" }));
    const panel = document.body.querySelector(".delpi-ui-select__panel--portal");
    expect(panel).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Número" }));
    expect(values).toEqual(["number"]);
  });

  it("aplica style de preview nas opções e no trigger", () => {
    render(
      <FormSelectControl
        ariaLabel="Fonte"
        value="Georgia, serif"
        onChange={() => undefined}
        options={[
          { value: "Arial, sans-serif", label: "Arial", style: { fontFamily: "Arial, sans-serif" } },
          {
            value: "Georgia, serif",
            label: "Georgia",
            style: { fontFamily: "Georgia, serif" },
          },
        ]}
      />,
    );

    const triggerLabel = screen.getByRole("button", { name: "Fonte" }).querySelector("span");
    expect(triggerLabel?.getAttribute("style") ?? "").toContain("Georgia, serif");

    fireEvent.click(screen.getByRole("button", { name: "Fonte" }));
    const arialOption = screen.getByRole("button", { name: "Arial" });
    expect(arialOption.getAttribute("style") ?? "").toContain("Arial, sans-serif");
  });

  it("usa classes canônicas delpi-ui-select", () => {
    const { container } = render(
      <FormSelectControl
        value="a"
        options={[{ value: "a", label: "A" }]}
        onChange={() => undefined}
      />,
    );
    expect(container.querySelector(".delpi-ui-select")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-select__trigger")).toBeTruthy();
  });
});
