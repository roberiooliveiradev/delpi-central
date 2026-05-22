// src/ui/admin/tabs/NotificationsTab.tsx

import { useContext, useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { Bell, History, Send } from "lucide-react";

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
import { NotificationRoleGroupPicker } from "../../../components/notifications/NotificationRoleGroupPicker";
import {
  buildTemplatePreview,
  resolvePreviewRecipientName,
} from "../../../components/notifications/notificationTemplates";
import { useNotificationTemplates } from "../../../components/notifications/useNotificationTemplates";
import { NotificationDispatchHistory } from "../../../components/notifications/NotificationDispatchHistory";
import {
  snapshotFromDispatchPayload,
  type DispatchFormSnapshot,
} from "../../../components/notifications/dispatchEditForm";

import "./NotificationsTab.css";

type AdminNotificationsView = "send" | "history";

const NOTIFICATION_TYPES: NotificationType[] = ["info", "success", "warning", "error"];

const NOTIFICATION_CATEGORIES: { value: NotificationCategory; label: string }[] = [
  { value: "system", label: "Sistema" },
  { value: "welcome", label: "Boas-vindas" },
  { value: "birthday", label: "Aniversário" },
  { value: "company_event", label: "Evento da empresa" },
  { value: "announcement", label: "Comunicado" },
  { value: "custom", label: "Personalizada" },
  { value: "controle_mp", label: "Controle MP" },
  { value: "transformometro", label: "Transformômetro" },
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
  const [selectedRoleIds, setSelectedRoleIds] = useState<string[]>([]);
  const [selectedGroupIds, setSelectedGroupIds] = useState<string[]>([]);
  const [excludedRoleGroupUserIds, setExcludedRoleGroupUserIds] = useState<string[]>([]);
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
  const [previewUserId, setPreviewUserId] = useState<string | null>(null);
  const [recipientLabels, setRecipientLabels] = useState<
    Record<string, { name: string; email: string }>
  >({});
  const [expiresEnabled, setExpiresEnabled] = useState(false);
  const [expiresInDays, setExpiresInDays] = useState(7);
  const [scheduleEnabled, setScheduleEnabled] = useState(false);
  const [scheduledAtLocal, setScheduledAtLocal] = useState("");
  const [view, setView] = useState<AdminNotificationsView>("send");
  const [editingDispatchId, setEditingDispatchId] = useState<string | null>(null);
  const [loadingEdit, setLoadingEdit] = useState(false);
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

  const previewRecipientName = useMemo(() => {
    if (previewUserId && recipientLabels[previewUserId]) {
      return recipientLabels[previewUserId].name;
    }
    return resolvePreviewRecipientName(user?.name);
  }, [previewUserId, recipientLabels, user?.name]);

  const previewRecipientVars = useMemo(() => {
    if (!selectedTemplate?.recipientAutoVars?.includes("userName")) {
      return undefined;
    }
    return { userName: previewRecipientName };
  }, [selectedTemplate, previewRecipientName]);

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
    : selectedUserIds.length +
      extraEmails.length +
      selectedRoleIds.length +
      selectedGroupIds.length;

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

  function applyFormSnapshot(snapshot: DispatchFormSnapshot) {
    setBroadcast(snapshot.broadcast);
    setSelectedUserIds(snapshot.selectedUserIds);
    setSelectedRoleIds(snapshot.selectedRoleIds);
    setSelectedGroupIds(snapshot.selectedGroupIds);
    setExcludedRoleGroupUserIds(snapshot.excludedRoleGroupUserIds);
    setExtraEmails(snapshot.extraEmails);
    setTitle(snapshot.title);
    setMessage(snapshot.message);
    setType(snapshot.type);
    setCategory(snapshot.category);
    setPresentation(snapshot.presentation);
    setHtmlContent(snapshot.htmlContent);
    setTemplateId(snapshot.templateId);
    setTemplateVars(snapshot.templateVars);
    setActionType(snapshot.actionType);
    setActionLabel(snapshot.actionLabel);
    setActionTarget(snapshot.actionTarget);
    setExpiresEnabled(snapshot.expiresEnabled);
    setExpiresInDays(snapshot.expiresInDays);
    setScheduleEnabled(snapshot.scheduleEnabled);
    setScheduledAtLocal(snapshot.scheduledAtLocal);
  }

  function resetComposeForm() {
    setBroadcast(false);
    setSelectedUserIds([]);
    setSelectedRoleIds([]);
    setSelectedGroupIds([]);
    setExcludedRoleGroupUserIds([]);
    setExtraEmails([]);
    setTitle("");
    setMessage("");
    setType("info");
    setCategory("announcement");
    setPresentation("template");
    setHtmlContent("");
    setTemplateId("welcome_v1");
    setTemplateVars({});
    setActionType("none");
    setActionLabel("");
    setActionTarget("");
    setExpiresEnabled(false);
    setExpiresInDays(7);
    setScheduleEnabled(false);
    setScheduledAtLocal("");
  }

  function cancelEditDispatch() {
    setEditingDispatchId(null);
    setFeedback(null);
    setError(null);
    resetComposeForm();
  }

  async function beginEditDispatch(dispatchId: string) {
    setEditingDispatchId(dispatchId);
    setView("send");
    setLoadingEdit(true);
    setFeedback(null);
    setError(null);

    try {
      const detail = await coreApi.getNotificationDispatch(dispatchId);
      applyFormSnapshot(
        snapshotFromDispatchPayload(detail.payload, detail.scheduledAt),
      );
    } catch (err) {
      setEditingDispatchId(null);
      setError(err instanceof Error ? err.message : "Falha ao carregar agendamento");
    } finally {
      setLoadingEdit(false);
    }
  }

  function buildDispatchPayload(): DispatchNotificationsPayload {
    const isTemplate = presentation === "template";
    const fallbackMessage = isTemplate
      ? templatePreview?.message ?? "Notificação"
      : presentation === "html"
        ? message.trim() || "Notificação em HTML"
        : message.trim();

    return {
      broadcast,
      userIds: broadcast ? undefined : selectedUserIds,
      emails: broadcast ? undefined : extraEmails,
      roleIds: broadcast ? undefined : selectedRoleIds,
      groupIds: broadcast ? undefined : selectedGroupIds,
      excludedUserIds:
        broadcast || (selectedRoleIds.length === 0 && selectedGroupIds.length === 0)
          ? undefined
          : excludedRoleGroupUserIds,
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
      expiresAt: expiresEnabled
        ? new Date(Date.now() + expiresInDays * 24 * 60 * 60 * 1000).toISOString()
        : null,
      scheduledAt:
        scheduleEnabled && scheduledAtLocal
          ? new Date(scheduledAtLocal).toISOString()
          : null,
      sourceApp: "portal-admin",
    };
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

    if (
      !broadcast &&
      selectedUserIds.length === 0 &&
      extraEmails.length === 0 &&
      selectedRoleIds.length === 0 &&
      selectedGroupIds.length === 0
    ) {
      setError(
        "Selecione ao menos um destinatário (usuário, e-mail, papel ou grupo).",
      );
      setIsSubmitting(false);
      return;
    }

    const payload = buildDispatchPayload();

    if (!payload.message && presentation !== "html") {
      setError("Informe a mensagem ou preencha o template.");
      setIsSubmitting(false);
      return;
    }

    if (presentation === "html" && !htmlContent.trim()) {
      setError("Informe o conteúdo HTML.");
      setIsSubmitting(false);
      return;
    }

    const requiresSchedule = Boolean(editingDispatchId) || scheduleEnabled;
    if (requiresSchedule && !scheduledAtLocal) {
      setError("Informe data e hora do agendamento.");
      setIsSubmitting(false);
      return;
    }

    if (editingDispatchId && !scheduleEnabled) {
      setError("O agendamento deve manter data e hora definidas.");
      setIsSubmitting(false);
      return;
    }

    try {
      if (editingDispatchId) {
        const updated = await coreApi.updateScheduledNotificationDispatch(
          editingDispatchId,
          payload,
        );
        setFeedback(
          updated.scheduledAt
            ? `Agendamento atualizado para ${new Date(updated.scheduledAt).toLocaleString("pt-BR")}.`
            : "Agendamento atualizado.",
        );
        setEditingDispatchId(null);
        setView("history");
      } else {
        const result = await coreApi.dispatchNotifications(payload);

        if (result.status === "pending") {
          setFeedback(
            result.scheduledAt
              ? `Envio agendado para ${new Date(result.scheduledAt).toLocaleString("pt-BR")}.`
              : "Envio agendado com sucesso.",
          );
        } else {
          const count = result.createdCount;
          setFeedback(
            count === 1
              ? "1 notificação enviada."
              : `${count} notificações enviadas para ${count} destinatário(s).`,
          );
        }

        if (!broadcast) {
          setSelectedUserIds([]);
          setExtraEmails([]);
        }

        setMessage("");
        setHtmlContent("");
        setScheduleEnabled(false);
        setScheduledAtLocal("");
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : editingDispatchId
            ? "Falha ao atualizar agendamento"
            : "Falha ao enviar notificações",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  const submitDisabled =
    loadingEdit ||
    isSubmitting ||
    (!broadcast &&
      selectedUserIds.length === 0 &&
      extraEmails.length === 0 &&
      selectedRoleIds.length === 0 &&
      selectedGroupIds.length === 0) ||
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

      <nav className="admin-notifications__subnav" aria-label="Seções de notificações">
        <button
          type="button"
          className={
            view === "send"
              ? "admin-notifications__subnav-btn admin-notifications__subnav-btn--active"
              : "admin-notifications__subnav-btn"
          }
          onClick={() => {
            if (editingDispatchId) {
              cancelEditDispatch();
            }
            setView("send");
          }}
        >
          <Send size={16} aria-hidden="true" />
          Novo envio
        </button>
        <button
          type="button"
          className={
            view === "history"
              ? "admin-notifications__subnav-btn admin-notifications__subnav-btn--active"
              : "admin-notifications__subnav-btn"
          }
          onClick={() => setView("history")}
        >
          <History size={16} aria-hidden="true" />
          Histórico
        </button>
      </nav>

      {view === "history" ? (
        <article className="admin-notifications__panel">
          <NotificationDispatchHistory
            coreApi={coreApi}
            onEditDispatch={(dispatchId) => void beginEditDispatch(dispatchId)}
          />
        </article>
      ) : null}

      {view === "send" ? (
      <form className="admin-notifications__form" onSubmit={(event) => void handleSubmit(event)}>
        {editingDispatchId ? (
          <div className="admin-notifications__edit-banner" role="status">
            <p>
              Editando envio agendado. Alterações só entram em vigor após salvar; o envio anterior
              não foi disparado.
            </p>
            <button
              type="button"
              className="admin-notifications__edit-cancel"
              onClick={cancelEditDispatch}
              disabled={isSubmitting}
            >
              Cancelar edição
            </button>
          </div>
        ) : null}
        {loadingEdit ? (
          <p className="admin-notifications__edit-loading">Carregando agendamento…</p>
        ) : null}
        <div className="admin-notifications__shell">
          <article className="admin-notifications__panel">
            <div className="admin-notifications__panel-head">
              <span className="admin-notifications__step" aria-hidden="true">
                1
              </span>
              <div>
                <h3 className="admin-notifications__panel-title">Destinatários</h3>
                <p className="admin-notifications__panel-desc">
                  Abra o seletor de usuários, cole e-mails ou IDs no atalho rápido, ou envie para
                  todos.
                </p>
              </div>
            </div>

            <label className="admin-notifications__toggle admin-notifications__toggle--card">
              <span className="admin-notifications__toggle-control">
                <input
                  type="checkbox"
                  checked={broadcast}
                  onChange={(event) => setBroadcast(event.target.checked)}
                />
              </span>
              <span className="admin-notifications__toggle-text">
                <strong>Notificação geral</strong>
                <span>Todos os usuários ativos da plataforma</span>
              </span>
            </label>

            {!broadcast ? (
              <>
                <NotificationRecipientPicker
                  adminApi={adminApi}
                  selectedUserIds={selectedUserIds}
                  extraEmails={extraEmails}
                  onChangeSelectedUserIds={setSelectedUserIds}
                  onChangeExtraEmails={setExtraEmails}
                  disabled={isSubmitting}
                  previewUserId={previewUserId}
                  onPreviewUserIdChange={setPreviewUserId}
                  onRecipientLabelsChange={setRecipientLabels}
                />
                <NotificationRoleGroupPicker
                  adminApi={adminApi}
                  coreApi={coreApi}
                  selectedRoleIds={selectedRoleIds}
                  selectedGroupIds={selectedGroupIds}
                  excludedUserIds={excludedRoleGroupUserIds}
                  onChangeRoleIds={setSelectedRoleIds}
                  onChangeGroupIds={setSelectedGroupIds}
                  onChangeExcludedUserIds={setExcludedRoleGroupUserIds}
                  disabled={isSubmitting}
                />
              </>
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
                    previewUserName={previewRecipientName}
                    action={actionForPreview}
                  />
                ) : null}

                <fieldset className="admin-notifications__fieldset admin-notifications__fieldset--expires">
                  <legend>Agendamento (opcional)</legend>
                  <label className="admin-notifications__toggle">
                    <span className="admin-notifications__toggle-control">
                      <input
                        type="checkbox"
                        checked={scheduleEnabled}
                        onChange={(event) => setScheduleEnabled(event.target.checked)}
                      />
                    </span>
                    <span className="admin-notifications__toggle-text">
                      <strong>Agendar envio</strong>
                      <span>Processar na data/hora indicada (cron ou botão no histórico)</span>
                    </span>
                  </label>
                  {scheduleEnabled ? (
                    <label className="admin-notifications__field">
                      <span>Data e hora</span>
                      <input
                        type="datetime-local"
                        value={scheduledAtLocal}
                        onChange={(event) => setScheduledAtLocal(event.target.value)}
                        required
                      />
                    </label>
                  ) : null}
                </fieldset>

                <fieldset className="admin-notifications__fieldset admin-notifications__fieldset--expires">
                  <legend>Validade (opcional)</legend>
                  <label className="admin-notifications__toggle">
                    <span className="admin-notifications__toggle-control">
                      <input
                        type="checkbox"
                        checked={expiresEnabled}
                        onChange={(event) => setExpiresEnabled(event.target.checked)}
                      />
                    </span>
                    <span className="admin-notifications__toggle-text">
                      <strong>Expirar automaticamente</strong>
                      <span>Some do sino após o prazo (notificações lidas permanecem no histórico até expirar)</span>
                    </span>
                  </label>
                  {expiresEnabled ? (
                    <label className="admin-notifications__field">
                      <span>Dias até expirar</span>
                      <input
                        type="number"
                        min={1}
                        max={365}
                        value={expiresInDays}
                        onChange={(event) =>
                          setExpiresInDays(Math.max(1, Number(event.target.value) || 1))
                        }
                      />
                    </label>
                  ) : null}
                </fieldset>

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
                {isSubmitting
                  ? editingDispatchId
                    ? "Salvando…"
                    : "Enviando…"
                  : editingDispatchId
                    ? "Salvar agendamento"
                    : scheduleEnabled
                      ? "Agendar envio"
                      : "Enviar notificações"}
              </button>
            </div>
          </footer>
        </div>
      </form>
      ) : null}
    </section>
  );
}
