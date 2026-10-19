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
import type { DeliaDictationTranscriber } from "./DeliaComposer";

afterEach(cleanup);

describe("DeliaComposer — audio capture gate", () => {
  it("does not expose mic when audioCaptureEnabled is false (default)", () => {
    render(
      <DeliaComposer
        inputId="delia-input"
        value=""
        onChange={() => undefined}
        onSubmit={() => undefined}
      />,
    );
    expect(screen.queryByRole("button", { name: "Gravar áudio" })).toBeNull();
    expect(
      screen.queryByRole("button", { name: "Gravação de áudio indisponível" }),
    ).toBeNull();
    expect(screen.getByLabelText("Pergunte à DÉLIA")).toBeTruthy();
  });

  it("shows unavailable mic when enabled without approved limits", () => {
    render(
      <DeliaComposer
        inputId="delia-input"
        value="draft"
        onChange={vi.fn()}
        onSubmit={vi.fn()}
        audioCaptureEnabled
      />,
    );
    expect(
      (
        screen.getByRole("button", {
          name: "Gravação de áudio indisponível",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
    expect(screen.getByLabelText("Pergunte à DÉLIA")).toHaveProperty(
      "value",
      "draft",
    );
  });

  it("shows mic trigger when enabled with explicit QA fixture limits", () => {
    Object.defineProperty(window, "isSecureContext", {
      configurable: true,
      get: () => true,
    });
    Object.defineProperty(navigator, "mediaDevices", {
      configurable: true,
      value: { getUserMedia: vi.fn() },
    });
    (
      globalThis as unknown as {
        MediaRecorder: {
          isTypeSupported: (m: string) => boolean;
        };
      }
    ).MediaRecorder = {
      isTypeSupported: (m: string) => m.includes("webm"),
    };

    render(
      <DeliaComposer
        inputId="delia-input"
        value=""
        onChange={() => undefined}
        onSubmit={() => undefined}
        audioCaptureEnabled
        audioCaptureMaxDurationMs={60_000}
        audioCaptureMaxBytes={256_000}
      />,
    );
    expect(screen.getByRole("button", { name: "Gravar áudio" })).toBeTruthy();
  });
});

/* ---------- Voice Dictation modal surface swap (VD-F02) ---------- */

type FakeTrack = { stop: ReturnType<typeof vi.fn>; kind: string };

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
    FakeMediaRecorder.instances.push(this);
  }

  static instances: FakeMediaRecorder[] = [];

  start() {
    this.state = "recording";
  }

  stop() {
    this.state = "inactive";
    this.ondataavailable?.({
      data: new Blob([new Uint8Array([1, 2, 3, 4])], { type: this.mimeType }),
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

function renderDictation(value = "") {
  const onSubmit = vi.fn();
  const onChange = vi.fn();
  const view = render(
    <DeliaComposer
      inputId="delia-input"
      value={value}
      onChange={onChange}
      onSubmit={onSubmit}
      audioCaptureEnabled
      audioCaptureMaxDurationMs={60_000}
      audioCaptureMaxBytes={256_000}
    />,
  );
  return { ...view, onSubmit, onChange };
}

describe("DeliaComposer — voice dictation surface swap", () => {
  beforeEach(() => {
    FakeMediaRecorder.instances = [];
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
      Object.defineProperty(window, "isSecureContext", originalIsSecureContext);
    }
  });

  it("recording replaces the write area: no textarea, no send, single surface", async () => {
    const { container } = renderDictation("rascunho do usuário");
    fireEvent.click(screen.getByRole("button", { name: "Gravar áudio" }));

    await waitFor(() => screen.getByText("Gravando"));

    expect(
      container.querySelectorAll(".delpi-ui-message-composer__surface"),
    ).toHaveLength(1);
    expect(screen.queryByLabelText("Pergunte à DÉLIA")).toBeNull();
    expect(screen.queryByRole("button", { name: "Enviar" })).toBeNull();
    expect(
      screen.getByRole("region", { name: "Gravação de áudio em andamento" }),
    ).toBeTruthy();
    expect(screen.getByRole("button", { name: "Cancelar gravação" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Finalizar gravação" })).toBeTruthy();
    expect(container.querySelectorAll("textarea")).toHaveLength(0);
  });

  it("cancel restores writing mode with the exact prior draft", async () => {
    const { container } = renderDictation("texto antes do ditado");
    fireEvent.click(screen.getByRole("button", { name: "Gravar áudio" }));
    await waitFor(() => screen.getByText("Gravando"));

    fireEvent.click(screen.getByRole("button", { name: "Cancelar gravação" }));

    await waitFor(() => screen.getByLabelText("Pergunte à DÉLIA"));
    expect(
      (screen.getByLabelText("Pergunte à DÉLIA") as HTMLTextAreaElement).value,
    ).toBe("texto antes do ditado");
    expect(screen.getByRole("button", { name: "Gravar áudio" })).toBeTruthy();
    void container;
  });

  it("finishing stays modal in preview: still no textarea, no submit", async () => {
    const { onSubmit } = renderDictation();
    fireEvent.click(screen.getByRole("button", { name: "Gravar áudio" }));
    await waitFor(() => screen.getByRole("button", { name: "Finalizar gravação" }));
    fireEvent.click(screen.getByRole("button", { name: "Finalizar gravação" }));

    await waitFor(() =>
      screen.getByRole("region", { name: "Prévia do áudio gravado" }),
    );
    expect(screen.queryByLabelText("Pergunte à DÉLIA")).toBeNull();
    expect(screen.queryByRole("button", { name: "Enviar" })).toBeNull();
    expect(onSubmit).not.toHaveBeenCalled();
    // Local-only: no audio send control, no fake transcription state.
    expect(screen.queryByRole("button", { name: "Enviar áudio" })).toBeNull();
    expect(screen.queryByText(/[Tt]ranscrev/)).toBeNull();
  });

  it("discarding preview restores writing mode with the prior draft", async () => {
    renderDictation("draft preservado");
    fireEvent.click(screen.getByRole("button", { name: "Gravar áudio" }));
    await waitFor(() => screen.getByRole("button", { name: "Finalizar gravação" }));
    fireEvent.click(screen.getByRole("button", { name: "Finalizar gravação" }));
    await waitFor(() => screen.getByRole("button", { name: "Descartar áudio" }));

    fireEvent.click(screen.getByRole("button", { name: "Descartar áudio" }));

    await waitFor(() => screen.getByLabelText("Pergunte à DÉLIA"));
    expect(
      (screen.getByLabelText("Pergunte à DÉLIA") as HTMLTextAreaElement).value,
    ).toBe("draft preservado");
  });

  it("permission denial keeps writing mode with honest error and preserved draft", async () => {
    (
      navigator.mediaDevices.getUserMedia as ReturnType<typeof vi.fn>
    ).mockRejectedValueOnce(
      Object.assign(new Error("denied"), { name: "NotAllowedError" }),
    );
    renderDictation("não perder isso");
    fireEvent.click(screen.getByRole("button", { name: "Gravar áudio" }));

    await waitFor(() => screen.getByRole("alert"));
    expect(screen.getByRole("alert").textContent).toMatch(/negada/i);
    expect(
      (screen.getByLabelText("Pergunte à DÉLIA") as HTMLTextAreaElement).value,
    ).toBe("não perder isso");
    expect(screen.getByRole("button", { name: "Gravar áudio" })).toBeTruthy();
  });

  it("Enter inside the capture region never submits text", async () => {
    const { onSubmit } = renderDictation("não enviar");
    fireEvent.click(screen.getByRole("button", { name: "Gravar áudio" }));
    await waitFor(() => screen.getByText("Gravando"));

    fireEvent.keyDown(screen.getByRole("region", {
      name: "Gravação de áudio em andamento",
    }), { key: "Enter" });
    fireEvent.keyDown(document.activeElement ?? document.body, { key: "Enter" });

    expect(onSubmit).not.toHaveBeenCalled();
  });
});

/* ---------- Voice Dictation STT integration (VD-F03) ---------- */

function StatefulComposer({
  initial,
  transcriber,
  onSubmit,
}: {
  initial: string;
  transcriber: DeliaDictationTranscriber | null;
  onSubmit: () => void;
}) {
  const [value, setValue] = useState(initial);
  return (
    <DeliaComposer
      inputId="delia-input"
      value={value}
      onChange={setValue}
      onSubmit={onSubmit}
      audioCaptureEnabled
      audioCaptureMaxDurationMs={60_000}
      audioCaptureMaxBytes={256_000}
      dictationTranscriber={transcriber}
    />
  );
}

function resolvedTranscriber(
  text: string,
  delayMs = 0,
): DeliaDictationTranscriber {
  return (_draft, _signal) =>
    new Promise((resolve) =>
      setTimeout(
        () =>
          resolve({ transcriptionId: "tr-1", text, language: "pt-BR" }),
        delayMs,
      ),
    );
}

describe("DeliaComposer — voice dictation STT (VD-F03)", () => {
  beforeEach(() => {
    FakeMediaRecorder.instances = [];
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
      Object.defineProperty(window, "isSecureContext", originalIsSecureContext);
    }
  });

  it("finish → real transcribing → editable transcript, never auto-submit", async () => {
    const onSubmit = vi.fn();
    render(
      <StatefulComposer
        initial=""
        transcriber={resolvedTranscriber(
          "Mostre os indicadores de produção desta semana.",
          30,
        )}
        onSubmit={onSubmit}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Gravar áudio" }));
    await waitFor(() => screen.getByRole("button", { name: "Finalizar gravação" }));
    fireEvent.click(screen.getByRole("button", { name: "Finalizar gravação" }));

    // Real transcribing state — no textarea, no send, no fake progress.
    await waitFor(() => screen.getByText("Transcrevendo sua fala…"));
    expect(screen.queryByLabelText("Pergunte à DÉLIA")).toBeNull();
    expect(screen.queryByRole("button", { name: "Enviar" })).toBeNull();
    expect(
      screen.getByRole("button", { name: "Cancelar transcrição" }),
    ).toBeTruthy();

    // Transcript lands editable in the composer — no submit fired.
    await waitFor(() => screen.getByLabelText("Pergunte à DÉLIA"));
    expect(
      (screen.getByLabelText("Pergunte à DÉLIA") as HTMLTextAreaElement).value,
    ).toBe("Mostre os indicadores de produção desta semana.");
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("merges transcript at the recorded caret, preserving the rest", async () => {
    const onSubmit = vi.fn();
    render(
      <StatefulComposer
        initial="olá mundo"
        transcriber={resolvedTranscriber("DÉLIA", 30)}
        onSubmit={onSubmit}
      />,
    );
    const textarea = screen.getByLabelText(
      "Pergunte à DÉLIA",
    ) as HTMLTextAreaElement;
    textarea.focus();
    textarea.setSelectionRange(4, 4); // caret after "olá "
    fireEvent(document, new Event("selectionchange"));

    fireEvent.click(screen.getByRole("button", { name: "Gravar áudio" }));
    await waitFor(() => screen.getByRole("button", { name: "Finalizar gravação" }));
    fireEvent.click(screen.getByRole("button", { name: "Finalizar gravação" }));

    await waitFor(() => screen.getByLabelText("Pergunte à DÉLIA"));
    expect(
      (screen.getByLabelText("Pergunte à DÉLIA") as HTMLTextAreaElement).value,
    ).toBe("olá DÉLIAmundo");
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("cancel during transcribing aborts and preserves the prior draft", async () => {
    const onSubmit = vi.fn();
    let resolveFn: ((r: { transcriptionId: string; text: string; language: string }) => void) | null = null;
    const transcriber: DeliaDictationTranscriber = (_d, _s) =>
      new Promise((resolve) => {
        resolveFn = resolve;
      });
    render(
      <StatefulComposer
        initial="draft antes"
        transcriber={transcriber}
        onSubmit={onSubmit}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Gravar áudio" }));
    await waitFor(() => screen.getByRole("button", { name: "Finalizar gravação" }));
    fireEvent.click(screen.getByRole("button", { name: "Finalizar gravação" }));
    await waitFor(() => screen.getByText("Transcrevendo sua fala…"));

    fireEvent.click(screen.getByRole("button", { name: "Cancelar transcrição" }));
    await waitFor(() => screen.getByLabelText("Pergunte à DÉLIA"));

    // Late response after local cancel is discarded, never applied.
    resolveFn?.({ transcriptionId: "t", text: "texto tardio", language: "pt-BR" });
    await waitFor(() =>
      expect(
        (screen.getByLabelText("Pergunte à DÉLIA") as HTMLTextAreaElement)
          .value,
      ).toBe("draft antes"),
    );
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("STT failure returns to writing with honest error and preserved draft", async () => {
    const onSubmit = vi.fn();
    const failing: DeliaDictationTranscriber = () =>
      Promise.reject(
        Object.assign(new Error("unavailable"), {
          code: "provider_unavailable",
        }),
      );
    render(
      <StatefulComposer
        initial="texto preservado"
        transcriber={failing}
        onSubmit={onSubmit}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Gravar áudio" }));
    await waitFor(() => screen.getByRole("button", { name: "Finalizar gravação" }));
    fireEvent.click(screen.getByRole("button", { name: "Finalizar gravação" }));

    await waitFor(() => screen.getByRole("alert"));
    expect(screen.getByRole("alert").textContent).toMatch(/indisponível/i);
    expect(
      (screen.getByLabelText("Pergunte à DÉLIA") as HTMLTextAreaElement).value,
    ).toBe("texto preservado");
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("without a transcriber, finishing stays in honest local preview", async () => {
    render(
      <StatefulComposer initial="" transcriber={null} onSubmit={vi.fn()} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Gravar áudio" }));
    await waitFor(() => screen.getByRole("button", { name: "Finalizar gravação" }));
    fireEvent.click(screen.getByRole("button", { name: "Finalizar gravação" }));

    await waitFor(() =>
      screen.getByRole("region", { name: "Prévia do áudio gravado" }),
    );
    expect(screen.queryByText(/[Tt]ranscrev/)).toBeNull();
  });
});
