import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { NativeCheckboxControl } from "./NativeCheckboxControl";
import { NativeTextControl } from "./NativeTextControl";

describe("NativeCheckboxControl", () => {
  it("dispara onChange com boolean", () => {
    const values: boolean[] = [];
    render(
      <NativeCheckboxControl
        id="chk"
        checked={false}
        label="Ativo"
        onChange={(checked) => values.push(checked)}
      />,
    );
    fireEvent.click(screen.getByLabelText("Ativo"));
    expect(values).toEqual([true]);
  });
});

describe("NativeTextControl", () => {
  it("dispara onChange com string", () => {
    const values: string[] = [];
    render(
      <NativeTextControl id="txt" value="" aria-label="Nome" onChange={(value) => values.push(value)} />,
    );
    fireEvent.change(screen.getByLabelText("Nome"), { target: { value: "OTD" } });
    expect(values).toEqual(["OTD"]);
  });
});
