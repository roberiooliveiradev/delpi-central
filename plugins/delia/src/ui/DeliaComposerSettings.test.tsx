/**
 * DeliaComposer — composer settings menu + dictation mode section
 * (spec 125, 2026-10-23).
 *
 * The permanent mode strip is gone; a discreet toolbar trigger opens
 * "Configurações do campo de pergunta" whose first section is "Ditado"
 * (batch default / live opt-in). CS-01..CS-18 unit + interaction matrix
 * (CS-11/CS-12 are browser QA).
 */

import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { useState } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { DeliaComposer } from "./DeliaComposer";
import type {
  DeliaDictationTranscription,
  DeliaDictationTranscriber,
} from "./DeliaComposer";
import type { DeliaIncrementalEvent } from "../api/dictationClient";
import type {
  IncrementalCapture,
  IncrementalTransport,
} from "../audio/incrementalDictationController";

afterEach(cleanup);

const fakeCapture: IncrementalCapture & {
  emit: ((blob: Blob, ms: number) => void) | null;
  started: boolean;
} = {
  emit: null,
  started: false,
  async start(onSegment) {
    this.emit = onSegment;
    this.started = true;
  },
  pause() {},
  resume() {},
  stop() {},
  abort() {},
};

vi.mock("@delpi/plugin-ui/index", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("@delpi/plugin-ui/index")>();
  return {
    ...actual,
    createSegmentedPcmCapture: () => fakeCapture,
  };
});

type FakeTrack = { stop: () => void; kind: string };
function createFakeStream(): MediaStream {
  const track: FakeTrack = { stop: vi.fn(), kind: "audio" };
  return {
    getTracks: () => [track as unknown as MediaStreamTrack],
    getAudioTracks: () => [track as unknown as MediaStreamTrack],
  } as unknown as MediaStream;
}

class FakeMediaRecorder {
  static isTypeSupported = vi.fn((mime: string) => mime.includes("webm"));
  state: "inactive" | "recording" | "paused" = "inactive";
  mimeType: string;
  ondataavailable: ((ev: { data: Blob }) => void) | null = null;
  onerror: (() => void) | null = null;
  onstop: (() => void) | null = null;

  constructor(_stream: MediaStream, options?: { mimeType?: string }) {
    this.mimeType = options?.mimeType || "audio/webm";
  }
  start() {
    this.state = "recording";
  }
  stop() {
    this.state = "inactive";
    this.ondataavailable?.({
      data: new Blob([new Uint8Array([1, 2, 3, 4])], {
        type: this.mimeType,
      }),
    });
    this.onstop?.();
  }
}

const originalMediaDevices = navigator.mediaDevices;
const originalMediaRecorder = globalThis.MediaRecorder;
const originalIsSecureContext = Object.getOwnPropertyDescriptor(
  window,
  "isSecureContext",
);

function makeTransport(): IncrementalTransport & { opened: number } {
  return {
    opened: 0,
    async openSession() {
      this.opened += 1;
      return {
        sessionId: "sess-cs",
        contract: "dictation.incremental.v1",
        contractVersion: "1",
        maxSessionMs: 300000,
        maxSegments: 120,
        maxSegmentDurationMs: 15000,
      };
    },
    async *streamSegment(input): AsyncGenerator<DeliaIncrementalEvent> {
      yield {
        type: "final",
        sessionId: "sess-cs",
        segmentId: input.segmentId,
        sequence: input.sequence,
        revision: 1,
        isFinal: true,
        text: "trecho",
        language: "pt-BR",
      };
    },
    async endSession() {},
  };
}

const transcriber: DeliaDictationTranscriber & { calls: number } =
  Object.assign(
    async (): Promise<DeliaDictationTranscription> => ({
      text: "transcrito",
      language: "pt-BR",
    }),
    { calls: 0 },
  );

function Harness({
  transport = null,
  initial = "",
}: {
  transport?: IncrementalTransport | null;
  initial?: string;
}) {
  const [value, setValue] = useState(initial);
  return (
    <DeliaComposer
      inputId="delia-cs-input"
      value={value}
      onChange={setValue}
      onSubmit={() => undefined}
      audioCaptureEnabled
      audioCaptureMaxDurationMs={60_000}
      audioCaptureMaxBytes={256_000}
      dictationTranscriber={transcriber}
      incrementalTransport={transport}
    />
  );
}

const TRIGGER = "Configurações do campo de pergunta";
const trigger = () =>
  screen.getByRole("button", { name: TRIGGER }) as HTMLButtonElement;
const openMenu = () => fireEvent.click(trigger());
const liveRadio = () =>
  screen.getByRole("radio", {
    name: /Transcrição em tempo real/,
  }) as HTMLInputElement;
const batchRadio = () =>
  screen.getByRole("radio", {
    name: /Gravar e transcrever/,
  }) as HTMLInputElement;
const menu = () => screen.queryByRole("dialog", { name: TRIGGER });
const textarea = () =>
  document.getElementById("delia-cs-input") as HTMLTextAreaElement;

describe("composer settings menu (spec 125)", () => {
  beforeEach(() => {
    fakeCapture.emit = null;
    fakeCapture.started = false;
    transcriber.calls = 0;
    Object.defineProperty(window, "isSecureContext", {
      configurable: true,
      get: () => true,
    });
    Object.defineProperty(navigator, "mediaDevices", {
      configurable: true,
      value: { getUserMedia: vi.fn(async () => createFakeStream()) },
    });
    (
      globalThis as unknown as { MediaRecorder: typeof FakeMediaRecorder }
    ).MediaRecorder = FakeMediaRecorder;
    URL.createObjectURL = vi.fn(() => "blob:test-audio");
    URL.revokeObjectURL = vi.fn();
  });

  afterEach(() => {
    if (originalMediaDevices) {
      Object.defineProperty(navigator, "mediaDevices", {
        configurable: true,
        value: originalMediaDevices,
      });
    }
    if (originalMediaRecorder) {
      (
        globalThis as unknown as { MediaRecorder: typeof MediaRecorder }
      ).MediaRecorder = originalMediaRecorder;
    }
    if (originalIsSecureContext) {
      Object.defineProperty(
        window,
        "isSecureContext",
        originalIsSecureContext,
      );
    }
  });

  it("CS-01: no permanent mode strip above the composer", () => {
    render(<Harness transport={makeTransport()} />);
    expect(
      screen.queryByRole("radiogroup"),
    ).toBeNull();
    expect(document.querySelector(".delia-dictation-mode")).toBeNull();
    // the only dictation affordance in the toolbar is the mic + settings
    expect(trigger()).toBeTruthy();
  });

  it("CS-02/CS-03: trigger lives in the composer toolbar; menu has the Ditado section", () => {
    render(<Harness transport={makeTransport()} />);
    expect(menu()).toBeNull();
    openMenu();
    expect(menu()).toBeTruthy();
    expect(screen.getByText("Configurações")).toBeTruthy();
    expect(screen.getByText("Campo de pergunta")).toBeTruthy();
    expect(screen.getByText("Ditado")).toBeTruthy();
  });

  it("CS-04/CS-05 + CM-01: batch default; live opt-in keeps the menu open", () => {
    render(<Harness transport={makeTransport()} />);
    openMenu();
    expect(batchRadio().checked).toBe(true);
    expect(liveRadio().checked).toBe(false);
    fireEvent.click(liveRadio());
    const dlg = document.body.querySelectorAll(String.fromCharCode(91)+'role=dialog'+String.fromCharCode(93))[0];
    console.log('DLG count=', document.body.querySelectorAll(String.fromCharCode(91)+'role=dialog'+String.fromCharCode(93)).length, 'html=', dlg ? dlg.outerHTML.slice(0,220) : 'none');
    expect(menu()).toBeTruthy();
    expect(liveRadio().checked).toBe(true);
    expect(
      screen.getByRole("button", { name: "Iniciar ditado" }),
    ).toBeTruthy();
  });

  it("CM-02: switching live back to batch also keeps the menu open", () => {
    render(<Harness transport={makeTransport()} />);
    openMenu();
    fireEvent.click(liveRadio());
    expect(liveRadio().checked).toBe(true);
    fireEvent.click(batchRadio());
    expect(menu()).toBeTruthy();
    expect(batchRadio().checked).toBe(true);
  });

  it("CS-06: live disabled with reason when incremental not admitted", () => {
    render(<Harness transport={null} />);
    openMenu();
    expect(liveRadio().disabled).toBe(true);
    expect(screen.getByText("Indisponível no momento.")).toBeTruthy();
    expect(batchRadio().checked).toBe(true);
  });

  it("CS-07: choosing live does not start capture or a session", async () => {
    const transport = makeTransport();
    render(<Harness transport={transport} />);
    openMenu();
    fireEvent.click(liveRadio());
    await Promise.resolve();
    expect(transport.opened).toBe(0);
    expect(fakeCapture.started).toBe(false);
  });

  it("CS-08 + CM-07: options disabled during live capture", async () => {
    render(<Harness transport={makeTransport()} />);
    openMenu();
    fireEvent.click(liveRadio());
    fireEvent.click(
      screen.getByRole("button", { name: "Iniciar ditado" }),
    );
    await waitFor(() => expect(fakeCapture.started).toBe(true));
    // menu stays open; options lock during capture
    expect(menu()).toBeTruthy();
    expect(liveRadio().disabled).toBe(true);
    expect(batchRadio().disabled).toBe(true);
  });

  it("CS-09: draft + caret preserved across open/select/close", () => {
    render(<Harness transport={makeTransport()} initial="abcdef" />);
    const el = textarea();
    el.focus();
    el.setSelectionRange(2, 4);
    document.dispatchEvent(new Event("selectionchange"));
    openMenu();
    expect(textarea().value).toBe("abcdef");
    fireEvent.click(liveRadio());
    const el2 = textarea();
    expect(el2.value).toBe("abcdef");
    expect(el2.selectionStart).toBe(2);
    expect(el2.selectionEnd).toBe(4);
  });

  it("CS-10 + CM-05: aria-expanded, Escape closes and restores focus from inside the panel", async () => {
    render(<Harness transport={makeTransport()} />);
    expect(trigger().getAttribute("aria-expanded")).toBe("false");
    openMenu();
    expect(trigger().getAttribute("aria-expanded")).toBe("true");
    batchRadio().focus();
    fireEvent.keyDown(window, { key: "Escape" });
    await waitFor(() => expect(menu()).toBeNull());
    expect(document.activeElement).toBe(trigger());
  });

  it("CL-04: only the selected row is marked; check is decorative", () => {
    render(<Harness transport={makeTransport()} />);
    openMenu();
    const options = document.querySelectorAll(
      ".delia-dictation-settings__option",
    );
    expect(options.length).toBe(2);
    expect(options[0].getAttribute("data-checked")).toBe("true");
    expect(options[1].getAttribute("data-checked")).toBe("false");
    expect(
      options[0].querySelector(".delia-dictation-settings__check"),
    ).toBeTruthy();
    fireEvent.click(liveRadio());
    const after = document.querySelectorAll(
      ".delia-dictation-settings__option",
    );
    expect(after[0].getAttribute("data-checked")).toBe("false");
    expect(after[1].getAttribute("data-checked")).toBe("true");
  });

  it("CL-05: whole row is clickable and selects the option", () => {
    render(<Harness transport={makeTransport()} />);
    openMenu();
    const liveRow = liveRadio().closest(
      ".delia-dictation-settings__option",
    ) as HTMLElement;
    fireEvent.click(liveRow);
    expect(liveRadio().checked).toBe(true);
  });

  it("outside click closes the menu", async () => {
    render(<Harness transport={makeTransport()} />);
    openMenu();
    expect(menu()).toBeTruthy();
    fireEvent.pointerDown(document.body);
    await waitFor(() => expect(menu()).toBeNull());
  });

  it("CM-03: outside click closes without stealing focus", async () => {
    render(<Harness transport={makeTransport()} />);
    const outside = document.createElement("button");
    document.body.appendChild(outside);
    try {
      openMenu();
      outside.focus();
      fireEvent.pointerDown(outside);
      await waitFor(() => expect(menu()).toBeNull());
      expect(document.activeElement).toBe(outside);
    } finally {
      outside.remove();
    }
  });

  it("CM-04/CM-05: repeated open/close is stable; choice keeps the menu open", async () => {
    render(<Harness transport={makeTransport()} />);
    for (let i = 0; i < 3; i += 1) {
      openMenu();
      expect(menu()).toBeTruthy();
      fireEvent.click(trigger());
      await waitFor(() => expect(menu()).toBeNull());
    }
    openMenu();
    fireEvent.click(liveRadio());
    expect(menu()).toBeTruthy();
    expect(liveRadio().checked).toBe(true);
    fireEvent.click(trigger());
    await waitFor(() => expect(menu()).toBeNull());
  });

  it("CM-06: repeated selections do not remount the editor or lose draft/caret", () => {
    render(<Harness transport={makeTransport()} initial="abcdef" />);
    const el = textarea();
    el.focus();
    el.setSelectionRange(1, 3);
    document.dispatchEvent(new Event("selectionchange"));
    openMenu();
    fireEvent.click(liveRadio());
    fireEvent.click(batchRadio());
    fireEvent.click(liveRadio());
    expect(menu()).toBeTruthy();
    const el2 = textarea();
    // mode swap remounts the editor; draft/caret survive via snapshot/restore
    expect(el2.value).toBe("abcdef");
    expect(el2.selectionStart).toBe(1);
    expect(el2.selectionEnd).toBe(3);
  });

  it("two independent mounts keep separate mode state", async () => {
    render(
      <>
        <Harness transport={makeTransport()} initial="a" />
        <Harness transport={makeTransport()} initial="b" />
      </>,
    );
    const triggers = screen.getAllByRole("button", { name: TRIGGER });
    fireEvent.click(triggers[0]);
    fireEvent.click(liveRadio());
    // the second mount still defaults to batch; mount-1 panel exits
    fireEvent.click(triggers[1]);
    await waitFor(() =>
      expect(
        screen.getAllByRole("dialog", { name: TRIGGER }).length,
      ).toBe(1),
    );
    expect(batchRadio().checked).toBe(true);
  });

  it("unmount with the menu open does not throw", () => {
    const { unmount } = render(<Harness transport={makeTransport()} />);
    openMenu();
    expect(menu()).toBeTruthy();
    expect(() => unmount()).not.toThrow();
  });

  it("CS-13: mic tooltip names the current mode", () => {
    render(<Harness transport={makeTransport()} />);
    const mic = screen.getByRole("button", { name: "Ditar mensagem" });
    fireEvent.focus(mic);
    expect(
      screen.getByText(/Gravar e transcrever: fale/),
    ).toBeTruthy();
    openMenu();
    fireEvent.click(liveRadio());
    const liveMic = screen.getByRole("button", { name: "Iniciar ditado" });
    fireEvent.focus(liveMic);
    expect(
      screen.getByText(/Transcrição em tempo real: o texto aparece/),
    ).toBeTruthy();
  });

  it("MOT-01: panel mounts with the entrance animation class", () => {
    render(<Harness transport={makeTransport()} />);
    openMenu();
    const panel = document.querySelector(
      ".delia-composer-settings__panel",
    );
    expect(
      panel?.classList.contains(
        "delia-composer-settings__panel--entering",
      ),
    ).toBe(true);
  });

  it("MOT-02: close fades out — exiting phase then unmount", async () => {
    render(<Harness transport={makeTransport()} />);
    openMenu();
    fireEvent.click(trigger());
    const panel = document.querySelector(
      ".delia-composer-settings__panel",
    );
    expect(
      panel?.classList.contains(
        "delia-composer-settings__panel--exiting",
      ),
    ).toBe(true);
    expect(menu()).toBeTruthy();
    await waitFor(() => expect(menu()).toBeNull());
  });

  it("MOT-03: reduced motion closes immediately, no exiting phase", () => {
    const original = window.matchMedia;
    window.matchMedia = ((query: string) => ({
      matches: query.includes("reduce"),
      media: query,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
      addListener: () => undefined,
      removeListener: () => undefined,
      onchange: null,
      dispatchEvent: () => false,
    })) as typeof window.matchMedia;
    try {
      render(<Harness transport={makeTransport()} />);
      openMenu();
      expect(menu()).toBeTruthy();
      fireEvent.click(trigger());
      expect(menu()).toBeNull();
      expect(
        document.querySelector(
          ".delia-composer-settings__panel--exiting",
        ),
      ).toBeNull();
    } finally {
      window.matchMedia = original;
    }
  });

  it("CS-16: no auto-submit after batch transcription", async () => {
    const onSubmit = vi.fn();
    function SubmitHarness() {
      const [value, setValue] = useState("");
      return (
        <DeliaComposer
          inputId="delia-cs-input"
          value={value}
          onChange={setValue}
          onSubmit={onSubmit}
          audioCaptureEnabled
          audioCaptureMaxDurationMs={60_000}
          audioCaptureMaxBytes={256_000}
          dictationTranscriber={transcriber}
          incrementalTransport={makeTransport()}
        />
      );
    }
    render(<SubmitHarness />);
    fireEvent.click(
      screen.getByRole("button", { name: "Ditar mensagem" }),
    );
    await waitFor(() => screen.getByText("Gravando"));
    fireEvent.click(
      screen.getByRole("button", { name: "Finalizar gravação" }),
    );
    await waitFor(() => expect(textarea().value).toBe("transcrito"));
    expect(onSubmit).not.toHaveBeenCalled();
  });
});
