import { useEffect, useId, useMemo, useState } from "react";

import {
  CHAT_SHORTCUT_PROMPT_COPY,
  fillShortcutTemplate,
  type ShortcutFieldDefinition,
  validateShortcutValues,
} from "../../../chatShortcutPrompt";

import { ChatModal } from "./ChatModal";
import "./ChatShortcutPromptDialog.css";

type ChatShortcutPromptDialogProps = {
  open: boolean;
  template: string;
  title?: string;
  description?: string;
  fields: ShortcutFieldDefinition[];
  initialValues?: Record<string, string>;
  confirmLabel?: string;
  onCancel: () => void;
  onConfirm: (filledQuery: string) => void;
};

export function ChatShortcutPromptDialog({
  open,
  template,
  title = CHAT_SHORTCUT_PROMPT_COPY.insert.title,
  description = CHAT_SHORTCUT_PROMPT_COPY.insert.description,
  fields,
  initialValues = {},
  confirmLabel = CHAT_SHORTCUT_PROMPT_COPY.insert.confirmLabel,
  onCancel,
  onConfirm,
}: ChatShortcutPromptDialogProps) {
  const formId = useId();
  const [values, setValues] = useState<Record<string, string>>(initialValues);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!open) {
      return;
    }

    setValues(initialValues);
    setErrors({});
  }, [open, template]);

  const preview = useMemo(() => {
    const filled = fillShortcutTemplate(template, values).trim();
    return filled || template;
  }, [template, values]);

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();

    const validationErrors = validateShortcutValues(fields, values);

    if (validationErrors) {
      setErrors(validationErrors);
      return;
    }

    const filledQuery = fillShortcutTemplate(template, values).trim();

    if (!filledQuery || filledQuery.includes("{{")) {
      setErrors({ _form: "Preencha todos os campos." });
      return;
    }

    onConfirm(filledQuery);
  }

  return (
    <ChatModal
      open={open}
      onClose={onCancel}
      size="md"
      ariaLabelledBy={`${formId}-title`}
      panelClassName="mdc-chat-shortcut-prompt"
    >
      <header className="mdc-chat-shortcut-prompt__header">
        <h2 id={`${formId}-title`}>{title}</h2>
        <p>{description}</p>
      </header>

      <form id={formId} className="mdc-chat-shortcut-prompt__form" onSubmit={handleSubmit}>
        {fields.map((field) => (
          <label key={field.id} className="mdc-chat-shortcut-prompt__field">
            <span>{field.label}</span>
            {field.multiline ? (
              <textarea
                rows={4}
                autoComplete="off"
                autoFocus={fields[0]?.id === field.id}
                placeholder={field.placeholder}
                value={values[field.id] ?? ""}
                onChange={(event) => {
                  const next = event.target.value;
                  setValues((current) => ({ ...current, [field.id]: next }));
                  setErrors((current) => {
                    if (!current[field.id]) {
                      return current;
                    }

                    const copy = { ...current };
                    delete copy[field.id];
                    return copy;
                  });
                }}
              />
            ) : (
              <input
                type="text"
                inputMode={field.inputMode === "numeric" ? "numeric" : "text"}
                autoComplete="off"
                autoFocus={fields[0]?.id === field.id}
                placeholder={field.placeholder}
                value={values[field.id] ?? ""}
                onChange={(event) => {
                  const next = event.target.value;
                  setValues((current) => ({ ...current, [field.id]: next }));
                  setErrors((current) => {
                    if (!current[field.id]) {
                      return current;
                    }

                    const copy = { ...current };
                    delete copy[field.id];
                    return copy;
                  });
                }}
              />
            )}
            {errors[field.id] ? (
              <small className="mdc-chat-shortcut-prompt__error">{errors[field.id]}</small>
            ) : null}
          </label>
        ))}

        {errors._form ? (
          <p className="mdc-chat-shortcut-prompt__error">{errors._form}</p>
        ) : null}

        <p className="mdc-chat-shortcut-prompt__preview">
          <span>Prévia</span>
          <em>{preview}</em>
        </p>

        <div className="mdc-chat-shortcut-prompt__actions">
          <button type="button" className="mdc-chat-shortcut-prompt__cancel" onClick={onCancel}>
            Cancelar
          </button>
          <button type="submit" className="mdc-chat-shortcut-prompt__confirm">
            {confirmLabel}
          </button>
        </div>
      </form>
    </ChatModal>
  );
}
