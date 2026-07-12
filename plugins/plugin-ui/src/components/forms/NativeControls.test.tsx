import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { NativeCheckboxControl } from "./NativeCheckboxControl";
import { NativeSwitchControl } from "./NativeSwitchControl";
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

  it("renderiza hint junto do label", () => {
    render(
      <NativeCheckboxControl
        checked={false}
        label="Master"
        hint="Logo compartilhado"
        onChange={() => undefined}
      />,
    );
    expect(screen.getByText("Logo compartilhado")).toBeTruthy();
  });
});

describe("NativeSwitchControl", () => {
  it("dispara onChange com role switch", () => {
    const values: boolean[] = [];
    render(
      <NativeSwitchControl
        checked={false}
        aria-label="Ativar"
        onChange={(checked) => values.push(checked)}
      />,
    );
    fireEvent.click(screen.getByRole("switch", { name: "Ativar" }));
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

  it("aceita type search e password", () => {
    const { rerender } = render(
      <NativeTextControl type="search" value="" aria-label="Busca" onChange={() => undefined} />,
    );
    expect((screen.getByLabelText("Busca") as HTMLInputElement).type).toBe("search");
    rerender(
      <NativeTextControl type="password" value="" aria-label="Senha" onChange={() => undefined} />,
    );
    expect((screen.getByLabelText("Senha") as HTMLInputElement).type).toBe("password");
  });
});
