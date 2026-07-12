import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { FormSelectControl } from "./FormSelectControl";

describe("FormSelectControl", () => {
  it("abre painel custom e dispara onChange", () => {
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
    expect(document.querySelector(".delpi-ui-select__panel")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Número" }));
    expect(values).toEqual(["number"]);
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
