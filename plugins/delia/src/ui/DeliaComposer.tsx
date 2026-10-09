import { useEffect, useRef } from "react";
import type { KeyboardEvent as ReactKeyboardEvent } from "react";
import { NativeTextAreaControl } from "@delpi/plugin-ui/index";
import { SendHorizontal } from "lucide-react";

/** Bounded composer growth — beyond this the textarea scrolls. */
const COMPOSER_MAX_HEIGHT_PX = 160;

export type DeliaComposerProps = {
  inputId: string;
  value: string;
  onChange: (value: string) => void;
  /** Explicit user intent only — never invoked programmatically. */
  onSubmit: () => void;
  loading?: boolean;
  placeholder?: string;
};

/**
 * S2-C — single composer shared by the full page and the global dock.
 *
 * Enter submits, Shift+Enter inserts a newline, IME composition is
 * never interrupted (`isComposing` guard). The draft is owned by the
 * parent and survives a failed request — the composer never clears it.
 */
export function DeliaComposer({
  inputId,
  value,
  onChange,
  onSubmit,
  loading = false,
  placeholder = "Escreva sua pergunta…",
}: DeliaComposerProps) {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(
      textarea.scrollHeight,
      COMPOSER_MAX_HEIGHT_PX,
    )}px`;
  }, [value]);

  function handleKeyDown(event: ReactKeyboardEvent<HTMLTextAreaElement>) {
    if (event.key !== "Enter" || event.shiftKey) return;
    if (event.nativeEvent.isComposing) return;
    event.preventDefault();
    onSubmit();
  }

  return (
    <form
      className="delia-composer"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <label className="delia-visually-hidden" htmlFor={inputId}>
        Pergunte à DÉLIA
      </label>
      <NativeTextAreaControl
        ref={textareaRef}
        id={inputId}
        className="delia-composer__input"
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        rows={1}
        disabled={loading}
        onKeyDown={handleKeyDown}
      />
      <button
        type="submit"
        className="delia-composer__submit"
        disabled={loading || !value.trim()}
      >
        <SendHorizontal size={15} aria-hidden="true" />
        <span>{loading ? "Enviando…" : "Enviar"}</span>
      </button>
    </form>
  );
}
