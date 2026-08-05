// src/components/notifications/AdminNotificationTemplateSection.tsx

import { useMemo, useState } from "react";
import { Lock, Plus, Trash2 } from "lucide-react";

import type {
  CoreApi,
  NotificationAction,
  NotificationCategory,
  NotificationTemplateDefinition,
  NotificationType,
} from "../../data/coreApi";
import { Button, FormField, Input, Select } from "../../ui-kit";
import { NotificationCard } from "./NotificationCard";
import { CustomTemplateModal } from "./CustomTemplateModal";
import {
  buildTemplatePreview,
  isSystemTemplate,
  resolvePreviewRecipientName,
} from "./notificationTemplates";
import { useNotificationTemplates } from "./useNotificationTemplates";
import { useConfirmDialog } from "../ConfirmDialogProvider";

import "./AdminNotificationTemplateSection.css";

type AdminNotificationTemplateSectionProps = {
  coreApi: CoreApi;
  templateId: string;
  onTemplateIdChange: (id: string) => void;
  templateVars: Record<string, string>;
  onTemplateVarsChange: (vars: Record<string, string>) => void;
  category: NotificationCategory;
  type: NotificationType;
  previewUserName?: string | null;
  action: NotificationAction | null;
};

export function AdminNotificationTemplateSection({
  coreApi,
  templateId,
  onTemplateIdChange,
  templateVars,
  onTemplateVarsChange,
  category,
  type,
  previewUserName,
  action,
}: AdminNotificationTemplateSectionProps) {
  const confirm = useConfirmDialog();
  const { templates, loading, reload } = useNotificationTemplates(coreApi);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [isSavingTemplate, setIsSavingTemplate] = useState(false);

  const selectedTemplate = useMemo(
    () => templates.find((item) => item.id === templateId) ?? null,
    [templates, templateId],
  );

  const isSystem = isSystemTemplate(selectedTemplate);

  const previewRecipientVars = useMemo(() => {
    if (!selectedTemplate?.recipientAutoVars?.includes("userName")) {
      return undefined;
    }
    return { userName: resolvePreviewRecipientName(previewUserName) };
  }, [selectedTemplate, previewUserName]);

  const templatePreview = useMemo(() => {
    if (!selectedTemplate) {
      return null;
    }
    return buildTemplatePreview(selectedTemplate, templateVars, previewRecipientVars);
  }, [selectedTemplate, templateVars, previewRecipientVars]);

  const editableFields = isSystem
    ? (selectedTemplate?.fields ?? [])
    : (selectedTemplate?.fields ?? []);

  async function handleCreateTemplate(
    payload: Omit<NotificationTemplateDefinition, "id">,
  ) {
    setIsSavingTemplate(true);
    try {
      const created = await coreApi.createNotificationTemplate(payload);
      await reload();
      onTemplateIdChange(created.id);
      onTemplateVarsChange({});
    } finally {
      setIsSavingTemplate(false);
    }
  }

  async function handleDeleteTemplate() {
    if (!selectedTemplate || isSystem) {
      return;
    }
    const confirmed = await confirm({
      title: "Excluir template",
      message: `Excluir o template "${selectedTemplate.label}"?`,
      confirmText: "Excluir",
      danger: true,
    });
    if (!confirmed) return;
    await coreApi.deleteNotificationTemplate(selectedTemplate.id);
    await reload();
    const fallback = templates.find((item) => item.isSystem)?.id ?? "welcome_v1";
    onTemplateIdChange(fallback);
    onTemplateVarsChange({});
  }

  const previewCard = templatePreview ? (
    <div className="admin-notifications__preview admin-template-section__preview">
      <p className="admin-notifications__preview-label">Pré-visualização</p>
      <NotificationCard
        notification={{
          id: "preview",
          title: templatePreview.title,
          message: templatePreview.message,
          type,
          category,
          presentation: "template",
          metadata: {
            templateId,
            vars: { ...previewRecipientVars, ...templateVars },
          },
          read: false,
          createdAt: new Date().toISOString(),
          action,
        }}
        onMarkRead={async () => {}}
      />
    </div>
  ) : null;

  return (
  <>
    <div className="admin-template-section admin-template-section--split">
      <div className="admin-template-section__main">
      <div className="admin-template-section__toolbar">
        <FormField
          label="Template"
          htmlFor="admin-template-select"
          className="admin-template-section__select"
        >
          <Select
            id="admin-template-select"
            value={templateId}
            disabled={loading}
            onChange={(nextId) => {
              onTemplateIdChange(nextId);
              const next = templates.find((item) => item.id === nextId);
              if (next) {
                const initialVars: Record<string, string> = {};
                for (const field of next.fields) {
                  initialVars[field.key] = templateVars[field.key] ?? "";
                }
                onTemplateVarsChange(initialVars);
              }
            }}
            options={templates.map((item) => ({
              value: item.id,
              label: `${item.isSystem ? "🔒 " : ""}${item.label}`,
            }))}
          />
        </FormField>

        <Button
          type="button"
          variant="secondary"
          size="sm"
          icon={<Plus size={16} />}
          onClick={() => setShowCreateModal(true)}
        >
          Novo template
        </Button>

        {!isSystem && selectedTemplate ? (
          <Button
            type="button"
            variant="danger-soft"
            size="sm"
            icon={<Trash2 size={16} />}
            onClick={() => void handleDeleteTemplate()}
          >
            Excluir
          </Button>
        ) : null}
      </div>

      {isSystem && selectedTemplate ? (
        <div className="admin-template-section__readonly">
          <p className="admin-template-section__readonly-title">
            <Lock size={14} aria-hidden="true" />
            Template padrão do sistema (somente leitura)
          </p>
          <dl className="admin-template-section__spec">
            <div>
              <dt>Título</dt>
              <dd>{selectedTemplate.defaultTitle}</dd>
            </div>
            <div>
              <dt>Mensagem</dt>
              <dd>{selectedTemplate.defaultMessage}</dd>
            </div>
            {selectedTemplate.hint ? (
              <div>
                <dt>Texto auxiliar</dt>
                <dd>{selectedTemplate.hint}</dd>
              </div>
            ) : null}
          </dl>
          {selectedTemplate.recipientAutoVars?.includes("userName") ? (
            <p className="admin-notifications__auto-var-hint">
              O nome de cada destinatário ({`{userName}`}) é preenchido automaticamente pelo
              sistema.
            </p>
          ) : null}
        </div>
      ) : null}

      {editableFields.map((field) => (
        <FormField
          key={field.key}
          label={field.label}
          required={field.required}
          htmlFor={`admin-template-field-${field.key}`}
        >
          <Input
            id={`admin-template-field-${field.key}`}
            value={templateVars[field.key] ?? ""}
            onChange={(event) =>
              onTemplateVarsChange({ ...templateVars, [field.key]: event.target.value })
            }
            placeholder={field.placeholder}
            required={field.required}
          />
        </FormField>
      ))}

      {!isSystem && selectedTemplate?.recipientAutoVars?.includes("userName") ? (
        <p className="admin-notifications__auto-var-hint">
          Este template personalizado usa {`{userName}`} do cadastro de cada destinatário.
        </p>
      ) : null}

      </div>
      {previewCard ? (
        <aside className="admin-template-section__aside" aria-label="Pré-visualização">
          {previewCard}
        </aside>
      ) : null}
    </div>

    <CustomTemplateModal
      open={showCreateModal}
      onClose={() => setShowCreateModal(false)}
      onSave={handleCreateTemplate}
      isSaving={isSavingTemplate}
    />
  </>
  );
}
