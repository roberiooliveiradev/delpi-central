// src/ui/admin/tabs/NotificationsTab.tsx

import { useContext, useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { Bell, Send } from "lucide-react";

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
import { AdminNotificationTemplateSection } from "../../../components/notifications/AdminNotificationTemplateSection";
import { NotificationCard } from "../../../components/notifications/NotificationCard";
import { NotificationHtmlEditor } from "../../../components/notifications/NotificationHtmlEditor";
import { NotificationVariableToolbar } from "../../../components/notifications/NotificationVariableToolbar";
import { NotificationRecipientPicker } from "../../../components/notifications/NotificationRecipientPicker";
import {
  buildTemplatePreview,
  resolvePreviewRecipientName,
} from "../../../components/notifications/notificationTemplates";
import { useNotificationTemplates } from "../../../components/notifications/useNotificationTemplates";

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

const PRESENTATION_MODES: {
  value: NotificationPresentation;
  label: string;
  hint: string;
}[] = [
  { value: "text", label: "Texto simples", hint: "Título e mensagem curtos" },
  {
    value: "template",
    label: "Template visual",
    hint: "Cards prontos com variáveis",
  },
  { value: "html", label: "HTML", hint: "Conteúdo rico sanitizado" },
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
  const [presentation, setPresentation] = useState<NotificationPresentation>("template");
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
  const titleRef = useRef<HTMLInputElement>(null);
  const messageRef = useRef<HTMLTextAreaElement>(null);

  const { templates } = useNotificationTemplates(coreApi);

  const selectedTemplate = useMemo(
    () => templates.find((item) => item.id === templateId) ?? null,
    [templates, templateId],
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

  const actionForPreview =
    actionType === "none"
      ? null
      : {
          type: actionType,
          label: actionLabel.trim() || "Abrir",
          target: actionTarget.trim(),
        };

  const recipientCount = broadcast
    ? null
    : selectedUserIds.length + extraEmails.length;

  const showTextPreview =
    presentation === "text" && Boolean(message.trim() || title.trim());

  const showHtmlPreview = presentation === "html" && Boolean(htmlContent.trim() || message.trim());

  const showSidePreview = showTextPreview || showHtmlPreview;

  useEffect(() => {
    if (!selectedTemplate || presentation !== "template") {
      return;
    }
    setCategory(selectedTemplate.category);
    setType(selectedTemplate.defaultType);
  }, [selectedTemplate, presentation]);

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
      : presentation === "html"
        ? message.trim() || "Notificação em HTML"
        : message.trim();

    if (!fallbackMessage && presentation !== "html") {
      setError("Informe a mensagem ou preencha o template.");
      setIsSubmitting(false);
      return;
    }

    if (presentation === "html" && !htmlContent.trim()) {
      setError("Informe o conteúdo HTML.");
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

  const submitDisabled =
    isSubmitting ||
    (!broadcast && selectedUserIds.length === 0 && extraEmails.length === 0) ||
    (presentation === "text" && !message.trim()) ||
    (presentation === "html" && !htmlContent.trim()) ||
    (presentation === "template" &&
      Boolean(
        selectedTemplate?.fields.some(
          (field) => field.required && !(templateVars[field.key] ?? "").trim(),
        ),
      ));

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
        <div className="admin-notifications__header-icon" aria-hidden="true">
          <Bell size={24} />
        </div>
        <div className="admin-notifications__header-text">
          <h2>Notificações da plataforma</h2>
          <p>
            Envie para vários usuários de uma vez. Cada destinatário recebe sua própria
            notificação no sino da sidebar, com variáveis preenchidas automaticamente quando
            aplicável.
          </p>
        </div>
      </header>

      <form className="admin-notifications__form" onSubmit={(event) => void handleSubmit(event)}>
        <div className="admin-notifications__shell">
          <article className="admin-notifications__panel">
            <div className="admin-notifications__panel-head">
              <span className="admin-notifications__step" aria-hidden="true">
                1
              </span>
              <div>
                <h3 className="admin-notifications__panel-title">Destinatários</h3>
                <p className="admin-notifications__panel-desc">
                  Escolha usuários nos cards, cole e-mails ou IDs, ou envie para todos.
                </p>
              </div>
            </div>

            <label className="admin-notifications__broadcast">
              <input
                type="checkbox"
                checked={broadcast}
                onChange={(event) => setBroadcast(event.target.checked)}
              />
              <span className="admin-notifications__broadcast-body">
                <strong>Notificação geral</strong>
                <span>Todos os usuários ativos da plataforma</span>
              </span>
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
          </article>

          <article className="admin-notifications__panel admin-notifications__panel--muted">
            <div className="admin-notifications__panel-head">
              <span className="admin-notifications__step" aria-hidden="true">
                2
              </span>
              <div>
                <h3 className="admin-notifications__panel-title">Conteúdo e apresentação</h3>
                <p className="admin-notifications__panel-desc">
                  Defina o formato visual e os campos da mensagem.
                </p>
              </div>
            </div>

            <div className="admin-notifications__modes" role="group" aria-label="Apresentação">
              <span className="admin-notifications__modes-label">Formato</span>
              <div className="admin-notifications__modes-row">
                {PRESENTATION_MODES.map((item) => (
                  <button
                    key={item.value}
                    type="button"
                    className={
                      presentation === item.value
                        ? "admin-notifications__mode admin-notifications__mode--active"
                        : "admin-notifications__mode"
                    }
                    onClick={() => setPresentation(item.value)}
                    aria-pressed={presentation === item.value}
                  >
                    <strong>{item.label}</strong>
                    <span>{item.hint}</span>
                  </button>
                ))}
              </div>
            </div>

            <div
              className={
                showSidePreview
                  ? "admin-notifications__main-grid admin-notifications__main-grid--with-preview"
                  : "admin-notifications__main-grid"
              }
            >
              <div className="admin-notifications__main-grid-content">
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
                    <span>Tipo visual</span>
                    <select
                      value={type}
                      onChange={(event) => setType(event.target.value as NotificationType)}
                    >
                      {NOTIFICATION_TYPES.map((item) => (
                        <option key={item} value={item}>
                          {item}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>

                {presentation === "template" ? (
                  <AdminNotificationTemplateSection
                    coreApi={coreApi}
                    templateId={templateId}
                    onTemplateIdChange={setTemplateId}
                    templateVars={templateVars}
                    onTemplateVarsChange={setTemplateVars}
                    category={category}
                    type={type}
                    previewUserName={user?.name}
                    action={actionForPreview}
                  />
                ) : null}

                {presentation === "html" ? (
                  <label className="admin-notifications__field">
                    <span>HTML personalizado</span>
                    <NotificationHtmlEditor
                      value={htmlContent}
                      onChange={setHtmlContent}
                      disabled={isSubmitting}
                    />
                  </label>
                ) : null}

                {presentation === "text" || presentation === "html" ? (
                  <>
                    <label className="admin-notifications__field">
                      <span>Título (opcional)</span>
                      <input
                        ref={titleRef}
                        value={title}
                        onChange={(event) => setTitle(event.target.value)}
                        maxLength={120}
                      />
                      <NotificationVariableToolbar
                        targetRef={titleRef}
                        value={title}
                        onChange={setTitle}
                        scopes={["recipient"]}
                        disabled={isSubmitting}
                      />
                    </label>

                    {presentation === "text" ? (
                      <label className="admin-notifications__field">
                        <span>Mensagem</span>
                        <textarea
                          ref={messageRef}
                          value={message}
                          onChange={(event) => setMessage(event.target.value)}
                          rows={4}
                          required
                          maxLength={500}
                        />
                        <NotificationVariableToolbar
                          targetRef={messageRef}
                          value={message}
                          onChange={setMessage}
                          scopes={["recipient"]}
                          disabled={isSubmitting}
                        />
                      </label>
                    ) : (
                      <label className="admin-notifications__field">
                        <span>Mensagem (fallback em texto)</span>
                        <textarea
                          ref={messageRef}
                          value={message}
                          onChange={(event) => setMessage(event.target.value)}
                          rows={2}
                          maxLength={500}
                          placeholder="Resumo exibido em clientes sem suporte a HTML"
                        />
                        <NotificationVariableToolbar
                          targetRef={messageRef}
                          value={message}
                          onChange={setMessage}
                          scopes={["recipient"]}
                          disabled={isSubmitting}
                        />
                      </label>
                    )}
                  </>
                ) : null}

                <fieldset className="admin-notifications__fieldset">
                  <legend>Ação (opcional)</legend>
                  <div className="admin-notifications__fieldset-grid">
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
                  </div>

                  {actionType !== "none" ? (
                    <div className="admin-notifications__fieldset-grid admin-notifications__fieldset-grid--action">
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
                    </div>
                  ) : null}
                </fieldset>
              </div>

              {showTextPreview ? (
                <aside
                  className="admin-notifications__preview admin-notifications__preview--sticky"
                  aria-label="Pré-visualização"
                >
                  <p className="admin-notifications__preview-label">Pré-visualização</p>
                  <NotificationCard
                    notification={{
                      id: "preview",
                      title: title.trim() || null,
                      message: message.trim() || "…",
                      type,
                      category,
                      presentation: "text",
                      read: false,
                      createdAt: new Date().toISOString(),
                      action: actionForPreview,
                    }}
                    onMarkRead={async () => {}}
                  />
                </aside>
              ) : null}

              {showHtmlPreview ? (
                <aside
                  className="admin-notifications__preview admin-notifications__preview--sticky"
                  aria-label="Pré-visualização"
                >
                  <p className="admin-notifications__preview-label">Pré-visualização</p>
                  <NotificationCard
                    notification={{
                      id: "preview",
                      title: title.trim() || null,
                      message: message.trim() || "Notificação em HTML",
                      type,
                      category,
                      presentation: "html",
                      htmlContent,
                      read: false,
                      createdAt: new Date().toISOString(),
                      action: actionForPreview,
                    }}
                    onMarkRead={async () => {}}
                  />
                </aside>
              ) : null}
            </div>
          </article>

          <footer className="admin-notifications__footer">
            <div className="admin-notifications__footer-meta">
              <strong>
                {broadcast
                  ? "Envio para todos os usuários ativos"
                  : recipientCount === 0
                    ? "Nenhum destinatário selecionado"
                    : recipientCount === 1
                      ? "1 destinatário selecionado"
                      : `${recipientCount} destinatários selecionados`}
              </strong>
              <span>
                {presentation === "template"
                  ? "Modo template visual"
                  : presentation === "html"
                    ? "Modo HTML sanitizado"
                    : "Modo texto simples"}
              </span>
              {feedback ? (
                <p className="admin-notifications__alert admin-notifications__alert--success">
                  {feedback}
                </p>
              ) : null}
              {error ? (
                <p className="admin-notifications__alert admin-notifications__alert--error">
                  {error}
                </p>
              ) : null}
            </div>

            <div className="admin-notifications__footer-actions">
              <button
                type="submit"
                className="admin-notifications__submit"
                disabled={submitDisabled}
              >
                <Send size={16} aria-hidden="true" />
                {isSubmitting ? "Enviando…" : "Enviar notificações"}
              </button>
            </div>
          </footer>
        </div>
      </form>
    </section>
  );
}
