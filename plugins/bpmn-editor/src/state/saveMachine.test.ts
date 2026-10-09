import { describe, expect, it } from "vitest";

import { SaveMachine } from "./saveMachine";

describe("SaveMachine (P4 §12/§13)", () => {
  it("LOADING → CLEAN on editable load", () => {
    const m = new SaveMachine();
    m.dispatch({ type: "LOAD_OK", editable: true });
    expect(m.state).toBe("CLEAN");
    expect(m.dirty()).toBe(false);
  });

  it("LOADING → READ_ONLY on non-editable load", () => {
    const m = new SaveMachine();
    m.dispatch({ type: "LOAD_OK", editable: false });
    expect(m.state).toBe("READ_ONLY");
  });

  it("CLEAN → DIRTY on execute; undo to save point → CLEAN", () => {
    const m = new SaveMachine();
    m.dispatch({ type: "LOAD_OK", editable: true });
    m.dispatch({ type: "COMMAND", trigger: "execute" });
    expect(m.state).toBe("DIRTY");
    m.dispatch({ type: "COMMAND", trigger: "undo" });
    expect(m.state).toBe("CLEAN");
  });

  it("branch-aware: undo→undo→new execute ≠ save point", () => {
    const m = new SaveMachine();
    m.dispatch({ type: "LOAD_OK", editable: true });
    m.dispatch({ type: "COMMAND", trigger: "execute" });
    m.dispatch({ type: "COMMAND", trigger: "execute" });
    m.dispatch({ type: "SAVE_REQUEST" });
    m.dispatch({ type: "SAVE_VERIFIED" });
    expect(m.state).toBe("CLEAN");
    // undo além do save point: estado ≠ salvo
    m.dispatch({ type: "COMMAND", trigger: "undo" });
    m.dispatch({ type: "COMMAND", trigger: "undo" });
    expect(m.state).toBe("DIRTY");
    // nova branch: mesma profundidade, identidade diferente → DIRTY
    m.dispatch({ type: "COMMAND", trigger: "execute" });
    m.dispatch({ type: "COMMAND", trigger: "execute" });
    expect(m.state).toBe("DIRTY");
    // undo/redo dentro da nova branch nunca volta a ser CLEAN
    m.dispatch({ type: "COMMAND", trigger: "undo" });
    m.dispatch({ type: "COMMAND", trigger: "undo" });
    m.dispatch({ type: "COMMAND", trigger: "undo" });
    expect(m.state).toBe("DIRTY");
    m.dispatch({ type: "COMMAND", trigger: "redo" });
    m.dispatch({ type: "COMMAND", trigger: "redo" });
    m.dispatch({ type: "COMMAND", trigger: "redo" });
    expect(m.state).toBe("DIRTY");
  });

  it("redo além do save point → DIRTY", () => {
    const m = new SaveMachine();
    m.dispatch({ type: "LOAD_OK", editable: true });
    m.dispatch({ type: "COMMAND", trigger: "execute" });
    m.dispatch({ type: "COMMAND", trigger: "undo" });
    expect(m.state).toBe("CLEAN");
    m.dispatch({ type: "COMMAND", trigger: "redo" });
    expect(m.state).toBe("DIRTY");
  });

  it("full save cycle: DIRTY → SAVING → CLEAN", () => {
    const m = new SaveMachine();
    m.dispatch({ type: "LOAD_OK", editable: true });
    m.dispatch({ type: "COMMAND", trigger: "execute" });
    m.dispatch({ type: "SAVE_REQUEST" });
    expect(m.state).toBe("SAVING");
    m.dispatch({ type: "SAVE_VERIFIED" });
    expect(m.state).toBe("CLEAN");
    expect(m.dirty()).toBe(false);
  });

  it("VALIDATION_BLOCKED → back to DIRTY, edit preserved", () => {
    const m = new SaveMachine();
    m.dispatch({ type: "LOAD_OK", editable: true });
    m.dispatch({ type: "COMMAND", trigger: "execute" });
    m.dispatch({ type: "SAVE_REQUEST" });
    m.dispatch({ type: "VALIDATION_BLOCKED" });
    expect(m.state).toBe("DIRTY");
    expect(m.dirty()).toBe(true);
  });

  it("version conflict → CONFLICT; reload resolves", () => {
    const m = new SaveMachine();
    m.dispatch({ type: "LOAD_OK", editable: true });
    m.dispatch({ type: "COMMAND", trigger: "execute" });
    m.dispatch({ type: "SAVE_REQUEST" });
    m.dispatch({ type: "VERSION_CONFLICT" });
    expect(m.state).toBe("CONFLICT");
    m.dispatch({ type: "CONFLICT_RELOAD" });
    expect(m.state).toBe("READ_ONLY");
  });

  it("network failure → SAVE_FAILED → retry → SAVING", () => {
    const m = new SaveMachine();
    m.dispatch({ type: "LOAD_OK", editable: true });
    m.dispatch({ type: "COMMAND", trigger: "execute" });
    m.dispatch({ type: "SAVE_REQUEST" });
    m.dispatch({ type: "SAVE_FAILED" });
    expect(m.state).toBe("SAVE_FAILED");
    expect(m.canSave()).toBe(true);
    m.dispatch({ type: "RETRY_SAVE" });
    expect(m.state).toBe("SAVING");
  });

  it("SAVE_REQUEST ignored when CLEAN (no-op)", () => {
    const m = new SaveMachine();
    m.dispatch({ type: "LOAD_OK", editable: true });
    m.dispatch({ type: "SAVE_REQUEST" });
    expect(m.state).toBe("CLEAN");
  });

  it("commands in READ_ONLY do not flip to DIRTY", () => {
    const m = new SaveMachine();
    m.dispatch({ type: "LOAD_OK", editable: false });
    m.dispatch({ type: "COMMAND", trigger: "execute" });
    expect(m.state).toBe("READ_ONLY");
  });
});
