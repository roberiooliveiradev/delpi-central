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
    expect(screen.queryByRole("button", { name: "Ditar mensagem" })).toBeNull();
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
    expect(screen.getByRole("button", { name: "Ditar mensagem" })).toBeTruthy();
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
    fireEvent.click(screen.getByRole("button", { name: "Ditar mensagem" }));

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
    fireEvent.click(screen.getByRole("button", { name: "Ditar mensagem" }));
    await waitFor(() => screen.getByText("Gravando"));

    fireEvent.click(screen.getByRole("button", { name: "Cancelar gravação" }));

    await waitFor(() => screen.getByLabelText("Pergunte à DÉLIA"));
    expect(
      (screen.getByLabelText("Pergunte à DÉLIA") as HTMLTextAreaElement).value,
    ).toBe("texto antes do ditado");
    expect(screen.getByRole("button", { name: "Ditar mensagem" })).toBeTruthy();
    void container;
  });

  it("finishing stays modal in preview: still no textarea, no submit", async () => {
    const { onSubmit } = renderDictation();
    fireEvent.click(screen.getByRole("button", { name: "Ditar mensagem" }));
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
    fireEvent.click(screen.getByRole("button", { name: "Ditar mensagem" }));
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
    fireEvent.click(screen.getByRole("button", { name: "Ditar mensagem" }));

    await waitFor(() => screen.getByRole("alert"));
    expect(screen.getByRole("alert").textContent).toMatch(/negada/i);
    expect(
      (screen.getByLabelText("Pergunte à DÉLIA") as HTMLTextAreaElement).value,
    ).toBe("não perder isso");
    expect(screen.getByRole("button", { name: "Ditar mensagem" })).toBeTruthy();
  });

  it("Enter inside the capture region never submits text", async () => {
    const { onSubmit } = renderDictation("não enviar");
    fireEvent.click(screen.getByRole("button", { name: "Ditar mensagem" }));
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
  maxDurationMs = 60_000,
  maxBytes = 256_000,
}: {
  initial: string;
  transcriber: DeliaDictationTranscriber | null;
  onSubmit: () => void;
  maxDurationMs?: number;
  maxBytes?: number;
}) {
  const [value, setValue] = useState(initial);
  return (
    <DeliaComposer
      inputId="delia-input"
      value={value}
      onChange={setValue}
      onSubmit={onSubmit}
      audioCaptureEnabled
      audioCaptureMaxDurationMs={maxDurationMs}
      audioCaptureMaxBytes={maxBytes}
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
    fireEvent.click(screen.getByRole("button", { name: "Ditar mensagem" }));
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

    fireEvent.click(screen.getByRole("button", { name: "Ditar mensagem" }));
    await waitFor(() => screen.getByRole("button", { name: "Finalizar gravação" }));
    fireEvent.click(screen.getByRole("button", { name: "Finalizar gravação" }));

    await waitFor(() => screen.getByLabelText("Pergunte à DÉLIA"));
    expect(
      (screen.getByLabelText("Pergunte à DÉLIA") as HTMLTextAreaElement).value,
    ).toBe("olá DÉLIA mundo");
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("cancel during transcribing aborts and preserves the prior draft", async () => {
    const onSubmit = vi.fn();
    let resolveFn: ((r: { transcriptionId: string; text: string; language: string }) => void) | undefined;
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
    fireEvent.click(screen.getByRole("button", { name: "Ditar mensagem" }));
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
    fireEvent.click(screen.getByRole("button", { name: "Ditar mensagem" }));
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
    fireEvent.click(screen.getByRole("button", { name: "Ditar mensagem" }));
    await waitFor(() => screen.getByRole("button", { name: "Finalizar gravação" }));
    fireEvent.click(screen.getByRole("button", { name: "Finalizar gravação" }));

    await waitFor(() =>
      screen.getByRole("region", { name: "Prévia do áudio gravado" }),
    );
    expect(screen.queryByText(/[Tt]ranscrev/)).toBeNull();
  });
});

/* ---------- VD-F04 — visual refinement, help, disclosure ---------- */

describe("DeliaComposer — voice dictation visual refinement (VD-F04)", () => {
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

  it("mic trigger shows the shared HelpTooltip on hover and keyboard focus", async () => {
    render(
      <StatefulComposer
        initial=""
        transcriber={resolvedTranscriber("ok")}
        onSubmit={vi.fn()}
      />,
    );
    const mic = screen.getByRole("button", { name: "Ditar mensagem" });

    fireEvent.mouseEnter(mic);
    await waitFor(() =>
      expect(
        screen.getByText(/Gravar e transcrever: fale/),
      ).toBeTruthy(),
    );
    fireEvent.mouseLeave(mic);

    fireEvent.focus(mic);
    await waitFor(() =>
      expect(
        screen.getByText(/Gravar e transcrever: fale/),
      ).toBeTruthy(),
    );
  });

  it("recording surface is a single surface with disclosure and cancel/finish help", async () => {
    const { container } = render(
      <StatefulComposer
        initial=""
        transcriber={resolvedTranscriber("ok")}
        onSubmit={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Ditar mensagem" }));
    await waitFor(() => screen.getByText("Gravando"));

    expect(
      container.querySelectorAll(".delpi-ui-message-composer__surface"),
    ).toHaveLength(1);
    // Contextual STT transparency inside the capture surface — the
    // global yellow header banner is gone.
    expect(
      screen.getByText(/enviada apenas para transcrição em texto/),
    ).toBeTruthy();

    const finish = screen.getByRole("button", { name: "Finalizar gravação" });
    fireEvent.mouseEnter(finish);
    await waitFor(() =>
      expect(
        screen.getByText(/transcrever sua fala para texto/),
      ).toBeTruthy(),
    );

    const cancel = screen.getByRole("button", { name: "Cancelar gravação" });
    fireEvent.mouseEnter(cancel);
    await waitFor(() =>
      expect(
        screen.getByText(/Descartar esta gravação/),
      ).toBeTruthy(),
    );
  });

  it("transcribing uses a single surface with an activity indicator and cancel help", async () => {
    render(
      <StatefulComposer
        initial=""
        transcriber={(_d, _s) => new Promise(() => undefined)}
        onSubmit={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Ditar mensagem" }));
    await waitFor(() => screen.getByRole("button", { name: "Finalizar gravação" }));
    fireEvent.click(screen.getByRole("button", { name: "Finalizar gravação" }));

    await waitFor(() => screen.getByText("Transcrevendo sua fala…"));
    expect(document.querySelector(".delpi-ui-audio-recorder__activity")).toBeTruthy();
    expect(screen.queryByText(/enviada apenas para transcrição/)).toBeNull();

    const cancel = screen.getByRole("button", { name: "Cancelar transcrição" });
    fireEvent.mouseEnter(cancel);
    await waitFor(() =>
      expect(
        screen.getByText(/processamento remoto pode continuar/),
      ).toBeTruthy(),
    );
  });

  it("successful transcription announces a discreet review notice once", async () => {
    render(
      <StatefulComposer
        initial=""
        transcriber={resolvedTranscriber("texto ditado", 10)}
        onSubmit={vi.fn()}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Ditar mensagem" }));
    await waitFor(() => screen.getByRole("button", { name: "Finalizar gravação" }));
    fireEvent.click(screen.getByRole("button", { name: "Finalizar gravação" }));

    await waitFor(() =>
      screen.getByText("Texto transcrito. Revise antes de enviar."),
    );
    const textarea = screen.getByLabelText(
      "Pergunte à DÉLIA",
    ) as HTMLTextAreaElement;
    expect(textarea.value).toBe("texto ditado");

    // Editing clears the notice — feedback is transient, not permanent.
    fireEvent.change(textarea, { target: { value: "texto ditado editado" } });
    await waitFor(() =>
      expect(
        screen.queryByText("Texto transcrito. Revise antes de enviar."),
      ).toBeNull(),
    );
  });

  it("clear-draft button keeps its own meaning, not cancel-capture", async () => {
    render(
      <StatefulComposer
        initial="rascunho"
        transcriber={resolvedTranscriber("ok")}
        onSubmit={vi.fn()}
      />,
    );
    const clear = screen.getByRole("button", { name: "Limpar texto" });
    fireEvent.mouseEnter(clear);
    await waitFor(() =>
      expect(screen.getByText("Limpar o texto do campo.")).toBeTruthy(),
    );
  });

  it("local-only capture discloses that audio stays in the browser", async () => {
    render(
      <StatefulComposer initial="" transcriber={null} onSubmit={vi.fn()} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Ditar mensagem" }));
    await waitFor(() => screen.getByText("Gravando"));
    expect(
      screen.getByText(/o áudio fica neste navegador/),
    ).toBeTruthy();
    expect(screen.queryByText(/enviada apenas para transcrição/)).toBeNull();
  });
});

/* ---------- VD-F05 — 5-minute dictation + draft continuity ---------- */

describe("DeliaComposer — five-minute dictation continuity (VD-F05)", () => {
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

  async function dictateOnce(finishLabel = "Finalizar gravação") {
    fireEvent.click(screen.getByRole("button", { name: "Ditar mensagem" }));
    await waitFor(() => screen.getByRole("button", { name: finishLabel }));
    fireEvent.click(screen.getByRole("button", { name: finishLabel }));
    await waitFor(() => screen.getByLabelText("Pergunte à DÉLIA"));
  }

  it("accumulates a second dictation into the same draft without glued words", async () => {
    const onSubmit = vi.fn();
    const segments = [
      "Quero analisar os indicadores de produção desta semana.",
      "Compare os resultados com a semana anterior.",
    ];
    let call = 0;
    const transcriber: DeliaDictationTranscriber = () =>
      Promise.resolve({
        transcriptionId: `tr-${call}`,
        text: segments[call++] ?? "",
        language: "pt-BR",
      });
    render(
      <StatefulComposer
        initial=""
        transcriber={transcriber}
        onSubmit={onSubmit}
        maxDurationMs={300_000}
        maxBytes={4_194_304}
      />,
    );

    await dictateOnce();
    expect(
      (screen.getByLabelText("Pergunte à DÉLIA") as HTMLTextAreaElement).value,
    ).toBe("Quero analisar os indicadores de produção desta semana.");

    await dictateOnce();
    expect(
      (screen.getByLabelText("Pergunte à DÉLIA") as HTMLTextAreaElement).value,
    ).toBe(
      "Quero analisar os indicadores de produção desta semana. Compare os resultados com a semana anterior.",
    );
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("a failed second dictation preserves the first transcript", async () => {
    const onSubmit = vi.fn();
    let call = 0;
    const transcriber: DeliaDictationTranscriber = () =>
      call++ === 0
        ? Promise.resolve({
            transcriptionId: "tr-1",
            text: "Primeiro trecho ditado.",
            language: "pt-BR",
          })
        : Promise.reject(
            Object.assign(new Error("rate"), { code: "rate_limited" }),
          );
    render(
      <StatefulComposer initial="" transcriber={transcriber} onSubmit={onSubmit} />,
    );

    await dictateOnce();
    await dictateOnce();

    await waitFor(() => screen.getByRole("alert"));
    expect(
      (screen.getByLabelText("Pergunte à DÉLIA") as HTMLTextAreaElement).value,
    ).toBe("Primeiro trecho ditado.");
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("manual edits between dictations are kept when the next transcript lands", async () => {
    const onSubmit = vi.fn();
    let call = 0;
    const transcriber: DeliaDictationTranscriber = () =>
      Promise.resolve({
        transcriptionId: `tr-${call}`,
        text: call++ === 0 ? "Parte um." : "Parte dois.",
        language: "pt-BR",
      });
    render(
      <StatefulComposer initial="" transcriber={transcriber} onSubmit={onSubmit} />,
    );

    await dictateOnce();
    const textarea = screen.getByLabelText(
      "Pergunte à DÉLIA",
    ) as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: "Parte um, editada." } });
    textarea.setSelectionRange(
      "Parte um, editada.".length,
      "Parte um, editada.".length,
    );
    // jsdom queues selectionchange asynchronously — flush it while the
    // textarea is still focused so the caret tracker registers.
    document.dispatchEvent(new Event("selectionchange"));

    await dictateOnce();
    expect(
      (screen.getByLabelText("Pergunte à DÉLIA") as HTMLTextAreaElement).value,
    ).toBe("Parte um, editada. Parte dois.");
  });

  it("mic help announces the admitted duration in minutes", async () => {
    render(
      <StatefulComposer
        initial=""
        transcriber={resolvedTranscriber("ok")}
        onSubmit={vi.fn()}
        maxDurationMs={300_000}
      />,
    );
    const mic = screen.getByRole("button", { name: "Ditar mensagem" });
    fireEvent.mouseEnter(mic);
    await waitFor(() =>
      expect(screen.getByText(/fale até 5 minutos/i)).toBeTruthy(),
    );
  });

  it("auto-stop at the admitted limit transcribes once via the normal path", async () => {
    const onSubmit = vi.fn();
    const transcriber = vi.fn(
      (_draft: unknown, _signal: AbortSignal) =>
        Promise.resolve({
          transcriptionId: "tr-auto",
          text: "Trecho finalizado pelo limite.",
          language: "pt-BR",
        }),
    ) as unknown as DeliaDictationTranscriber & ReturnType<typeof vi.fn>;
    render(
      <StatefulComposer
        initial="continuação:"
        transcriber={transcriber}
        onSubmit={onSubmit}
        maxDurationMs={200}
      />,
    );

    fireEvent.click(screen.getByRole("button", { name: "Ditar mensagem" }));
    await waitFor(() => screen.getByText("Gravando"));

    // No click on Finalizar — the admitted limit ends the capture and
    // the transcript lands in the draft (the transcribing state may be
    // too fast to observe; the merge is the asserted postcondition).
    await waitFor(() => screen.getByLabelText("Pergunte à DÉLIA"), {
      timeout: 3_000,
    });

    expect(transcriber).toHaveBeenCalledTimes(1);
    const draft = transcriber.mock.calls[0]?.[0] as { durationMs: number };
    expect(draft.durationMs).toBeGreaterThan(0);
    expect(draft.durationMs).toBeLessThanOrEqual(200);
    expect(
      (screen.getByLabelText("Pergunte à DÉLIA") as HTMLTextAreaElement).value,
    ).toBe("continuação: Trecho finalizado pelo limite.");
    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Ditar mensagem" })).toBeTruthy();
  });

  it("reports truncation honestly when the merge exceeds the character limit", async () => {
    const onSubmit = vi.fn();
    const almostFull = "x".repeat(16_380);
    render(
      <StatefulComposer
        initial={almostFull}
        transcriber={resolvedTranscriber("texto ditado extra", 10)}
        onSubmit={onSubmit}
      />,
    );

    await dictateOnce();
    const textarea = screen.getByLabelText(
      "Pergunte à DÉLIA",
    ) as HTMLTextAreaElement;
    expect(textarea.value.length).toBe(16_384);
    expect(textarea.value.startsWith(almostFull)).toBe(true);
    await waitFor(() => screen.getByRole("alert"));
    expect(screen.getByRole("alert").textContent).toMatch(
      /limite de caracteres/,
    );
    expect(onSubmit).not.toHaveBeenCalled();
  });
});

describe('DeliaComposer — VOX unified voice visuals (spec 126)', () => {
  beforeEach(() => {
    FakeMediaRecorder.instances = [];
    Object.defineProperty(window, 'isSecureContext', {
      configurable: true,
      get: () => true,
    });
    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: { getUserMedia: vi.fn(async () => createFakeStream()) },
    });
    (
      globalThis as unknown as { MediaRecorder: typeof FakeMediaRecorder }
    ).MediaRecorder = FakeMediaRecorder;
    URL.createObjectURL = vi.fn(() => 'blob:test-audio');
    URL.revokeObjectURL = vi.fn();
  });

  afterEach(() => {
    if (originalMediaDevices) {
      Object.defineProperty(navigator, 'mediaDevices', {
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
      Object.defineProperty(window, 'isSecureContext', originalIsSecureContext);
    }
  });

  it('VOX-01: batch mic trigger belongs to the circular voice family', () => {
    renderDictation();
    const mic = screen.getByRole('button', { name: 'Ditar mensagem' });
    expect(
      mic.classList.contains('delpi-ui-audio-recorder__trigger'),
    ).toBe(true);
  });

  it('VOX-03/08: recording shows primary finalize, subdued-danger discard and capture halo', async () => {
    renderDictation();
    fireEvent.click(screen.getByRole('button', { name: 'Ditar mensagem' }));
    await waitFor(() => screen.getByText('Gravando'));

    const finish = screen.getByRole('button', {
      name: 'Finalizar gravação',
    });
    const cancel = screen.getByRole('button', {
      name: 'Cancelar gravação',
    });
    expect(finish.className).toContain('delpi-ui-icon-btn--primary');
    // discard affordance: neutral by default, danger only on hover/focus
    expect(cancel.className).toContain('delpi-ui-icon-btn--danger');
    // capture halo marks the whole composer as the active surface
    expect(
      document.querySelector('.delia-composer--capturing'),
    ).toBeTruthy();
  });
});
