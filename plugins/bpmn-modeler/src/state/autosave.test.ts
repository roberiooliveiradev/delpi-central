import { describe, expect, it, vi } from "vitest";

import { AutosaveController } from "./autosave";
import { SaveMachine, type SaveState } from "./saveMachine";
import { BpmnModelerApiError } from "../data/api/bpmnModelerApi";

function apiError(status: number, code = "X"): BpmnModelerApiError {
  return new BpmnModelerApiError(status, {
    success: false,
    error: { code, message: code },
    meta: { request_id: "t" },
  }, `HTTP ${status}`);
}

type WriteImpl = (xml: string, version: number) => Promise<{ version: number }>;

function build(
  overrides: {
    writeImpl?: WriteImpl;
    readBackXml?: () => string;
    refresh?: () => Promise<boolean>;
    canAutosave?: () => boolean;
  } = {},
) {
  const machine = new SaveMachine();
  machine.dispatch({ type: "LOAD_OK", editable: true });

  let currentXml = "<xml>base</xml>";
  let version = 1;
  const states: SaveState[] = [];
  const writtenXml: string[] = [];

  const defaultWrite: WriteImpl = async (xml) => {
    writtenXml.push(xml);
    version += 1;
    return { version };
  };

  const controller = new AutosaveController({
    machine,
    canAutosave: overrides.canAutosave ?? (() => true),
    exportXml: async () => currentXml,
    write: overrides.writeImpl ?? defaultWrite,
    readBack: async () => ({
      xml: overrides.readBackXml
        ? overrides.readBackXml()
        : writtenXml[writtenXml.length - 1] ?? "",
      version,
    }),
    getVersion: () => version,
    setVersion: (v) => {
      version = v;
    },
    requestTokenRefresh: overrides.refresh ?? (async () => true),
    emit: (s) => states.push(s),
    debounceMs: 5,
  });

  const edit = (xml: string) => {
    currentXml = xml;
    machine.dispatch({ type: "COMMAND", trigger: "execute" });
    controller.notifyCommand();
  };

  return {
    machine,
    controller,
    edit,
    states,
    writtenXml,
    writes: () => writtenXml.length,
    persisted: () => writtenXml[writtenXml.length - 1] ?? "",
  };
}

const tick = (ms = 40) => new Promise((r) => setTimeout(r, ms));

describe("AutosaveController", () => {
  it("comando → debounce → write + read-back → CLEAN", async () => {
    const w = build();
    w.edit("<xml>a</xml>");
    expect(w.machine.state).toBe("DIRTY");
    await tick();
    expect(w.writes()).toBe(1);
    expect(w.machine.state).toBe("CLEAN");
    expect(w.persisted()).toBe("<xml>a</xml>");
  });

  it("coalescing: burst de 20 comandos = 1 write do estado final", async () => {
    const w = build();
    for (let i = 0; i < 20; i++) w.edit(`<xml>e${i}</xml>`);
    await tick();
    expect(w.writes()).toBe(1);
    expect(w.persisted()).toBe("<xml>e19</xml>");
    expect(w.machine.state).toBe("CLEAN");
  });

  it("edição durante save in-flight → write seguinte carrega o estado mais novo", async () => {
    let release!: () => void;
    const gate = new Promise<void>((r) => (release = r));
    let calls = 0;
    const w = build({
      writeImpl: async (xml) => {
        calls += 1;
        w.writtenXml.push(xml);
        if (calls === 1) await gate;
        return { version: calls + 1 };
      },
    });
    w.edit("<xml>A</xml>");
    await tick(15); // debounce passou → write A in-flight (bloqueado no gate)
    expect(w.machine.state).toBe("SAVING");
    w.edit("<xml>B</xml>");
    w.edit("<xml>C</xml>");
    release();
    await tick(80);
    expect(calls).toBe(2);
    expect(w.writtenXml[0]).toBe("<xml>A</xml>");
    expect(w.writtenXml[1]).toBe("<xml>C</xml>"); // B coalescido
    expect(w.machine.state).toBe("CLEAN");
    expect(w.machine.dirty()).toBe(false);
  });

  it("read-back divergente → SAVE_FAILED, nunca Salvo", async () => {
    const w = build({ readBackXml: () => "<xml>OTHER</xml>" });
    w.edit("<xml>x</xml>");
    await tick();
    expect(w.machine.state).toBe("SAVE_FAILED");
    expect(w.machine.dirty()).toBe(true);
  });

  it("401 → refresh → 1 retry → CLEAN", async () => {
    let calls = 0;
    const refresh = vi.fn(async () => true);
    const w = build({
      refresh,
      writeImpl: async (xml) => {
        calls += 1;
        if (calls === 1) throw apiError(401, "AUTHENTICATION_FAILED");
        w.writtenXml.push(xml);
        return { version: 2 };
      },
    });
    w.edit("<xml>auth</xml>");
    await tick();
    expect(refresh).toHaveBeenCalledTimes(1);
    expect(calls).toBe(2);
    expect(w.machine.state).toBe("CLEAN");
  });

  it("401 persistente → SESSION_EXPIRED, dirty preservado", async () => {
    const w = build({
      writeImpl: async () => {
        throw apiError(401, "AUTHENTICATION_FAILED");
      },
    });
    w.edit("<xml>x</xml>");
    await tick();
    expect(w.machine.state).toBe("SESSION_EXPIRED");
    expect(w.machine.dirty()).toBe(true);
  });

  it("403 → READ_ONLY (fail closed, sem retry silencioso)", async () => {
    const w = build({
      writeImpl: async () => {
        throw apiError(403, "FORBIDDEN");
      },
    });
    w.edit("<xml>x</xml>");
    await tick();
    expect(w.machine.state).toBe("READ_ONLY");
  });

  it("CONFLICT → estado CONFLICT, nunca overwrite silencioso", async () => {
    const w = build({
      writeImpl: async () => {
        throw apiError(409, "CONFLICT");
      },
    });
    w.edit("<xml>x</xml>");
    await tick();
    expect(w.machine.state).toBe("CONFLICT");
    expect(w.machine.dirty()).toBe(true);
  });

  it("TypeError (rede) → OFFLINE com trabalho preservado", async () => {
    const w = build({
      writeImpl: async () => {
        throw new TypeError("fetch failed");
      },
    });
    w.edit("<xml>x</xml>");
    await tick();
    expect(w.machine.state).toBe("OFFLINE");
    expect(w.machine.dirty()).toBe(true);
  });

  it("flush() persiste imediatamente (guard de navegação/Ctrl+S)", async () => {
    const w = build();
    w.edit("<xml>nav</xml>");
    const ok = await w.controller.flush();
    expect(ok).toBe(true);
    expect(w.machine.state).toBe("CLEAN");
    expect(w.writes()).toBe(1);
  });

  it("nova edição após SAVE_FAILED re-agenda autosave", async () => {
    let fail = true;
    const w = build({
      writeImpl: async (xml) => {
        if (fail) throw apiError(500, "INFRA");
        w.writtenXml.push(xml);
        return { version: 2 };
      },
    });
    w.edit("<xml>a</xml>");
    await tick();
    expect(w.machine.state).toBe("SAVE_FAILED");
    fail = false;
    w.edit("<xml>b</xml>");
    await tick();
    expect(w.machine.state).toBe("CLEAN");
    expect(w.persisted()).toBe("<xml>b</xml>");
  });
});
