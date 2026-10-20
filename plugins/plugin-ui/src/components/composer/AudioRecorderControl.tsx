import { Check, Mic, MicOff, Pause, Play, RotateCcw, Square, X } from "lucide-react";
import type { ReactNode } from "react";
import { IconButton } from "../actions/IconButton";
import { HelpTooltip } from "../help/HelpTooltip";
import type { AudioRecorderControlProps } from "./audioRecorderTypes";
import { formatAudioDurationMs } from "./audioRecorderTypes";
import { useLocalAudioRecorder } from "./useLocalAudioRecorder";

export function audioRecorderErrorMessage(reason: string | null): string {
  switch (reason) {
    case "permission_denied":
      return "Permissão do microfone negada. Você pode digitar a mensagem.";
    case "device_not_found":
      return "Nenhum microfone foi encontrado neste dispositivo.";
    case "device_not_readable":
      return "Não foi possível acessar o microfone. Verifique se outro app está usando o dispositivo.";
    case "api_unavailable":
    case "mime_unsupported":
      return "Gravação de áudio não é suportada neste navegador.";
    case "secure_context_required":
      return "A captura de áudio exige uma conexão segura (HTTPS).";
    case "limit_duration":
      return "A gravação atingiu o tempo máximo permitido.";
    case "limit_bytes":
      return "A gravação atingiu o tamanho máximo permitido.";
    case "recorder_failed":
      return "Falha ao gravar o áudio. Tente novamente ou digite a mensagem.";
    default:
      return "Não foi possível gravar o áudio. Tente novamente ou digite a mensagem.";
  }
}

function Waveform({ levels, live }: { levels: number[]; live: boolean }) {
  return (
    <div
      className="delpi-ui-audio-recorder__wave"
      aria-hidden="true"
      data-live={live ? "true" : "false"}
    >
      {levels.map((level, index) => (
        <span
          key={index}
          className="delpi-ui-audio-recorder__bar"
          style={{ transform: `scaleY(${Math.max(0.12, level)})` }}
        />
      ))}
    </div>
  );
}

export type AudioRecorderControlRenderProps = {
  /** Mic / status trigger for MessageComposer.secondaryActions */
  trigger: ReactNode;
  /** Full recording/preview panel when capture is active */
  panel: ReactNode | null;
  /** Host should block concurrent text submit while true */
  blocking: boolean;
  status: ReturnType<typeof useLocalAudioRecorder>["status"];
  /** Machine-readable capture error for host-rendered messaging. */
  errorReason: ReturnType<typeof useLocalAudioRecorder>["errorReason"];
  /** Completed local draft while status === "preview" (null otherwise). */
  draft: ReturnType<typeof useLocalAudioRecorder>["draft"];
  /** Discard the local draft/preview and return to idle writing. */
  discard: () => void;
};

/**
 * Local-only audio capture control for chat composers.
 * Does not upload, transcribe, or auto-submit. Requires approved limits.
 */
export function AudioRecorderControl({
  enabled,
  disabled = false,
  busy = false,
  maxDurationMs,
  maxBytes,
  canSendAudio = false,
  helpCopy,
  onDraftReady,
  onDiscard,
  onConfirmSend,
  onCaptureError,
  onBlockingChange,
  className,
  children,
}: AudioRecorderControlProps & {
  children?: (api: AudioRecorderControlRenderProps) => ReactNode;
}) {
  const recorder = useLocalAudioRecorder({
    enabled,
    disabled,
    busy,
    maxDurationMs,
    maxBytes,
    onDraftReady,
    onDiscard,
    onCaptureError,
    onBlockingChange,
  });

  const {
    status,
    errorReason,
    durationMs,
    draft,
    levels,
    isPlaying,
    playbackProgress,
    start,
    cancel,
    stop,
    discard,
    rerecord,
    togglePlayback,
    clearError,
  } = recorder;

  const blocking =
    status === "requesting_permission" ||
    status === "recording" ||
    status === "stopping";

  let trigger: ReactNode = null;
  if (status === "unavailable") {
    if (enabled) {
      trigger = (
        <HelpTooltip
          wrap
          content={
            helpCopy?.unavailableHelp ??
            "Gravação de áudio indisponível neste navegador ou contexto."
          }
        >
          <IconButton
            aria-label="Gravação de áudio indisponível"
            disabled
            className="delpi-ui-audio-recorder__trigger"
          >
            <MicOff size={18} aria-hidden="true" />
          </IconButton>
        </HelpTooltip>
      );
    }
  } else if (status === "idle" || status === "error") {
    trigger = (
      <HelpTooltip
        wrap
        content={helpCopy?.startHelp ?? "Iniciar a gravação de áudio."}
      >
        <IconButton
          aria-label={helpCopy?.startLabel ?? "Gravar áudio"}
          disabled={disabled || busy}
          onClick={() => {
            if (status === "error") clearError();
            start();
          }}
          className="delpi-ui-audio-recorder__trigger"
        >
          <Mic size={18} aria-hidden="true" />
        </IconButton>
      </HelpTooltip>
    );
  }

  let panel: ReactNode | null = null;

  if (status === "requesting_permission") {
    panel = (
      <div
        className="delpi-ui-audio-recorder delpi-ui-audio-recorder--requesting"
        role="status"
        aria-live="polite"
      >
        <span className="delpi-ui-audio-recorder__activity" aria-hidden="true">
          <i />
          <i />
          <i />
        </span>
        <span className="delpi-ui-audio-recorder__status-text">
          Aguardando acesso ao microfone…
        </span>
        <HelpTooltip
          wrap
          content="Cancelar a solicitação do microfone e voltar ao texto."
        >
          <IconButton aria-label="Cancelar solicitação de microfone" onClick={cancel}>
            <X size={18} aria-hidden="true" />
          </IconButton>
        </HelpTooltip>
      </div>
    );
  } else if (status === "recording" || status === "stopping") {
    panel = (
      <div
        className="delpi-ui-audio-recorder delpi-ui-audio-recorder--recording"
        role="region"
        aria-label="Gravação de áudio em andamento"
      >
        <span
          className="delpi-ui-audio-recorder__live-dot"
          aria-hidden="true"
        />
        <span className="delpi-ui-audio-recorder__live-label">Gravando</span>
        <span
          className="delpi-ui-audio-recorder__duration"
          aria-label={
            typeof maxDurationMs === "number" && maxDurationMs > 0
              ? `Duração ${formatAudioDurationMs(durationMs)} de ${formatAudioDurationMs(maxDurationMs)}`
              : `Duração ${formatAudioDurationMs(durationMs)}`
          }
        >
          {formatAudioDurationMs(durationMs)}
          {typeof maxDurationMs === "number" && maxDurationMs > 0 ? (
            <span
              className="delpi-ui-audio-recorder__duration-limit"
              aria-hidden="true"
            >
              {" / "}
              {formatAudioDurationMs(maxDurationMs)}
            </span>
          ) : null}
        </span>
        <Waveform levels={levels} live />
        {status === "recording" &&
        typeof maxDurationMs === "number" &&
        maxDurationMs > 30_000 &&
        durationMs >= maxDurationMs - 30_000 ? (
          <span
            className="delpi-ui-audio-recorder__limit-note"
            role="status"
          >
            A gravação será finalizada em breve.
          </span>
        ) : null}
        <div className="delpi-ui-audio-recorder__actions">
          <HelpTooltip
            wrap
            content="Descartar esta gravação e voltar ao texto anterior."
          >
            <IconButton
              aria-label="Cancelar gravação"
              tone="danger"
              onClick={cancel}
              disabled={status === "stopping"}
            >
              <X size={18} aria-hidden="true" />
            </IconButton>
          </HelpTooltip>
          <HelpTooltip
            wrap
            content={helpCopy?.finishHelp ?? "Encerrar a gravação."}
          >
            <IconButton
              aria-label="Finalizar gravação"
              tone="primary"
              onClick={stop}
              disabled={status === "stopping"}
              autoFocus={status === "recording"}
            >
              <Square size={16} aria-hidden="true" />
            </IconButton>
          </HelpTooltip>
        </div>
      </div>
    );
  } else if (status === "preview" && draft) {
    panel = (
      <div
        className="delpi-ui-audio-recorder delpi-ui-audio-recorder--preview"
        role="region"
        aria-label="Prévia do áudio gravado"
      >
        <HelpTooltip
          wrap
          content={
            isPlaying ? "Pausar a reprodução." : "Reproduzir esta gravação."
          }
        >
          <IconButton
            aria-label={isPlaying ? "Pausar áudio" : "Reproduzir áudio"}
            aria-pressed={isPlaying}
            onClick={togglePlayback}
          >
            {isPlaying ? (
              <Pause size={18} aria-hidden="true" />
            ) : (
              <Play size={18} aria-hidden="true" />
            )}
          </IconButton>
        </HelpTooltip>
        <div className="delpi-ui-audio-recorder__preview-meta">
          <span className="delpi-ui-audio-recorder__duration">
            {formatAudioDurationMs(draft.durationMs)}
          </span>
          <div
            className="delpi-ui-audio-recorder__progress"
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={Math.round(playbackProgress * 100)}
            aria-label="Progresso da reprodução"
          >
            <span
              className="delpi-ui-audio-recorder__progress-fill"
              style={{ width: `${Math.round(playbackProgress * 100)}%` }}
            />
          </div>
        </div>
        <div className="delpi-ui-audio-recorder__actions">
          <HelpTooltip
            wrap
            content="Descartar a gravação e voltar ao texto."
          >
            <IconButton aria-label="Descartar áudio" tone="danger" onClick={discard}>
              <X size={18} aria-hidden="true" />
            </IconButton>
          </HelpTooltip>
          <HelpTooltip
            wrap
            content="Descartar esta gravação e iniciar outra."
          >
            <IconButton aria-label="Regravar áudio" onClick={rerecord}>
              <RotateCcw size={18} aria-hidden="true" />
            </IconButton>
          </HelpTooltip>
          {canSendAudio ? (
            <HelpTooltip wrap content="Enviar este áudio.">
              <IconButton
                aria-label="Enviar áudio"
                tone="primary"
                onClick={() => onConfirmSend?.(draft)}
              >
                <Check size={18} aria-hidden="true" />
              </IconButton>
            </HelpTooltip>
          ) : null}
        </div>
      </div>
    );
  }

  // VD-F05: a duration/byte limit that produced a usable draft is
  // informational, not an error — muted note + role="status" instead of
  // the danger alert used for real capture failures.
  const limitReached =
    status === "preview" &&
    (errorReason === "limit_duration" || errorReason === "limit_bytes");
  const errorBanner = limitReached ? (
    <p className="delpi-ui-audio-recorder__limit-banner" role="status">
      {audioRecorderErrorMessage(errorReason)}
    </p>
  ) : status === "error" ? (
    <p className="delpi-ui-audio-recorder__error" role="alert">
      {audioRecorderErrorMessage(errorReason)}
    </p>
  ) : null;

  const api: AudioRecorderControlRenderProps = {
    trigger,
    panel: panel ? (
      <div className={["delpi-ui-audio-recorder-shell", className].filter(Boolean).join(" ")}>
        {panel}
        {status === "preview" ? errorBanner : null}
      </div>
    ) : status === "error" ? (
      <div className={["delpi-ui-audio-recorder-shell", className].filter(Boolean).join(" ")}>
        {errorBanner}
      </div>
    ) : null,
    blocking,
    status,
    errorReason,
    draft,
    discard,
  };

  if (typeof children === "function") {
    return <>{children(api)}</>;
  }

  return (
    <div className={["delpi-ui-audio-recorder-shell", className].filter(Boolean).join(" ")}>
      {api.panel}
      {status === "error" ? errorBanner : null}
      {trigger}
    </div>
  );
}
