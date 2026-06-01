import { useEffect, useId, useState } from "react";

import type { ChatContextChip } from "./ChatContextBar";
import { ModalPortal } from "./ModalPortal";
import "./ChatAddContextDialog.css";

export type ManualContextPinKind = "branch" | "warehouse" | "product";

const PIN_KIND_OPTIONS: Array<{ id: ManualContextPinKind; label: string; placeholder: string }> = [
  { id: "branch", label: "Filial", placeholder: "Ex.: 01 ou 02" },
  { id: "warehouse", label: "Armazém", placeholder: "Ex.: 01 ou 99" },
  { id: "product", label: "Produto", placeholder: "Ex.: 10080001" },
];

type ChatAddContextDialogProps = {
  open: boolean;
  onCancel: () => void;
  onConfirm: (chip: ChatContextChip) => void;
};

export function buildManualContextChip(kind: ManualContextPinKind, rawValue: string): ChatContextChip | null {
  const value = rawValue.trim();

  if (!value) {
    return null;
  }

  if (kind === "branch") {
    return { kind: "branch", value: value.toUpperCase(), label: `Filial ${value.toUpperCase()}` };
  }

  if (kind === "warehouse") {
    return {
      kind: "warehouse",
      value: value.toUpperCase(),
      label: `Armazém ${value.toUpperCase()}`,
    };
  }

  const productCode = value.replace(/\s+/g, "").toUpperCase();

  if (!/^[A-Z0-9.-]{4,20}$/.test(productCode)) {
    return null;
  }

  return { kind: "product", value: productCode, label: `Produto ${productCode}` };
}

export function ChatAddContextDialog({ open, onCancel, onConfirm }: ChatAddContextDialogProps) {
  const formId = useId();
  const [kind, setKind] = useState<ManualContextPinKind>("branch");
  const [value, setValue] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) {
      return;
    }

    setKind("branch");
    setValue("");
    setError(null);
  }, [open]);

  if (!open) {
    return null;
  }

  const selectedOption = PIN_KIND_OPTIONS.find((option) => option.id === kind) ?? PIN_KIND_OPTIONS[0];

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();

    const chip = buildManualContextChip(kind, value);

    if (!chip) {
      setError("Informe um valor válido para o contexto.");
      return;
    }

    onConfirm(chip);
  }

  return (
    <ModalPortal>
      <div
        className="mdc-chat-add-context-backdrop"
        role="presentation"
        onMouseDown={(event) => {
          if (event.target === event.currentTarget) {
            onCancel();
          }
        }}
      >
        <section
          className="mdc-chat-add-context"
          role="dialog"
          aria-modal="true"
          aria-labelledby={`${formId}-title`}
        >
          <header className="mdc-chat-add-context__header">
            <h2 id={`${formId}-title`}>Adicionar ao contexto</h2>
            <p>Fixe filial, armazém ou produto para as próximas perguntas desta conversa.</p>
          </header>

          <form id={formId} className="mdc-chat-add-context__form" onSubmit={handleSubmit}>
            <label className="mdc-chat-add-context__field">
              <span>Tipo</span>
              <select
                value={kind}
                onChange={(event) => {
                  setKind(event.target.value as ManualContextPinKind);
                  setError(null);
                }}
              >
                {PIN_KIND_OPTIONS.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="mdc-chat-add-context__field">
              <span>{selectedOption.label}</span>
              <input
                value={value}
                placeholder={selectedOption.placeholder}
                autoFocus
                onChange={(event) => {
                  setValue(event.target.value);
                  setError(null);
                }}
              />
            </label>

            {error ? <p className="mdc-chat-add-context__error">{error}</p> : null}

            <footer className="mdc-chat-add-context__actions">
              <button type="button" className="mdc-chat-add-context__secondary" onClick={onCancel}>
                Cancelar
              </button>
              <button type="submit" className="mdc-chat-add-context__primary">
                Adicionar
              </button>
            </footer>
          </form>
        </section>
      </div>
    </ModalPortal>
  );
}
