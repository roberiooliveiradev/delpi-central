import { useEffect, useId, useMemo, useState } from "react";

import {
  fillShortcutTemplate,
  type ShortcutFieldDefinition,
  validateShortcutValues,
} from "../chatShortcutPrompt";

import { ModalPortal } from "./ModalPortal";
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
  title = "Preencha para continuar",
  description = "Informe os dados da consulta antes de enviar.",
  fields,
  initialValues = {},
  confirmLabel = "Usar no chat",
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

  if (!open) {
    return null;
  }

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
    <ModalPortal>
      <div
        className="mdc-chat-shortcut-prompt-backdrop"
        role="presentation"
        onMouseDown={(event) => {
          if (event.target === event.currentTarget) {
            onCancel();
          }
        }}
      >
        <section
          className="mdc-chat-shortcut-prompt"
          role="dialog"
          aria-modal="true"
          aria-labelledby={`${formId}-title`}
        >
          <header className="mdc-chat-shortcut-prompt__header">
            <h2 id={`${formId}-title`}>{title}</h2>
            <p>{description}</p>
          </header>

          <form id={formId} className="mdc-chat-shortcut-prompt__form" onSubmit={handleSubmit}>
            {fields.map((field) => (
              <label key={field.id} className="mdc-chat-shortcut-prompt__field">
                <span>{field.label}</span>
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
        </section>
      </div>
    </ModalPortal>
  );
}
