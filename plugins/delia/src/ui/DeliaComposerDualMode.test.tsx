/**
 * DeliaComposer — dual-mode dictation (PO decision 2026-10-23,
 * spec 123 §12).
 *
 * Batch is the product default even when incremental is admitted;
 * live is explicit opt-in only. Mode switching is idle-only, keeps
 * the draft, and restores caret/selection across the subtree remount.
 * DM-01..DM-17 (DM-18 is browser QA).
 */

import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { useState } from "react";
import { act } from "react";
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

// Incremental capture seam (AudioWorklet cannot run in jsdom).
const fakeCapture: IncrementalCapture & {
  emit: ((blob: Blob, ms: number) => void) | null;
  started: boolean;
  aborted: boolean;
} = {
  emit: null,
  started: false,
  aborted: false,
  async start(onSegment) {
    this.emit = onSegment;
    this.started = true;
  },
  pause() {},
  resume() {},
  stop() {},
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

// Batch recorder seam (MediaRecorder + getUserMedia in jsdom).
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
  static instances: FakeMediaRecorder[] = [];
  state: "inactive" | "recording" | "paused" = "inactive";
  mimeType: string;
  ondataavailable: ((ev: { data: Blob }) => void) | null = null;
  onerror: (() => void) | null = null;
  onstop: (() => void) | null = null;

  constructor(_stream: MediaStream, options?: { mimeType?: string }) {
    this.mimeType = options?.mimeType || "audio/webm";
    FakeMediaRecorder.instances.push(this);
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

function makeTransport(): IncrementalTransport & {
  opened: number;
  ended: string[];
} {
  const ended: string[] = [];
  return {
    ended,
    opened: 0,
    async openSession() {
      this.opened += 1;
      return {
        sessionId: "sess-dual",
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
        sessionId: "sess-dual",
        segmentId: input.segmentId,
        sequence: input.sequence,
        revision: 1,
        isFinal: true,
        text: "trecho",
        language: "pt-BR",
      };
    },
    async endSession(sessionId) {
      ended.push(sessionId);
    },
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
  withTranscriber = true,
  initial = "",
}: {
  transport?: IncrementalTransport | null;
  withTranscriber?: boolean;
  initial?: string;
}) {
  const [value, setValue] = useState(initial);
  return (
    <DeliaComposer
      inputId="delia-dual-input"
      value={value}
      onChange={setValue}
      onSubmit={() => undefined}
      audioCaptureEnabled
      audioCaptureMaxDurationMs={60_000}
      audioCaptureMaxBytes={256_000}
      dictationTranscriber={withTranscriber ? transcriber : null}
      incrementalTransport={transport}
    />
  );
}

const LIVE_OPTION = "Transcrição em tempo real";
const BATCH_OPTION = "Gravar e transcrever";

const liveOption = () =>
  screen.getByRole("button", { name: LIVE_OPTION }) as HTMLButtonElement;
const batchOption = () =>
  screen.getByRole("button", { name: BATCH_OPTION }) as HTMLButtonElement;
const textarea = () =>
  document.getElementById("delia-dual-input") as HTMLTextAreaElement;

describe("dual-mode dictation", () => {
  beforeEach(() => {
    FakeMediaRecorder.instances = [];
    fakeCapture.emit = null;
    fakeCapture.started = false;
    fakeCapture.aborted = false;
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

  it("DM-01/DM-02/DM-17: default is batch even with incremental admitted", () => {
    render(<Harness transport={makeTransport()} />);
    expect(batchOption().getAttribute("aria-pressed")).toBe("true");
    expect(liveOption().getAttribute("aria-pressed")).toBe("false");
    // batch path rendered: VD-F03 mic, no live trigger
    expect(
      screen.getByRole("button", { name: "Ditar mensagem" }),
    ).toBeTruthy();
    expect(
      screen.queryByRole("button", { name: "Iniciar ditado" }),
    ).toBeNull();
  });

  it("DM-03/DM-04: batch records via v1 and never opens an incremental session", async () => {
    const transport = makeTransport();
    render(<Harness transport={transport} />);
    fireEvent.click(
      screen.getByRole("button", { name: "Ditar mensagem" }),
    );
    await waitFor(() => screen.getByText("Gravando"));
    expect(transport.opened).toBe(0);
    expect(
      screen.queryByRole("button", { name: "Iniciar ditado" }),
    ).toBeNull();
  });

  it("DM-05/DM-06: live requires explicit selection, then uses incremental", async () => {
    const transport = makeTransport();
    render(<Harness transport={transport} />);
    expect(
      screen.queryByRole("button", { name: "Iniciar ditado" }),
    ).toBeNull();
    fireEvent.click(liveOption());
    expect(liveOption().getAttribute("aria-pressed")).toBe("true");
    fireEvent.click(
      screen.getByRole("button", { name: "Iniciar ditado" }),
    );
    await waitFor(() => expect(transport.opened).toBe(1));
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Finalizar ditado" }),
      ).toBeTruthy(),
    );
  });

  it("DM-07: live cannot be activated when incremental is not admitted", () => {
    render(<Harness transport={null} />);
    expect(screen.queryByRole("button", { name: LIVE_OPTION })).toBeNull();
    expect(
      screen.getByRole("button", { name: "Ditar mensagem" }),
    ).toBeTruthy();
  });

  it("DM-08: no capability at all — fail-closed, typing preserved", () => {
    render(
      <DeliaComposer
        inputId="delia-dual-input"
        value="rascunho"
        onChange={() => undefined}
        onSubmit={() => undefined}
      />,
    );
    expect(screen.queryByRole("button", { name: LIVE_OPTION })).toBeNull();
    expect(
      screen.queryByRole("button", { name: BATCH_OPTION }),
    ).toBeNull();
    expect(textarea().value).toBe("rascunho");
  });

  it("DM-09/DM-12: idle switch preserves the draft", () => {
    render(<Harness transport={makeTransport()} initial="rascunho" />);
    fireEvent.click(liveOption());
    expect(textarea().value).toBe("rascunho");
    fireEvent.click(batchOption());
    expect(textarea().value).toBe("rascunho");
  });

  it("DM-10: switching is blocked during live capture", async () => {
    render(<Harness transport={makeTransport()} />);
    fireEvent.click(liveOption());
    fireEvent.click(
      screen.getByRole("button", { name: "Iniciar ditado" }),
    );
    await waitFor(() => expect(fakeCapture.started).toBe(true));
    expect(liveOption().disabled).toBe(true);
    expect(batchOption().disabled).toBe(true);
    fireEvent.click(batchOption());
    // still live: capture controls remain
    expect(
      screen.getByRole("button", { name: "Finalizar ditado" }),
    ).toBeTruthy();
  });

  it("DM-11: switching is blocked during batch recording", async () => {
    render(<Harness transport={makeTransport()} />);
    fireEvent.click(
      screen.getByRole("button", { name: "Ditar mensagem" }),
    );
    await waitFor(() => screen.getByText("Gravando"));
    expect(liveOption().disabled).toBe(true);
    expect(batchOption().disabled).toBe(true);
  });

  it("DM-12b: switching after a finished live session keeps confirmed text", async () => {
    const transport = makeTransport();
    render(<Harness transport={transport} initial="base " />);
    fireEvent.click(liveOption());
    fireEvent.click(
      screen.getByRole("button", { name: "Iniciar ditado" }),
    );
    await waitFor(() => expect(fakeCapture.emit).toBeTruthy());
    textarea().setSelectionRange(5, 5);
    act(() => fakeCapture.emit?.(new Blob(["w"]), 2000));
    fireEvent.click(
      screen.getByRole("button", { name: "Finalizar ditado" }),
    );
    await waitFor(() =>
      expect(
        screen.getByText("Texto transcrito. Revise antes de enviar."),
      ).toBeTruthy(),
    );
    expect(textarea().value).toBe("base trecho");
    // review concluded → the selector unlocks, then switching is allowed
    await waitFor(() => expect(batchOption().disabled).toBe(false));
    fireEvent.click(batchOption());
    expect(textarea().value).toBe("base trecho");
    expect(
      screen.getByRole("button", { name: "Ditar mensagem" }),
    ).toBeTruthy();
  });

  it("DM-13: caret/selection restored across the mode switch", () => {
    render(<Harness transport={makeTransport()} initial="abcdef" />);
    const el = textarea();
    el.focus();
    el.setSelectionRange(2, 4);
    fireEvent(el, new Event("selectionchange"));
    document.dispatchEvent(new Event("selectionchange"));
    fireEvent.click(liveOption());
    const el2 = document.getElementById(
      "delia-dual-input",
    ) as HTMLTextAreaElement;
    expect(el2.selectionStart).toBe(2);
    expect(el2.selectionEnd).toBe(4);
  });

  it("DM-14: batch transcription merges into the draft (v1 path)", async () => {
    render(<Harness transport={makeTransport()} />);
    fireEvent.click(
      screen.getByRole("button", { name: "Ditar mensagem" }),
    );
    await waitFor(() => screen.getByText("Gravando"));
    fireEvent.click(
      screen.getByRole("button", { name: "Finalizar gravação" }),
    );
    await waitFor(() =>
      expect(textarea().value).toBe("transcrito"),
    );
  });

  it("batch selected while live unavailable shows batch path, not live", () => {
    // batch unavailable + live available edge: no auto-selection
    render(<Harness transport={makeTransport()} withTranscriber={false} />);
    expect(batchOption().getAttribute("aria-pressed")).toBe("true");
    expect(
      screen.queryByRole("button", { name: "Iniciar ditado" }),
    ).toBeNull();
    fireEvent.click(liveOption());
    expect(
      screen.getByRole("button", { name: "Iniciar ditado" }),
    ).toBeTruthy();
  });
});
