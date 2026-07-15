import { afterEach, describe, expect, it } from "vitest";

import {
  disposeEditorShortcutSession,
  getEditorShortcutSession,
} from "./editorShortcutSession";

afterEach(() => {
  disposeEditorShortcutSession();
});

describe("EditorShortcutSession", () => {
  it("só preventDefault quando o handler retorna handled — F12 livre", () => {
    const live = getEditorShortcutSession();
    live.register(
      "claim-f1",
      (event) => (event.key === "F1" ? { handled: true } : undefined),
      { phase: "capture", priority: 10 },
    );

    const f12 = new KeyboardEvent("keydown", { key: "F12", bubbles: true, cancelable: true });
    window.dispatchEvent(f12);
    expect(f12.defaultPrevented).toBe(false);

    const f1 = new KeyboardEvent("keydown", { key: "F1", bubbles: true, cancelable: true });
    window.dispatchEvent(f1);
    expect(f1.defaultPrevented).toBe(true);
  });

  it("setEnabled(false) impede claim mesmo com handler", () => {
    const live = getEditorShortcutSession();
    live.register("claim", () => ({ handled: true }), { phase: "capture" });
    live.setEnabled(false);
    const event = new KeyboardEvent("keydown", { key: "Delete", bubbles: true, cancelable: true });
    window.dispatchEvent(event);
    expect(event.defaultPrevented).toBe(false);
  });

  it("dispose remove listeners e libera teclas do browser", () => {
    const live = getEditorShortcutSession();
    live.register("claim", () => ({ handled: true }), { phase: "capture" });
    disposeEditorShortcutSession();
    const event = new KeyboardEvent("keydown", { key: "F1", bubbles: true, cancelable: true });
    window.dispatchEvent(event);
    expect(event.defaultPrevented).toBe(false);
  });
});
