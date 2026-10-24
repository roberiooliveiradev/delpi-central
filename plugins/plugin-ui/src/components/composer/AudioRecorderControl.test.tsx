import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { MessageComposer } from "./MessageComposer";
import { AudioRecorderControl } from "./AudioRecorderControl";
import { formatAudioDurationMs } from "./audioRecorderTypes";
import {
  isLocalAudioCaptureSupported,
  pickSupportedAudioRecorderMime,
} from "./audioRecorderMime";

const QA_MAX_DURATION_MS = 60_000;
const QA_MAX_BYTES = 256_000;

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
  private stream: MediaStream;

  constructor(stream: MediaStream, options?: { mimeType?: string }) {
    this.stream = stream;
    this.mimeType = options?.mimeType || "audio/webm";
    FakeMediaRecorder.instances.push(this);
  }

  static instances: FakeMediaRecorder[] = [];

  start(_timeslice?: number) {
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

beforeEach(() => {
  FakeMediaRecorder.instances = [];
  FakeMediaRecorder.isTypeSupported = vi.fn((mime: string) =>
    mime.includes("webm"),
  );
  Object.defineProperty(window, "isSecureContext", {
    configurable: true,
    get: () => true,
  });
  Object.defineProperty(navigator, "mediaDevices", {
    configurable: true,
    value: {
      getUserMedia: vi.fn(async () => createFakeStream()),
    },
  });
  (
    globalThis as unknown as { MediaRecorder: typeof FakeMediaRecorder }
  ).MediaRecorder = FakeMediaRecorder;
  vi.stubGlobal(
    "Audio",
    class {
      paused = true;
      duration = 2;
      currentTime = 0;
      onended: (() => void) | null = null;
      ontimeupdate: (() => void) | null = null;
      play = vi.fn(async () => {
        this.paused = false;
        this.currentTime = 1;
        this.ontimeupdate?.();
      });
      pause = vi.fn(() => {
        this.paused = true;
      });
      load = vi.fn();
      removeAttribute = vi.fn();
    },
  );
  URL.createObjectURL = vi.fn(() => "blob:test-audio");
  URL.revokeObjectURL = vi.fn();
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
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
  } else {
    delete (globalThis as { MediaRecorder?: unknown }).MediaRecorder;
  }
  if (originalIsSecureContext) {
    Object.defineProperty(window, "isSecureContext", originalIsSecureContext);
  }
});

function renderGated(
  overrides: Partial<Parameters<typeof AudioRecorderControl>[0]> = {},
) {
  return render(
    <AudioRecorderControl
      enabled
      maxDurationMs={QA_MAX_DURATION_MS}
      maxBytes={QA_MAX_BYTES}
      canSendAudio={false}
      {...overrides}
    >
      {({ trigger, panel, blocking }) => (
        <div>
          {panel}
          <MessageComposer
            value="rascunho preservado"
            onChange={() => undefined}
            onSubmit={() => undefined}
            inputLabel="Mensagem"
            secondaryActions={trigger ?? undefined}
            submitDisabled={blocking}
          />
        </div>
      )}
    </AudioRecorderControl>,
  );
}

describe("formatAudioDurationMs", () => {
  it("formats mm:ss", () => {
    expect(formatAudioDurationMs(0)).toBe("00:00");
    expect(formatAudioDurationMs(65_000)).toBe("01:05");
  });
});

describe("audio capture support helpers", () => {
  it("picks a supported mime", () => {
    expect(pickSupportedAudioRecorderMime()).toBe("audio/webm;codecs=opus");
  });

  it("reports unsupported when MediaRecorder missing", () => {
    delete (globalThis as { MediaRecorder?: unknown }).MediaRecorder;
    expect(isLocalAudioCaptureSupported()).toBe(false);
  });
});

describe("AudioRecorderControl — feature gate", () => {
  it("renders nothing when enabled is false", () => {
    renderGated({ enabled: false });
    expect(screen.queryByRole("button", { name: "Gravar áudio" })).toBeNull();
    expect(
      screen.queryByRole("button", { name: "Gravação de áudio indisponível" }),
    ).toBeNull();
  });

  it("stays unavailable without approved limits even when enabled", () => {
    render(
      <AudioRecorderControl enabled canSendAudio={false}>
        {({ trigger }) => <div>{trigger}</div>}
      </AudioRecorderControl>,
    );
    expect(
      (
        screen.getByRole("button", {
          name: "Gravação de áudio indisponível",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
  });

  it("shows mic trigger when enabled with QA limits", () => {
    renderGated();
    expect(screen.getByRole("button", { name: "Gravar áudio" })).toBeTruthy();
  });
});

describe("AudioRecorderControl — permission and capture", () => {
  it("requests mic only after explicit click and records", async () => {
    const getUserMedia = navigator.mediaDevices.getUserMedia as ReturnType<
      typeof vi.fn
    >;
    renderGated();
    expect(getUserMedia).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Gravar áudio" }));

    await waitFor(() => {
      expect(getUserMedia).toHaveBeenCalledTimes(1);
      expect(
        screen.getByRole("region", { name: "Gravação de áudio em andamento" }),
      ).toBeTruthy();
    });
    expect(screen.getByText("Gravando")).toBeTruthy();
    expect(FakeMediaRecorder.instances).toHaveLength(1);
    expect(FakeMediaRecorder.instances[0]?.state).toBe("recording");
  });

  it("maps permission denied to an alert", async () => {
    (
      navigator.mediaDevices.getUserMedia as ReturnType<typeof vi.fn>
    ).mockRejectedValueOnce(
      Object.assign(new Error("denied"), { name: "NotAllowedError" }),
    );
    const onCaptureError = vi.fn();
    renderGated({ onCaptureError });

    fireEvent.click(screen.getByRole("button", { name: "Gravar áudio" }));

    await waitFor(() => {
      expect(screen.getByRole("alert").textContent).toMatch(/negada/i);
    });
    expect(onCaptureError).toHaveBeenCalledWith("permission_denied");
  });

  it("maps missing device", async () => {
    (
      navigator.mediaDevices.getUserMedia as ReturnType<typeof vi.fn>
    ).mockRejectedValueOnce(
      Object.assign(new Error("missing"), { name: "NotFoundError" }),
    );
    renderGated();
    fireEvent.click(screen.getByRole("button", { name: "Gravar áudio" }));
    await waitFor(() => {
      expect(screen.getByRole("alert").textContent).toMatch(/microfone/i);
    });
  });

  it("finalizes into preview without send control when canSendAudio is false", async () => {
    const onDraftReady = vi.fn();
    renderGated({ onDraftReady });
    fireEvent.click(screen.getByRole("button", { name: "Gravar áudio" }));
    await waitFor(() => screen.getByRole("button", { name: "Finalizar gravação" }));

    fireEvent.click(screen.getByRole("button", { name: "Finalizar gravação" }));

    await waitFor(() => {
      expect(
        screen.getByRole("region", { name: "Prévia do áudio gravado" }),
      ).toBeTruthy();
    });
    expect(onDraftReady).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole("button", { name: "Enviar áudio" })).toBeNull();
    expect(URL.createObjectURL).toHaveBeenCalled();
  });

  it("plays and pauses preview audio", async () => {
    renderGated();
    fireEvent.click(screen.getByRole("button", { name: "Gravar áudio" }));
    await waitFor(() => screen.getByRole("button", { name: "Finalizar gravação" }));
    fireEvent.click(screen.getByRole("button", { name: "Finalizar gravação" }));
    await waitFor(() =>
      screen.getByRole("button", { name: "Reproduzir áudio" }),
    );

    fireEvent.click(screen.getByRole("button", { name: "Reproduzir áudio" }));
    await waitFor(() =>
      screen.getByRole("button", { name: "Pausar áudio" }),
    );
    fireEvent.click(screen.getByRole("button", { name: "Pausar áudio" }));
    expect(screen.getByRole("button", { name: "Reproduzir áudio" })).toBeTruthy();
  });

  it("discards preview and returns to idle trigger", async () => {
    const onDiscard = vi.fn();
    renderGated({ onDiscard });
    fireEvent.click(screen.getByRole("button", { name: "Gravar áudio" }));
    await waitFor(() => screen.getByRole("button", { name: "Finalizar gravação" }));
    fireEvent.click(screen.getByRole("button", { name: "Finalizar gravação" }));
    await waitFor(() => screen.getByRole("button", { name: "Descartar áudio" }));

    fireEvent.click(screen.getByRole("button", { name: "Descartar áudio" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Gravar áudio" })).toBeTruthy();
    });
    expect(onDiscard).toHaveBeenCalled();
    expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:test-audio");
  });

  it("re-records from preview: revokes URL, requests mic again, captures", async () => {
    renderGated();
    fireEvent.click(screen.getByRole("button", { name: "Gravar áudio" }));
    await waitFor(() => screen.getByRole("button", { name: "Finalizar gravação" }));
    fireEvent.click(screen.getByRole("button", { name: "Finalizar gravação" }));
    await waitFor(() =>
      screen.getByRole("button", { name: "Regravar áudio" }),
    );

    fireEvent.click(screen.getByRole("button", { name: "Regravar áudio" }));

    await waitFor(() =>
      screen.getByRole("button", { name: "Finalizar gravação" }),
    );
    expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:test-audio");
    expect(
      (navigator.mediaDevices.getUserMedia as ReturnType<typeof vi.fn>).mock
        .calls.length,
    ).toBe(2);
    expect(FakeMediaRecorder.instances.length).toBe(2);
  });

  it("cancels recording and stops tracks", async () => {
    renderGated();
    fireEvent.click(screen.getByRole("button", { name: "Gravar áudio" }));
    await waitFor(() => screen.getByRole("button", { name: "Cancelar gravação" }));
    const track = (
      FakeMediaRecorder.instances[0] as unknown as { stream: MediaStream }
    ).stream?.getTracks?.()?.[0] as unknown as FakeTrack | undefined;

    // stream is private — grab from getUserMedia result via track stop on cancel
    fireEvent.click(screen.getByRole("button", { name: "Cancelar gravação" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Gravar áudio" })).toBeTruthy();
    });
    // track stop is called via stream from getUserMedia
    const stream = await (
      navigator.mediaDevices.getUserMedia as ReturnType<typeof vi.fn>
    ).mock.results[0]?.value;
    const stopped = stream?.getTracks?.()?.[0]?.stop as ReturnType<typeof vi.fn>;
    expect(stopped).toHaveBeenCalled();
    void track;
  });

  it("blocks text submit while recording and preserves draft value", async () => {
    const onSubmit = vi.fn();
    render(
      <AudioRecorderControl
        enabled
        maxDurationMs={QA_MAX_DURATION_MS}
        maxBytes={QA_MAX_BYTES}
        canSendAudio={false}
      >
        {({ trigger, panel, blocking }) => (
          <div>
            {panel}
            <MessageComposer
              value="rascunho preservado"
              onChange={() => undefined}
              onSubmit={onSubmit}
              inputLabel="Mensagem"
              secondaryActions={trigger ?? undefined}
              submitDisabled={blocking}
            />
          </div>
        )}
      </AudioRecorderControl>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Gravar áudio" }));
    await waitFor(() => screen.getByText("Gravando"));

    fireEvent.keyDown(screen.getByLabelText("Mensagem"), { key: "Enter" });
    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByLabelText("Mensagem")).toHaveProperty(
      "value",
      "rascunho preservado",
    );
    expect(
      (screen.getByRole("button", { name: "Enviar mensagem" }) as HTMLButtonElement)
        .disabled,
    ).toBe(true);
  });

  it("does not auto-submit on finalize", async () => {
    const onSubmit = vi.fn();
    const onConfirmSend = vi.fn();
    render(
      <AudioRecorderControl
        enabled
        maxDurationMs={QA_MAX_DURATION_MS}
        maxBytes={QA_MAX_BYTES}
        canSendAudio={false}
        onConfirmSend={onConfirmSend}
      >
        {({ trigger, panel, blocking }) => (
          <div>
            {panel}
            <MessageComposer
              value="texto"
              onChange={() => undefined}
              onSubmit={onSubmit}
              inputLabel="Mensagem"
              secondaryActions={trigger ?? undefined}
              submitDisabled={blocking}
            />
          </div>
        )}
      </AudioRecorderControl>,
    );
    fireEvent.click(screen.getByRole("button", { name: "Gravar áudio" }));
    await waitFor(() => screen.getByRole("button", { name: "Finalizar gravação" }));
    fireEvent.click(screen.getByRole("button", { name: "Finalizar gravação" }));
    await waitFor(() =>
      screen.getByRole("region", { name: "Prévia do áudio gravado" }),
    );
    expect(onSubmit).not.toHaveBeenCalled();
    expect(onConfirmSend).not.toHaveBeenCalled();
  });

  it("ignores duplicate start while already recording", async () => {
    const getUserMedia = navigator.mediaDevices.getUserMedia as ReturnType<
      typeof vi.fn
    >;
    renderGated();
    fireEvent.click(screen.getByRole("button", { name: "Gravar áudio" }));
    await waitFor(() => screen.getByText("Gravando"));
    expect(getUserMedia).toHaveBeenCalledTimes(1);
    // trigger hidden while recording — no second start path
    expect(screen.queryByRole("button", { name: "Gravar áudio" })).toBeNull();
  });

  it("revokes object URL on unmount", async () => {
    const view = renderGated();
    fireEvent.click(screen.getByRole("button", { name: "Gravar áudio" }));
    await waitFor(() => screen.getByRole("button", { name: "Finalizar gravação" }));
    fireEvent.click(screen.getByRole("button", { name: "Finalizar gravação" }));
    await waitFor(() =>
      screen.getByRole("region", { name: "Prévia do áudio gravado" }),
    );

    act(() => {
      view.unmount();
    });
    expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:test-audio");
  });

  it("reports mime unsupported when no candidate matches", async () => {
    FakeMediaRecorder.isTypeSupported = vi.fn(() => false);
    const onCaptureError = vi.fn();
    // isLocalAudioCaptureSupported becomes false → unavailable trigger
    renderGated({ onCaptureError });
    expect(
      (
        screen.getByRole("button", {
          name: "Gravação de áudio indisponível",
        }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
  });
});

describe("MessageComposer — submitDisabled", () => {
  it("blocks Enter and send without clearing the draft", () => {
    const onSubmit = vi.fn();
    render(
      <MessageComposer
        value="ainda aqui"
        onChange={() => undefined}
        onSubmit={onSubmit}
        inputLabel="Mensagem"
        submitDisabled
      />,
    );
    fireEvent.keyDown(screen.getByLabelText("Mensagem"), { key: "Enter" });
    expect(onSubmit).not.toHaveBeenCalled();
    expect(
      (screen.getByRole("button", { name: "Enviar mensagem" }) as HTMLButtonElement)
        .disabled,
    ).toBe(true);
    expect(screen.getByLabelText("Mensagem")).toHaveProperty("value", "ainda aqui");
  });
});

/* ---------- VD-F05 — five-minute limit UX ---------- */

describe("AudioRecorderControl — duration limit UX (VD-F05)", () => {
  it("shows the admitted limit next to the live timer (mm:ss / mm:ss)", async () => {
    const { container } = renderGated({ maxDurationMs: 300_000 });
    fireEvent.click(screen.getByRole("button", { name: "Gravar áudio" }));
    await waitFor(() => screen.getByText("Gravando"));

    const duration = container.querySelector(
      ".delpi-ui-audio-recorder__duration",
    );
    expect(duration?.textContent).toMatch(/\d{2}:\d{2}\s*\/\s*05:00/);
    expect(
      duration?.getAttribute("aria-label"),
    ).toMatch(/^Duração \d{2}:\d{2} de 05:00$/);
  });

  it("auto-stops exactly once at the duration limit via the normal finish path", async () => {
    vi.useFakeTimers();
    try {
      const onDraftReady = vi.fn();
      renderGated({ maxDurationMs: 300_000, onDraftReady });
      fireEvent.click(screen.getByRole("button", { name: "Gravar áudio" }));
      await act(async () => {
        await vi.advanceTimersByTimeAsync(0);
      });
      await act(async () => {
        await vi.advanceTimersByTimeAsync(0);
      });
      expect(FakeMediaRecorder.instances[0]?.state).toBe("recording");

      // Jump past the limit; the interval tick stops the recorder once.
      await act(async () => {
        vi.setSystemTime(Date.now() + 300_500);
        await vi.advanceTimersByTimeAsync(250);
      });

      expect(FakeMediaRecorder.instances[0]?.state).toBe("inactive");
      expect(onDraftReady).toHaveBeenCalledTimes(1);
      const draft = onDraftReady.mock.calls[0]?.[0] as {
        durationMs: number;
        sizeBytes: number;
      };
      // The interval overshoot is clamped — the contract bound is never
      // reported as exceeded.
      expect(draft.durationMs).toBe(300_000);
      expect(draft.sizeBytes).toBeGreaterThan(0);

      // Further ticks must never finalize a second time.
      await act(async () => {
        await vi.advanceTimersByTimeAsync(2_000);
      });
      expect(onDraftReady).toHaveBeenCalledTimes(1);

      // Preview + informational note (status), never a danger alert.
      expect(
        screen.getByRole("region", { name: "Prévia do áudio gravado" }),
      ).toBeTruthy();
      const note = screen.getByText("A gravação atingiu o tempo máximo permitido.");
      expect(note.closest('[role="status"]')).not.toBeNull();
      expect(screen.queryByRole("alert")).toBeNull();
    } finally {
      vi.useRealTimers();
    }
  });

  it("shows the discreet notice only in the last 30 seconds before the limit", async () => {
    vi.useFakeTimers();
    try {
      renderGated({ maxDurationMs: 300_000 });
      fireEvent.click(screen.getByRole("button", { name: "Gravar áudio" }));
      await act(async () => {
        await vi.advanceTimersByTimeAsync(0);
      });
      await act(async () => {
        await vi.advanceTimersByTimeAsync(0);
      });
      expect(FakeMediaRecorder.instances[0]?.state).toBe("recording");

      // 04:29 — still no notice.
      await act(async () => {
        vi.setSystemTime(Date.now() + 269_000);
        await vi.advanceTimersByTimeAsync(250);
      });
      expect(
        screen.queryByText("A gravação será finalizada em breve."),
      ).toBeNull();

      // 04:31 — discreet notice appears once (role=status, no modal).
      await act(async () => {
        vi.setSystemTime(Date.now() + 2_000);
        await vi.advanceTimersByTimeAsync(250);
      });
      const note = screen.getByText("A gravação será finalizada em breve.");
      expect(note.closest('[role="status"]')).not.toBeNull();
    } finally {
      vi.useRealTimers();
    }
  });

  it("stops safely with an honest error when captured bytes exceed the limit", async () => {
    renderGated({ maxBytes: 8 });
    fireEvent.click(screen.getByRole("button", { name: "Gravar áudio" }));
    await waitFor(() => screen.getByText("Gravando"));

    act(() => {
      FakeMediaRecorder.instances[0]?.ondataavailable?.({
        data: new Blob([new Uint8Array(16)], { type: "audio/webm" }),
      });
    });

    await waitFor(() => screen.getByRole("alert"));
    expect(screen.getByRole("alert").textContent).toMatch(
      /tamanho máximo permitido/,
    );
    // No usable draft is delivered; the text draft is untouched.
    expect(FakeMediaRecorder.instances[0]?.state).toBe("inactive");
    expect(screen.getByLabelText("Mensagem")).toHaveProperty(
      "value",
      "rascunho preservado",
    );
  });
});
