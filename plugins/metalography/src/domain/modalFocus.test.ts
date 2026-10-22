/** @vitest-environment jsdom */
import { afterEach, describe, expect, it } from "vitest";

import { retainModalFocus } from "./modalFocus";

function dialog(): HTMLElement {
  const root = document.createElement("div");
  root.innerHTML = `<div role="dialog"><button type="button" id="cancel">Cancelar</button><button type="button" id="confirm">Confirmar</button></div>`;
  document.body.appendChild(root);
  return root.querySelector("[role='dialog']") as HTMLElement;
}

describe("retainModalFocus", () => {
  afterEach(() => {
    document.body.innerHTML = "";
  });

  it("foca o primeiro controle e devolve o foco ao fechar", () => {
    const opener = document.createElement("button");
    opener.textContent = "Excluir";
    document.body.appendChild(opener);
    opener.focus();

    const release = retainModalFocus(dialog());
    expect(document.activeElement?.id).toBe("cancel");

    release();
    expect(document.activeElement).toBe(opener);
  });

  it("circula o Tab dentro do diálogo e não leva o foco para fora", () => {
    const panel = dialog();
    retainModalFocus(panel);
    const confirm = panel.querySelector("#confirm") as HTMLButtonElement;
    confirm.focus();

    const event = new KeyboardEvent("keydown", { key: "Tab", bubbles: true, cancelable: true });
    panel.dispatchEvent(event);

    expect(event.defaultPrevented).toBe(true);
    expect(document.activeElement?.id).toBe("cancel");
  });
});
