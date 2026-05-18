// src/components/notifications/CustomTemplateModal.tsx

import { useRef, useState, type FormEvent } from "react";
import { X } from "lucide-react";

import type {
  NotificationCategory,
  NotificationTemplateDefinition,
  NotificationType,
} from "../../data/coreApi";
import { NotificationVariableToolbar } from "./NotificationVariableToolbar";

import "./CustomTemplateModal.css";

type CustomTemplateModalProps = {
  open: boolean;
  onClose: () => void;
  onSave: (payload: Omit<NotificationTemplateDefinition, "id">) => Promise<void>;
  isSaving?: boolean;
};

const CATEGORIES: NotificationCategory[] = [
  "custom",
  "announcement",
  "company_event",
  "welcome",
  "birthday",
  "system",
];

const TYPES: NotificationType[] = ["info", "success", "warning", "error"];

export function CustomTemplateModal({
  open,
  onClose,
  onSave,
  isSaving = false,
}: CustomTemplateModalProps) {
  const titleRef = useRef<HTMLInputElement>(null);
  const messageRef = useRef<HTMLTextAreaElement>(null);

  const [label, setLabel] = useState("");
  const [category, setCategory] = useState<NotificationCategory>("custom");
  const [defaultType, setDefaultType] = useState<NotificationType>("info");
  const [defaultTitle, setDefaultTitle] = useState("");
  const [defaultMessage, setDefaultMessage] = useState("");
  const [hint, setHint] = useState("");
  const [useUserName, setUseUserName] = useState(true);
  const [error, setError] = useState<string | null>(null);

  if (!open) {
    return null;
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    if (!label.trim() || !defaultTitle.trim() || !defaultMessage.trim()) {
      setError("Preencha nome, título e mensagem do template.");
      return;
    }

    try {
      await onSave({
        label: label.trim(),
        category,
        defaultType,
        defaultTitle: defaultTitle.trim(),
        defaultMessage: defaultMessage.trim(),
        recipientAutoVars: useUserName ? ["userName"] : [],
        recipientVars: useUserName ? ["userName"] : [],
        requiredVars: [],
        optionalVars: [],
        isSystem: false,
        hint: hint.trim() || undefined,
        fields: [],
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao salvar template");
    }
  }

  return (
    <div className="custom-template-modal__backdrop" role="presentation" onClick={onClose}>
      <div
        className="custom-template-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="custom-template-title"
        onClick={(event) => event.stopPropagation()}
      >
        <header className="custom-template-modal__header">
          <h3 id="custom-template-title">Novo template personalizado</h3>
          <button type="button" className="custom-template-modal__close" onClick={onClose}>
            <X size={18} />
          </button>
        </header>

        <form className="custom-template-modal__form" onSubmit={(event) => void handleSubmit(event)}>
          <label className="custom-template-modal__field">
            <span>Nome do template *</span>
            <input value={label} onChange={(e) => setLabel(e.target.value)} maxLength={120} />
          </label>

          <div className="custom-template-modal__row">
            <label className="custom-template-modal__field">
              <span>Categoria</span>
              <select value={category} onChange={(e) => setCategory(e.target.value as NotificationCategory)}>
                {CATEGORIES.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
            <label className="custom-template-modal__field">
              <span>Tipo visual</span>
              <select value={defaultType} onChange={(e) => setDefaultType(e.target.value as NotificationType)}>
                {TYPES.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <label className="custom-template-modal__field">
            <span>Título *</span>
            <input
              ref={titleRef}
              value={defaultTitle}
              onChange={(e) => setDefaultTitle(e.target.value)}
              maxLength={120}
            />
            <NotificationVariableToolbar
              targetRef={titleRef}
              value={defaultTitle}
              onChange={setDefaultTitle}
              disabled={isSaving}
            />
          </label>

          <label className="custom-template-modal__field">
            <span>Mensagem *</span>
            <textarea
              ref={messageRef}
              value={defaultMessage}
              onChange={(e) => setDefaultMessage(e.target.value)}
              rows={3}
              maxLength={500}
            />
            <NotificationVariableToolbar
              targetRef={messageRef}
              value={defaultMessage}
              onChange={setDefaultMessage}
              disabled={isSaving}
            />
          </label>

          <label className="custom-template-modal__field">
            <span>Texto auxiliar (opcional)</span>
            <input value={hint} onChange={(e) => setHint(e.target.value)} maxLength={200} />
          </label>

          <label className="custom-template-modal__checkbox">
            <input
              type="checkbox"
              checked={useUserName}
              onChange={(e) => setUseUserName(e.target.checked)}
            />
            Usar nome do destinatário automaticamente ({`{userName}`})
          </label>

          {error ? <p className="custom-template-modal__error">{error}</p> : null}

          <footer className="custom-template-modal__footer">
            <button type="button" className="custom-template-modal__ghost" onClick={onClose}>
              Cancelar
            </button>
            <button type="submit" className="custom-template-modal__submit" disabled={isSaving}>
              {isSaving ? "Salvando..." : "Criar template"}
            </button>
          </footer>
        </form>
      </div>
    </div>
  );
}
