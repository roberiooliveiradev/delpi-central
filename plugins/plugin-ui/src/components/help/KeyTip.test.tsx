import { afterEach, describe, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";

import { KeyTip } from "./KeyTip";

afterEach(() => {
  cleanup();
});

describe("KeyTip", () => {
  it("não renderiza balão quando inactive", () => {
    render(
      <KeyTip label="Ctrl+Z" active={false}>
        <button type="button">Desfazer</button>
      </KeyTip>,
    );
    expect(screen.getByRole("button", { name: "Desfazer" })).toBeTruthy();
    expect(document.querySelector(".delpi-ui-keytip")).toBeNull();
  });

  it("mostra balão com label quando active", () => {
    render(
      <KeyTip label="Ctrl+Z" active placement="bottom">
        <button type="button">Desfazer</button>
      </KeyTip>,
    );
    const tip = document.querySelector(".delpi-ui-keytip");
    expect(tip?.textContent).toBe("Ctrl+Z");
  });

  it("aplica variant letter e data attrs no âncora", () => {
    render(
      <KeyTip label="P" active variant="letter" data-td-keytip="P" data-td-keytip-scope="tabs">
        <button type="button">Página Inicial</button>
      </KeyTip>,
    );
    const tip = document.querySelector(".delpi-ui-keytip");
    expect(tip?.textContent).toBe("P");
    expect(tip?.className).toContain("delpi-ui-keytip--letter");
    const anchor = document.querySelector("[data-td-keytip='P']");
    expect(anchor?.getAttribute("data-td-keytip-scope")).toBe("tabs");
  });
});
