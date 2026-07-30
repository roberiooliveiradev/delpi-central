import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { EditorChrome } from "./EditorChrome";
import { EditorChromeNotice, EditorChromeNotices } from "./EditorChromeNotice";

describe("EditorChromeNotice", () => {
  it("renderiza tone e ação", () => {
    const onAction = vi.fn();
    render(
      <EditorChromeNotice tone="warning" actionLabel="Ok" onAction={onAction}>
        Aviso de teste
      </EditorChromeNotice>,
    );
    expect(screen.getByRole("status").className).toContain(
      "delpi-ui-editor-chrome-notice--warning",
    );
    fireEvent.click(screen.getByRole("button", { name: "Ok" }));
    expect(onAction).toHaveBeenCalledTimes(1);
  });
});

describe("EditorChrome notices slot", () => {
  it("encaixa avisos entre head e ribbon", () => {
    render(
      <EditorChrome
        leading={<span>Lead</span>}
        notices={
          <EditorChromeNotices>
            <EditorChromeNotice tone="info">Editando: Ana</EditorChromeNotice>
          </EditorChromeNotices>
        }
        ribbon={<div>Ribbon</div>}
      >
        <div>Body</div>
      </EditorChrome>,
    );
    expect(screen.getByText("Editando: Ana")).toBeTruthy();
    const notices = document.querySelector(".delpi-ui-editor-chrome__notices");
    expect(notices).toBeTruthy();
    expect(notices?.textContent).toContain("Editando: Ana");
  });
});
