// src/components/notifications/CustomTemplateModal.tsx

import { useRef, useState, type FormEvent } from "react";
import { X } from "lucide-react";

import type {
  NotificationCategory,
  NotificationTemplateDefinition,
  NotificationType,
} from "../../data/coreApi";
import { Alert, Button, Checkbox, FormField, FormGrid, Input, Select, Textarea } from "../../ui-kit";
import { NOTIFICATION_TYPE_OPTIONS } from "../../utils/notificationSeverityTone";
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
          <Button
            type="button"
            variant="ghost"
            size="sm"
            aria-label="Fechar"
            onClick={onClose}
            icon={<X size={18} />}
          />
        </header>

        <form className="custom-template-modal__form" onSubmit={(event) => void handleSubmit(event)}>
          <FormField label="Nome do template" required htmlFor="custom-template-label">
            <Input
              id="custom-template-label"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              maxLength={120}
            />
          </FormField>

          <FormGrid columns={2}>
            <FormField label="Categoria" htmlFor="custom-template-category">
              <Select
                id="custom-template-category"
                value={category}
                onChange={(value) => setCategory(value as NotificationCategory)}
                options={CATEGORIES.map((item) => ({ value: item, label: item }))}
              />
            </FormField>
            <FormField label="Tipo visual" htmlFor="custom-template-type">
              <Select
                id="custom-template-type"
                value={defaultType}
                onChange={(value) => setDefaultType(value as NotificationType)}
                options={NOTIFICATION_TYPE_OPTIONS}
              />
            </FormField>
          </FormGrid>

          <div className="custom-template-modal__field-stack">
            <FormField label="Título" required htmlFor="custom-template-default-title">
              <Input
                id="custom-template-default-title"
                ref={titleRef}
                value={defaultTitle}
                onChange={(e) => setDefaultTitle(e.target.value)}
                maxLength={120}
              />
            </FormField>
            <NotificationVariableToolbar
              targetRef={titleRef}
              value={defaultTitle}
              onChange={setDefaultTitle}
              disabled={isSaving}
            />
          </div>

          <div className="custom-template-modal__field-stack">
            <FormField label="Mensagem" required htmlFor="custom-template-default-message">
              <Textarea
                id="custom-template-default-message"
                ref={messageRef}
                value={defaultMessage}
                onChange={(e) => setDefaultMessage(e.target.value)}
                rows={3}
                maxLength={500}
              />
            </FormField>
            <NotificationVariableToolbar
              targetRef={messageRef}
              value={defaultMessage}
              onChange={setDefaultMessage}
              disabled={isSaving}
            />
          </div>

          <FormField label="Texto auxiliar (opcional)" htmlFor="custom-template-hint">
            <Input
              id="custom-template-hint"
              value={hint}
              onChange={(e) => setHint(e.target.value)}
              maxLength={200}
            />
          </FormField>

          <Checkbox
            checked={useUserName}
            onChange={(e) => setUseUserName(e.target.checked)}
            label={
              <>
                Usar nome do destinatário automaticamente ({`{userName}`})
              </>
            }
          />

          {error ? <Alert tone="danger">{error}</Alert> : null}

          <footer className="custom-template-modal__footer">
            <Button type="button" variant="ghost" onClick={onClose}>
              Cancelar
            </Button>
            <Button type="submit" variant="primary" loading={isSaving} disabled={isSaving}>
              {isSaving ? "Salvando..." : "Criar template"}
            </Button>
          </footer>
        </form>
      </div>
    </div>
  );
}
