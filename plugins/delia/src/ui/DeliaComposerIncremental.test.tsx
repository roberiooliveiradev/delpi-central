/**
 * DeliaComposer — VD-F06 incremental dictation surface.
 *
 * Proves the same composer keeps the textarea rendered and editable
 * through a live session: controls appear without replacing the write
 * area, real transport events update the draft, human edits register
 * with the reconciler, cancel keeps confirmed text, and nothing ever
 * auto-submits.
 */

import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { act } from "react";

afterEach(cleanup);

import { DeliaComposer } from "./DeliaComposer";
import type { DeliaIncrementalEvent } from "../api/dictationClient";
import type {
  IncrementalCapture,
  IncrementalTransport,
} from "../audio/incrementalDictationController";

// Capture seam: the real AudioWorklet capture cannot run in jsdom —
// inject the fake through the plugin-ui export the hook consumes.
const fakeCapture: IncrementalCapture & {
  emit: ((blob: Blob, ms: number) => void) | null;
  started: boolean;
  aborted: boolean;
  stopped: boolean;
  paused: boolean;
} = {
  emit: null,
  started: false,
  aborted: false,
  stopped: false,
  paused: false,
  async start(onSegment) {
    this.emit = onSegment;
    this.started = true;
  },
  pause() {
    this.paused = true;
  },
  resume() {
    this.paused = false;
  },
  stop() {
    this.stopped = true;
  },
  abort() {
    this.aborted = true;
  },
};

vi.mock("@delpi/plugin-ui/index", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("@delpi/plugin-ui/index")>();
  return {
    ...actual,
    createSegmentedPcmCapture: () => fakeCapture,
  };
});

function makeTransport(
  events: Record<string, DeliaIncrementalEvent[]>,
): IncrementalTransport & { ended: string[] } {
  const ended: string[] = [];
  return {
    ended,
    async openSession() {
      return {
        sessionId: "sess-ui",
        contract: "dictation.incremental.v1",
        contractVersion: "1",
        maxSessionMs: 300000,
        maxSegments: 120,
        maxSegmentDurationMs: 15000,
      };
    },
    async *streamSegment(input) {
      const queue = events[input.segmentId] ?? [
        {
          type: "final" as const,
          sessionId: "sess-ui",
          segmentId: input.segmentId,
          sequence: input.sequence,
          revision: 1,
          isFinal: true,
          text: "texto",
          language: "pt-BR",
        },
      ];
      for (const event of queue) yield event;
    },
    async endSession(sessionId) {
      ended.push(sessionId);
    },
  };
}

function Harness({
  transport,
  initial = "",
}: {
  transport: IncrementalTransport;
  initial?: string;
}) {
  const [value, setValue] = useStateWrapper(initial);
  const submitted = useSubmitCount();
  return (
    <DeliaComposer
      inputId="delia-test-input"
      value={value}
      onChange={setValue}
      onSubmit={submitted.submit}
      incrementalTransport={transport}
      incrementalMaxSessionMs={300000}
      incrementalMaxSegments={120}
    />
  );
}

// tiny state wrappers kept inside the test file
import { useState } from "react";
function useStateWrapper(initial: string) {
  return useState(initial);
}
function useSubmitCount() {
  const [count, setCount] = useState(0);
  return { count, submit: () => setCount((c) => c + 1) };
}

const PARTIALS: Record<string, DeliaIncrementalEvent[]> = {
  "seg-1": [
    {
      type: "started",
      sessionId: "sess-ui",
      segmentId: "seg-1",
      sequence: 1,
      revision: 0,
    },
    {
      type: "partial",
      sessionId: "sess-ui",
      segmentId: "seg-1",
      sequence: 1,
      revision: 1,
      text: "Mostre os",
    },
    {
      type: "partial",
      sessionId: "sess-ui",
      segmentId: "seg-1",
      sequence: 1,
      revision: 2,
      text: "Mostre os indicadores",
    },
    {
      type: "final",
      sessionId: "sess-ui",
      segmentId: "seg-1",
      sequence: 1,
      revision: 3,
      isFinal: true,
      text: "Mostre os indicadores.",
      language: "pt-BR",
    },
  ],
};

const SETTINGS_NAME = "Configurações do campo de pergunta";
// selection keeps the menu open (spec 125 §10) — dismiss explicitly so
// later steps see a deterministic surface
const selectLive = () => {
  const settingsTrigger = () =>
    screen.getByRole("button", { name: SETTINGS_NAME });
  if (screen.queryByRole("dialog", { name: SETTINGS_NAME }) == null) {
    fireEvent.click(settingsTrigger());
  }
  fireEvent.click(
    screen.getByRole("radio", { name: /Transcrição em tempo real/ }),
  );
  fireEvent.click(settingsTrigger());
};

describe("incremental dictation surface", () => {
  beforeEach(() => {
    fakeCapture.emit = null;
    fakeCapture.started = false;
    fakeCapture.aborted = false;
    fakeCapture.stopped = false;
    fakeCapture.paused = false;
  });

  it("renders the dictation trigger; textarea present", () => {
    render(<Harness transport={makeTransport({})} />);
    selectLive();
    expect(
      screen.getByRole("button", { name: "Iniciar ditado" }),
    ).toBeTruthy();
    expect(
      document.getElementById("delia-test-input"),
    ).toBeInstanceOf(HTMLTextAreaElement);
  });

  it("start shows live controls and keeps the textarea editable", async () => {
    render(<Harness transport={makeTransport(PARTIALS)} />);
    selectLive();
    fireEvent.click(screen.getByRole("button", { name: "Iniciar ditado" }));
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Pausar ditado" }),
      ).toBeTruthy(),
    );
    expect(
      screen.getByRole("button", { name: "Finalizar ditado" }),
    ).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Descartar captura" }),
    ).toBeTruthy();
    const textarea = document.getElementById(
      "delia-test-input",
    ) as HTMLTextAreaElement;
    expect(textarea).toBeInstanceOf(HTMLTextAreaElement);
    // typing during capture still works
    fireEvent.change(textarea, { target: { value: "digitado" } });
    expect(textarea.value).toBe("digitado");
  });

  it("real transport events write partial then final at the caret", async () => {
    render(<Harness transport={makeTransport(PARTIALS)} initial="base " />);
    selectLive();
    fireEvent.click(screen.getByRole("button", { name: "Iniciar ditado" }));
    await waitFor(() => expect(fakeCapture.emit).toBeTruthy());
    const textarea = document.getElementById(
      "delia-test-input",
    ) as HTMLTextAreaElement;
    textarea.setSelectionRange(5, 5);
    act(() => fakeCapture.emit?.(new Blob(["w"]), 3000));
    await waitFor(() =>
      expect(textarea.value).toBe("base Mostre os indicadores."),
    );
  });

  it("cancel keeps confirmed+human text, drops pending partial", async () => {
    const transport = makeTransport({
      "seg-1": [
        {
          type: "partial",
          sessionId: "sess-ui",
          segmentId: "seg-1",
          sequence: 1,
          revision: 1,
          text: "provisório",
        },
      ],
    });
    render(<Harness transport={transport} initial="meu " />);
    selectLive();
    fireEvent.click(screen.getByRole("button", { name: "Iniciar ditado" }));
    await waitFor(() => expect(fakeCapture.emit).toBeTruthy());
    const textarea = document.getElementById(
      "delia-test-input",
    ) as HTMLTextAreaElement;
    textarea.setSelectionRange(4, 4);
    act(() => fakeCapture.emit?.(new Blob(["w"]), 2000));
    await waitFor(() => expect(textarea.value).toBe("meu provisório"));
    fireEvent.click(
      screen.getByRole("button", { name: "Descartar captura" }),
    );
    await waitFor(() => expect(textarea.value).toBe("meu "));
    expect(transport.ended).toEqual(["sess-ui"]);
  });

  it("finalize ends the session and shows the review hint", async () => {
    render(<Harness transport={makeTransport(PARTIALS)} initial="" />);
    selectLive();
    fireEvent.click(screen.getByRole("button", { name: "Iniciar ditado" }));
    await waitFor(() => expect(fakeCapture.emit).toBeTruthy());
    act(() => fakeCapture.emit?.(new Blob(["w"]), 2000));
    fireEvent.click(screen.getByRole("button", { name: "Finalizar ditado" }));
    await waitFor(() =>
      expect(
        screen.getByText("Texto transcrito. Revise antes de enviar."),
      ).toBeTruthy(),
    );
  });

  it("never auto-submits on any dictation event", async () => {
    const submit = vi.fn();
    function Sub() {
      const [value, setValue] = useState("");
      return (
        <DeliaComposer
          inputId="delia-test-input"
          value={value}
          onChange={setValue}
          onSubmit={submit}
          incrementalTransport={makeTransport(PARTIALS)}
        />
      );
    }
    render(<Sub />);
    selectLive();
    fireEvent.click(screen.getByRole("button", { name: "Iniciar ditado" }));
    await waitFor(() => expect(fakeCapture.emit).toBeTruthy());
    act(() => fakeCapture.emit?.(new Blob(["w"]), 2000));
    await waitFor(() =>
      expect(
        (document.getElementById("delia-test-input") as HTMLTextAreaElement)
          .value,
      ).toBe("Mostre os indicadores."),
    );
    expect(submit).not.toHaveBeenCalled();
  });
});
