import { useEffect, useRef } from "react";
import type {
  KeyboardEvent as ReactKeyboardEvent,
  ReactNode,
} from "react";

import { NativeTextAreaControl } from "../forms/NativeTextAreaControl";
import { ComposerCharacterCounter } from "./ComposerCharacterCounter";
import { ComposerSendButton } from "./ComposerSendButton";

const DEFAULT_MAX_INPUT_HEIGHT_PX = 160;

export type MessageComposerProps = {
  value: string;
  onChange: (value: string) => void;
  /** Explicit user intent only — invoked by Enter or the send control. */
  onSubmit: () => void;
  /** id applied to the textarea. */
  inputId?: string;
  /** Accessible name of the textarea (no visible label by design). */
  inputLabel?: string;
  placeholder?: string;
  disabled?: boolean;
  loading?: boolean;
  /** Accessible name of the send action while a request is in flight. */
  loadingLabel?: string;
  /** Secondary text rendered under the surface (honest product copy). */
  helperText?: ReactNode;
  /** Submit failure text — rendered with `role="alert"`, draft preserved. */
  error?: string | null;
  /**
   * Left region of the toolbar for real, contracted secondary actions
   * (compose with `IconButton`). Omit — never pad — while no contract
   * exists for a control.
   */
  secondaryActions?: ReactNode;
  /** Visual keyboard hint; `null` omits it. CSS may hide it on narrow docks. */
  keyboardHint?: string | null;
  /**
   * Contracted input bound (e.g. backend-enforced max chars). The
   * `n/limit` counter renders only when provided — never invent it.
   */
  characterLimit?: number;
  /** Auto-grow cap in px; the textarea scrolls beyond it. */
  maxInputHeight?: number;
  /** Send button label (icon remains in every layout). */
  sendLabel?: string;
  className?: string;
};

/**
 * Chat-first message composer — single rounded surface with two bands:
 * a borderless multiline write area and a bottom toolbar
 * (secondary actions · hint/counter · primary send).
 *
 * Presentation only: the host owns the draft, submission, loading and
 * error policy. The composer never clears the draft, never persists
 * anything and never calls an API itself.
 *
 * CSS: `styles/message-composer.css` (`.delpi-ui-message-composer*`).
 * Tokens: `--delpi-ui-*` with Portal fallbacks (`--surface`, `--text`,
 * `--border`, `--primary`) — light and dark follow the host theme.
 */
export function MessageComposer({
  value,
  onChange,
  onSubmit,
  inputId,
  inputLabel,
  placeholder,
  disabled = false,
  loading = false,
  loadingLabel = "Enviando…",
  helperText,
  error,
  secondaryActions,
  keyboardHint = "Enter envia · Shift+Enter quebra linha",
  characterLimit,
  maxInputHeight = DEFAULT_MAX_INPUT_HEIGHT_PX,
  sendLabel = "Enviar",
  className,
}: MessageComposerProps) {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const canSubmit = !disabled && !loading && value.trim().length > 0;

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(
      textarea.scrollHeight,
      maxInputHeight,
    )}px`;
  }, [value, maxInputHeight]);

  function submitIntent() {
    if (!canSubmit) return;
    onSubmit();
  }

  function handleKeyDown(event: ReactKeyboardEvent<HTMLTextAreaElement>) {
    if (event.key !== "Enter" || event.shiftKey) return;
    if (event.nativeEvent.isComposing) return;
    event.preventDefault();
    submitIntent();
  }

  return (
    <form
      className={["delpi-ui-message-composer", className]
        .filter(Boolean)
        .join(" ")}
      onSubmit={(event) => {
        event.preventDefault();
        submitIntent();
      }}
    >
      <div className="delpi-ui-message-composer__surface">
        <div className="delpi-ui-message-composer__write">
          <NativeTextAreaControl
            ref={textareaRef}
            id={inputId}
            className="delpi-ui-message-composer__input"
            value={value}
            onChange={onChange}
            placeholder={placeholder}
            aria-label={inputLabel}
            rows={1}
            disabled={disabled || loading}
            onKeyDown={handleKeyDown}
          />
          {typeof characterLimit === "number" && characterLimit > 0 ? (
            <ComposerCharacterCounter
              value={value}
              limit={characterLimit}
            />
          ) : null}
        </div>

        <div className="delpi-ui-message-composer__toolbar">
          {secondaryActions ? (
            <div className="delpi-ui-message-composer__actions">
              {secondaryActions}
            </div>
          ) : null}
          {keyboardHint ? (
            <span className="delpi-ui-message-composer__hint">
              {keyboardHint}
            </span>
          ) : null}
          <ComposerSendButton
            loading={loading}
            disabled={disabled || !value.trim()}
            label={sendLabel}
            loadingLabel={loadingLabel}
          />
        </div>
      </div>

      {error ? (
        <p className="delpi-ui-message-composer__error" role="alert">
          {error}
        </p>
      ) : null}
      {helperText ? (
        <p className="delpi-ui-message-composer__helper">{helperText}</p>
      ) : null}
    </form>
  );
}
