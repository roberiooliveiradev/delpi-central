import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";

import { NativeCheckboxControl } from "./NativeCheckboxControl";
import { NativeSelectControl } from "./NativeSelectControl";
import { NativeSwitchControl } from "./NativeSwitchControl";
import { NativeTextAreaControl } from "./NativeTextAreaControl";
import { NativeTextControl } from "./NativeTextControl";
import {
  NATIVE_CONTROL_CLASS,
  NATIVE_CONTROL_SELECT_CLASS,
  NATIVE_CONTROL_TEXTAREA_CLASS,
} from "./nativeControlClasses";

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

  it("usa classe canônica delpi-ui-native-checkbox", () => {
    const { container } = render(
      <NativeCheckboxControl checked={false} label="X" onChange={() => undefined} />,
    );
    expect(container.querySelector(".delpi-ui-native-checkbox")).toBeTruthy();
  });

  it("aceita children como alias de label (compat plugins legados)", () => {
    const { container } = render(
      <NativeCheckboxControl checked={false} onChange={() => undefined}>
        Filial SC
      </NativeCheckboxControl>,
    );
    expect(screen.getByText("Filial SC")).toBeTruthy();
    expect(container.querySelector(".delpi-ui-native-checkbox__label")?.textContent).toBe(
      "Filial SC",
    );
  });

  it("declara flex-direction row no CSS canônico (defesa contra label column do portal)", () => {
    const cssPath = resolve(
      dirname(fileURLToPath(import.meta.url)),
      "../../styles/native-controls.css",
    );
    const css = readFileSync(cssPath, "utf8");
    expect(css).toMatch(/\.delpi-ui-native-checkbox\s*\{[^}]*flex-direction:\s*row/s);
    expect(css).toMatch(/\.delpi-ui-native-switch\s*\{[^}]*flex-direction:\s*row/s);
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

  it("usa classe canônica delpi-ui-native-switch", () => {
    const { container } = render(
      <NativeSwitchControl checked={false} aria-label="S" onChange={() => undefined} />,
    );
    expect(container.querySelector(".delpi-ui-native-switch")).toBeTruthy();
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

  it("aplica classe canônica delpi-ui-native-control", () => {
    render(<NativeTextControl value="" aria-label="Campo" onChange={() => undefined} />);
    expect(screen.getByLabelText("Campo").className).toContain(NATIVE_CONTROL_CLASS);
  });
});

describe("NativeSelectControl", () => {
  it("aplica classes canônicas de select", () => {
    render(
      <NativeSelectControl
        value="a"
        aria-label="Formato"
        options={[{ value: "a", label: "A" }]}
        onChange={() => undefined}
      />,
    );
    const select = screen.getByLabelText("Formato");
    expect(select.className).toContain(NATIVE_CONTROL_CLASS);
    expect(select.className).toContain(NATIVE_CONTROL_SELECT_CLASS);
  });
});

describe("NativeTextAreaControl", () => {
  it("aplica classes canônicas de textarea", () => {
    render(
      <NativeTextAreaControl value="" aria-label="Notas" onChange={() => undefined} />,
    );
    const area = screen.getByLabelText("Notas");
    expect(area.className).toContain(NATIVE_CONTROL_CLASS);
    expect(area.className).toContain(NATIVE_CONTROL_TEXTAREA_CLASS);
  });
});
