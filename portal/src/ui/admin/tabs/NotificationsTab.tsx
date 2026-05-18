// src/ui/admin/tabs/NotificationsTab.tsx

import { useContext, useEffect, useMemo, useState, type FormEvent } from "react";
import { Bell } from "lucide-react";

import { AuthContext } from "../../../state/AuthContext";
import { ApiClient } from "../../../data/apiClient";
import { AdminApi } from "../../../data/adminApi";
import {
  CoreApi,
  type DispatchNotificationsPayload,
  type NotificationActionType,
  type NotificationCategory,
  type NotificationPresentation,
  type NotificationTemplateId,
  type NotificationType,
} from "../../../data/coreApi";
import { NotificationCard } from "../../../components/notifications/NotificationCard";
import {
  NOTIFICATION_TEMPLATE_DEFINITIONS,
  buildTemplatePreview,
  resolvePreviewRecipientName,
} from "../../../components/notifications/notificationTemplates";
import { NotificationRecipientPicker } from "../../../components/notifications/NotificationRecipientPicker";

import "./NotificationsTab.css";

const NOTIFICATION_TYPES: NotificationType[] = ["info", "success", "warning", "error"];

const NOTIFICATION_CATEGORIES: { value: NotificationCategory; label: string }[] = [
  { value: "system", label: "Sistema" },
  { value: "welcome", label: "Boas-vindas" },
  { value: "birthday", label: "Aniversário" },
  { value: "company_event", label: "Evento da empresa" },
  { value: "announcement", label: "Comunicado" },
  { value: "custom", label: "Personalizada" },
];

const PRESENTATION_MODES: { value: NotificationPresentation; label: string }[] = [
  { value: "text", label: "Texto simples" },
  { value: "template", label: "Template visual (recomendado)" },
  { value: "html", label: "HTML personalizado (sanitizado)" },
];

const ACTION_TYPES: { value: NotificationActionType | "none"; label: string }[] = [
  { value: "none", label: "Sem ação" },
  { value: "portal_route", label: "Rota do Portal" },
  { value: "external_url", label: "URL externa (https)" },
];

export function NotificationsTab() {
  const { getAccessToken, refreshToken, user } = useContext(AuthContext);

  const apiClient = useMemo(
    () =>
      new ApiClient("", getAccessToken, {
        refreshToken: async () => {
          await refreshToken();
          return Boolean(getAccessToken());
        },
      }),
    [getAccessToken, refreshToken],
  );

  const coreApi = useMemo(() => new CoreApi(apiClient), [apiClient]);
  const adminApi = useMemo(() => new AdminApi(apiClient), [apiClient]);

  const [broadcast, setBroadcast] = useState(false);
  const [selectedUserIds, setSelectedUserIds] = useState<string[]>([]);
  const [extraEmails, setExtraEmails] = useState<string[]>([]);
  const [title, setTitle] = useState("");
  const [message, setMessage] = useState("");
  const [type, setType] = useState<NotificationType>("info");
  const [category, setCategory] = useState<NotificationCategory>("announcement");
  const [presentation, setPresentation] = useState<NotificationPresentation>("text");
  const [htmlContent, setHtmlContent] = useState("");
  const [templateId, setTemplateId] = useState<NotificationTemplateId>("welcome_v1");
  const [templateVars, setTemplateVars] = useState<Record<string, string>>({});
  const [actionType, setActionType] = useState<NotificationActionType | "none">("none");
  const [actionLabel, setActionLabel] = useState("");
  const [actionTarget, setActionTarget] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const isSuperadmin = Boolean(user?.is_superadmin);

  const selectedTemplate = useMemo(
    () => NOTIFICATION_TEMPLATE_DEFINITIONS.find((item) => item.id === templateId) ?? null,
    [templateId],
  );

  const previewRecipientVars = useMemo(() => {
    if (!selectedTemplate?.recipientAutoVars?.includes("userName")) {
      return undefined;
    }
    return { userName: resolvePreviewRecipientName(user?.name) };
  }, [selectedTemplate, user?.name]);

  const templatePreview = useMemo(() => {
    if (!selectedTemplate) {
      return null;
    }
    return buildTemplatePreview(selectedTemplate, templateVars, previewRecipientVars);
  }, [selectedTemplate, templateVars, previewRecipientVars]);

  useEffect(() => {
    if (!selectedTemplate || presentation !== "template") {
      return;
    }
    setCategory(selectedTemplate.category);
    setType(selectedTemplate.defaultType);
  }, [selectedTemplate, presentation]);

  function updateTemplateVar(key: string, value: string) {
    setTemplateVars((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    if (!isSuperadmin) {
      setError("Apenas superadmin pode enviar notificações.");
      return;
    }

    setIsSubmitting(true);
    setFeedback(null);
    setError(null);

    if (!broadcast && selectedUserIds.length === 0 && extraEmails.length === 0) {
      setError("Selecione ao menos um destinatário (e-mail, ID ou card de usuário).");
      setIsSubmitting(false);
      return;
    }

    const isTemplate = presentation === "template";
    const fallbackMessage = isTemplate
      ? templatePreview?.message ?? "Notificação"
      : message.trim();

    if (!fallbackMessage) {
      setError("Informe a mensagem ou preencha o template.");
      setIsSubmitting(false);
      return;
    }

    const payload: DispatchNotificationsPayload = {
      broadcast,
      userIds: broadcast ? undefined : selectedUserIds,
      emails: broadcast ? undefined : extraEmails,
      title: isTemplate ? title.trim() || templatePreview?.title || null : title.trim() || null,
      message: fallbackMessage,
      type,
      category,
      presentation,
      htmlContent: presentation === "html" ? htmlContent : null,
      templateId: isTemplate ? templateId : undefined,
      templateVars: isTemplate ? templateVars : undefined,
      action:
        actionType === "none"
          ? null
          : {
              type: actionType,
              label: actionLabel.trim() || undefined,
              target: actionTarget.trim(),
            },
      sourceApp: "portal-admin",
    };

    try {
      const result = await coreApi.dispatchNotifications(payload);
      const count = result.createdCount;
      setFeedback(
        count === 1
          ? "1 notificação enviada."
          : `${count} notificações enviadas para ${count} destinatário(s).`,
      );

      if (!broadcast) {
        setSelectedUserIds([]);
        setExtraEmails([]);
      }

      setMessage("");
      setHtmlContent("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao enviar notificações");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (!isSuperadmin) {
    return (
      <section className="admin-notifications">
        <div className="admin-notifications__empty">
          <Bell size={28} aria-hidden="true" />
          <p>Envio de notificações requer perfil de superadmin.</p>
        </div>
      </section>
    );
  }

  return (
    <section className="admin-notifications">
      <header className="admin-notifications__header">
        <h2>Notificações da plataforma</h2>
        <p>
          Envie para vários usuários de uma vez (seleção nos cards ou lista de e-mails/IDs). Cada
          destinatário recebe sua própria notificação no sino da sidebar.
        </p>
      </header>

      <form className="admin-notifications__form" onSubmit={(event) => void handleSubmit(event)}>
        <label className="admin-notifications__checkbox">
          <input
            type="checkbox"
            checked={broadcast}
            onChange={(event) => setBroadcast(event.target.checked)}
          />
          Notificação geral (todos os usuários ativos)
        </label>

        {!broadcast ? (
          <NotificationRecipientPicker
            adminApi={adminApi}
            selectedUserIds={selectedUserIds}
            extraEmails={extraEmails}
            onChangeSelectedUserIds={setSelectedUserIds}
            onChangeExtraEmails={setExtraEmails}
            disabled={isSubmitting}
          />
        ) : null}

        <div className="admin-notifications__row">
          <label className="admin-notifications__field">
            <span>Categoria</span>
            <select
              value={category}
              onChange={(event) => setCategory(event.target.value as NotificationCategory)}
            >
              {NOTIFICATION_CATEGORIES.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>

          <label className="admin-notifications__field">
            <span>Apresentação</span>
            <select
              value={presentation}
              onChange={(event) =>
                setPresentation(event.target.value as NotificationPresentation)
              }
            >
              {PRESENTATION_MODES.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>

          <label className="admin-notifications__field">
            <span>Tipo visual</span>
            <select value={type} onChange={(event) => setType(event.target.value as NotificationType)}>
              {NOTIFICATION_TYPES.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>
        </div>

        <label className="admin-notifications__field">
          <span>Título (opcional)</span>
          <input value={title} onChange={(event) => setTitle(event.target.value)} maxLength={120} />
        </label>

        {presentation === "template" && selectedTemplate ? (
          <>
            <label className="admin-notifications__field">
              <span>Template</span>
              <select
                value={templateId}
                onChange={(event) => {
                  const nextId = event.target.value as NotificationTemplateId;
                  setTemplateId(nextId);
                  const nextTemplate = NOTIFICATION_TEMPLATE_DEFINITIONS.find(
                    (item) => item.id === nextId,
                  );
                  if (nextTemplate) {
                    const initialVars: Record<string, string> = {};
                    for (const field of nextTemplate.fields) {
                      initialVars[field.key] = templateVars[field.key] ?? "";
                    }
                    setTemplateVars(initialVars);
                  }
                }}
              >
                {NOTIFICATION_TEMPLATE_DEFINITIONS.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.label}
                  </option>
                ))}
              </select>
            </label>

            {selectedTemplate.recipientAutoVars?.includes("userName") ? (
              <p className="admin-notifications__auto-var-hint">
                O nome de cada destinatário é preenchido automaticamente pelo sistema (primeiro
                nome do cadastro).
              </p>
            ) : null}

            {selectedTemplate.fields.map((field) => (
              <label key={field.key} className="admin-notifications__field">
                <span>
                  {field.label}
                  {field.required ? " *" : ""}
                </span>
                <input
                  value={templateVars[field.key] ?? ""}
                  onChange={(event) => updateTemplateVar(field.key, event.target.value)}
                  placeholder={field.placeholder}
                  required={field.required}
                />
              </label>
            ))}

            <div className="admin-notifications__preview">
              <p className="admin-notifications__preview-label">Pré-visualização</p>
              <NotificationCard
                notification={{
                  id: "preview",
                  title: templatePreview?.title ?? null,
                  message: templatePreview?.message ?? "",
                  type,
                  category,
                  presentation: "template",
                  metadata: {
                    templateId,
                    vars: { ...previewRecipientVars, ...templateVars },
                  },
                  read: false,
                  createdAt: new Date().toISOString(),
                  action:
                    actionType === "none"
                      ? null
                      : {
                          type: actionType,
                          label: actionLabel.trim() || "Abrir",
                          target: actionTarget.trim(),
                        },
                }}
                onMarkRead={async () => {}}
              />
            </div>
          </>
        ) : null}

        {presentation === "html" ? (
          <label className="admin-notifications__field">
            <span>HTML personalizado</span>
            <textarea
              value={htmlContent}
              onChange={(event) => setHtmlContent(event.target.value)}
              rows={6}
              required
              placeholder="<p>Olá, <strong>nome</strong>!</p>"
            />
          </label>
        ) : null}

        {presentation === "text" ? (
          <label className="admin-notifications__field">
            <span>Mensagem</span>
            <textarea
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              rows={3}
              required
              maxLength={500}
            />
          </label>
        ) : null}

        <fieldset className="admin-notifications__fieldset">
          <legend>Ação (opcional)</legend>
          <label className="admin-notifications__field">
            <span>Tipo de ação</span>
            <select
              value={actionType}
              onChange={(event) =>
                setActionType(event.target.value as NotificationActionType | "none")
              }
            >
              {ACTION_TYPES.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>

          {actionType !== "none" ? (
            <>
              <label className="admin-notifications__field">
                <span>Rótulo do botão</span>
                <input
                  value={actionLabel}
                  onChange={(event) => setActionLabel(event.target.value)}
                  placeholder="Abrir aplicativo"
                  maxLength={80}
                />
              </label>
              <label className="admin-notifications__field">
                <span>Destino</span>
                <input
                  value={actionTarget}
                  onChange={(event) => setActionTarget(event.target.value)}
                  placeholder={
                    actionType === "portal_route" ? "/apps/minha-delpi-ai" : "https://..."
                  }
                  maxLength={500}
                />
              </label>
            </>
          ) : null}
        </fieldset>

        {feedback ? <p className="admin-notifications__success">{feedback}</p> : null}
        {error ? <p className="admin-notifications__error">{error}</p> : null}

        <button
          type="submit"
          className="admin-notifications__submit"
          disabled={
            isSubmitting ||
            (!broadcast && selectedUserIds.length === 0 && extraEmails.length === 0) ||
            (presentation === "text" && !message.trim()) ||
            (presentation === "html" && !htmlContent.trim()) ||
            (presentation === "template" &&
              (selectedTemplate?.fields.some(
                (field) => field.required && !(templateVars[field.key] ?? "").trim(),
              ) ??
                true))
          }
        >
          {isSubmitting ? "Enviando..." : "Enviar notificações"}
        </button>
      </form>
    </section>
  );
}
