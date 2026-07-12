import { ChatNativeTextInput } from "../chatNativeFormFields";
import { useEffect, useId, useRef } from "react";
import { X } from "lucide-react";

import { ChatModal } from "./ChatModal";
import "./ChatPromptDialog.css";

type ChatPromptDialogProps = {
  open: boolean;
  title: string;
  description?: string;
  label?: string;
  defaultValue?: string;
  placeholder?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  maxLength?: number;
  onConfirm: (value: string) => void;
  onCancel: () => void;
};

export function ChatPromptDialog({
  open,
  title,
  description,
  label,
  defaultValue = "",
  placeholder,
  confirmLabel = "Salvar",
  cancelLabel = "Cancelar",
  maxLength = 120,
  onConfirm,
  onCancel,
}: ChatPromptDialogProps) {
  const titleId = useId();
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!open) {
      return;
    }

    const frame = window.requestAnimationFrame(() => {
      const input = inputRef.current;

      if (!input) {
        return;
      }

      input.value = defaultValue;
      input.focus();
      input.select();
    });

    return () => window.cancelAnimationFrame(frame);
  }, [defaultValue, open]);

  return (
    <ChatModal
      open={open}
      onClose={onCancel}
      size="md"
      mobileLayout="centered"
      ariaLabelledBy={titleId}
      panelClassName="mdc-chat-prompt"
    >
      <header className="mdc-chat-prompt__header">
        <div>
          <h2 id={titleId}>{title}</h2>
          {description ? <p>{description}</p> : null}
        </div>

        <button
          type="button"
          className="mdc-chat-modal-icon-btn mdc-chat-modal-icon-btn--outlined mdc-chat-modal-icon-btn--sm"
          onClick={onCancel}
          aria-label="Fechar"
        >
          <X size={17} aria-hidden="true" />
        </button>
      </header>

      <form
        className="mdc-chat-prompt__form"
        onSubmit={(event) => {
          event.preventDefault();
          const value = inputRef.current?.value.trim() ?? "";

          if (value) {
            onConfirm(value);
          }
        }}
      >
        <label className="mdc-chat-prompt__field">
          <span>{label ?? "Nome"}</span>
          <ChatNativeTextInput
            ref={inputRef}
            type="text"
            defaultValue={defaultValue}
            placeholder={placeholder}
            maxLength={maxLength}
            autoComplete="off"
          />
        </label>

        <footer className="mdc-chat-prompt__actions">
          <button type="button" className="mdc-chat-prompt__secondary" onClick={onCancel}>
            {cancelLabel}
          </button>
          <button type="submit" className="mdc-chat-prompt__primary">
            {confirmLabel}
          </button>
        </footer>
      </form>
    </ChatModal>
  );
}
