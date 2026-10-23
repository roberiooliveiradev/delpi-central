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
    expect(screen.getByText(TRIGGER)).toBeTruthy();
    expect(screen.getByText("Ditado")).toBeTruthy();
  });

  it("CS-04/CS-05: batch default; live selected only by explicit gesture", () => {
    render(<Harness transport={makeTransport()} />);
    openMenu();
    expect(batchRadio().checked).toBe(true);
    expect(liveRadio().checked).toBe(false);
    fireEvent.click(liveRadio());
    openMenu();
    expect(liveRadio().checked).toBe(true);
    expect(
      screen.getByRole("button", { name: "Iniciar ditado" }),
    ).toBeTruthy();
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

  it("CS-08: options disabled during live capture", async () => {
    render(<Harness transport={makeTransport()} />);
    openMenu();
    fireEvent.click(liveRadio());
    fireEvent.click(
      screen.getByRole("button", { name: "Iniciar ditado" }),
    );
    await waitFor(() => expect(fakeCapture.started).toBe(true));
    openMenu();
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

  it("CS-10: aria-expanded, Escape closes and restores focus", () => {
    render(<Harness transport={makeTransport()} />);
    expect(trigger().getAttribute("aria-expanded")).toBe("false");
    openMenu();
    expect(trigger().getAttribute("aria-expanded")).toBe("true");
    fireEvent.keyDown(window, { key: "Escape" });
    expect(menu()).toBeNull();
    expect(document.activeElement).toBe(
      trigger().querySelector ? trigger() : trigger(),
    );
  });

  it("outside click closes the menu", () => {
    render(<Harness transport={makeTransport()} />);
    openMenu();
    expect(menu()).toBeTruthy();
    fireEvent.pointerDown(document.body);
    expect(menu()).toBeNull();
  });

  it("repeated open/close is stable and menu closes after a choice", () => {
    render(<Harness transport={makeTransport()} />);
    for (let i = 0; i < 3; i += 1) {
      openMenu();
      expect(menu()).toBeTruthy();
      fireEvent.click(trigger());
      expect(menu()).toBeNull();
    }
    openMenu();
    fireEvent.click(liveRadio());
    expect(menu()).toBeNull();
  });

  it("two independent mounts keep separate mode state", () => {
    render(
      <>
        <Harness transport={makeTransport()} initial="a" />
        <Harness transport={makeTransport()} initial="b" />
      </>,
    );
    const triggers = screen.getAllByRole("button", { name: TRIGGER });
    fireEvent.click(triggers[0]);
    fireEvent.click(liveRadio());
    // the second mount still defaults to batch
    fireEvent.click(triggers[1]);
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
