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
import { useNotificationCatalog } from "../../../state/NotificationCatalogContext";
import { buildNotificationCategoryOptions } from "../../../utils/notificationCatalog";
import { NOTIFICATION_TYPE_OPTIONS } from "../../../utils/notificationSeverityTone";

import {
  Alert,
  Button,
  FormField,
  FormGrid,
  Input,
  Select,
  Spinner,
  Switch,
  Tabs,
  Textarea,
} from "../../../ui-kit";

import "./NotificationsTab.css";

type AdminNotificationsView = "send" | "history";

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
  const { catalog } = useNotificationCatalog();
  const notificationCategories = useMemo(
    () => buildNotificationCategoryOptions(catalog),
    [catalog],
  );

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

      <Tabs
        className="admin-notifications__subnav"
        aria-label="Seções de notificações"
        value={view}
        onChange={(id) => {
          if (id === "send" && editingDispatchId) {
            cancelEditDispatch();
          }
          setView(id as AdminNotificationsView);
        }}
        items={[
          {
            id: "send",
            label: "Novo envio",
            icon: <Send size={16} />,
          },
          {
            id: "history",
            label: "Histórico",
            icon: <Bell size={16} />,
          },
        ]}
      />

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
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={cancelEditDispatch}
              disabled={isSubmitting}
            >
              Cancelar edição
            </Button>
          </div>
        ) : null}
        {loadingEdit ? (
          <Spinner label="Carregando agendamento…" />
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

            <Switch
              className="admin-notifications__toggle admin-notifications__toggle--card"
              checked={broadcast}
              onChange={(event) => setBroadcast(event.target.checked)}
              label={
                <span className="admin-notifications__toggle-text">
                  <strong>Notificação geral</strong>
                  <span>Todos os usuários ativos da plataforma</span>
                </span>
              }
            />

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
                <FormGrid columns={2} className="admin-notifications__row">
                  <FormField label="Categoria" htmlFor="admin-notif-category">
                    <Select
                      id="admin-notif-category"
                      value={category}
                      onChange={(value) => setCategory(value as NotificationCategory)}
                      options={notificationCategories.map((item) => ({
                        value: item.value,
                        label: item.label,
                      }))}
                    />
                  </FormField>

                  <FormField label="Tipo visual" htmlFor="admin-notif-type">
                    <Select
                      id="admin-notif-type"
                      value={type}
                      onChange={(value) => setType(value as NotificationType)}
                      options={NOTIFICATION_TYPE_OPTIONS}
                    />
                  </FormField>
                </FormGrid>

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
                  <Switch
                    className="admin-notifications__toggle"
                    checked={scheduleEnabled}
                    onChange={(event) => setScheduleEnabled(event.target.checked)}
                    label={
                      <span className="admin-notifications__toggle-text">
                        <strong>Agendar envio</strong>
                        <span>Processar na data/hora indicada (cron ou botão no histórico)</span>
                      </span>
                    }
                  />
                  {scheduleEnabled ? (
                    <FormField label="Data e hora" required htmlFor="admin-notif-scheduled-at">
                      <Input
                        id="admin-notif-scheduled-at"
                        type="datetime-local"
                        value={scheduledAtLocal}
                        onChange={(event) => setScheduledAtLocal(event.target.value)}
                        required
                      />
                    </FormField>
                  ) : null}
                </fieldset>

                <fieldset className="admin-notifications__fieldset admin-notifications__fieldset--expires">
                  <legend>Validade (opcional)</legend>
                  <Switch
                    className="admin-notifications__toggle"
                    checked={expiresEnabled}
                    onChange={(event) => setExpiresEnabled(event.target.checked)}
                    label={
                      <span className="admin-notifications__toggle-text">
                        <strong>Expirar automaticamente</strong>
                        <span>Some do sino após o prazo (notificações lidas permanecem no histórico até expirar)</span>
                      </span>
                    }
                  />
                  {expiresEnabled ? (
                    <FormField label="Dias até expirar" htmlFor="admin-notif-expires-days">
                      <Input
                        id="admin-notif-expires-days"
                        type="number"
                        min={1}
                        max={365}
                        value={expiresInDays}
                        onChange={(event) =>
                          setExpiresInDays(Math.max(1, Number(event.target.value) || 1))
                        }
                      />
                    </FormField>
                  ) : null}
                </fieldset>

                {presentation === "html" ? (
                  <FormField label="HTML personalizado" htmlFor="admin-notif-html">
                    <NotificationHtmlEditor
                      value={htmlContent}
                      onChange={setHtmlContent}
                      disabled={isSubmitting}
                    />
                  </FormField>
                ) : null}

                {presentation === "text" || presentation === "html" ? (
                  <>
                    <div className="admin-notifications__field-stack">
                      <FormField label="Título (opcional)" htmlFor="admin-notif-title">
                        <Input
                          id="admin-notif-title"
                          ref={titleRef}
                          value={title}
                          onChange={(event) => setTitle(event.target.value)}
                          maxLength={120}
                        />
                      </FormField>
                      <NotificationVariableToolbar
                        targetRef={titleRef}
                        value={title}
                        onChange={setTitle}
                        scopes={["recipient"]}
                        disabled={isSubmitting}
                      />
                    </div>

                    {presentation === "text" ? (
                      <div className="admin-notifications__field-stack">
                        <FormField label="Mensagem" required htmlFor="admin-notif-message">
                          <Textarea
                            id="admin-notif-message"
                            ref={messageRef}
                            value={message}
                            onChange={(event) => setMessage(event.target.value)}
                            rows={4}
                            required
                            maxLength={500}
                          />
                        </FormField>
                        <NotificationVariableToolbar
                          targetRef={messageRef}
                          value={message}
                          onChange={setMessage}
                          scopes={["recipient"]}
                          disabled={isSubmitting}
                        />
                      </div>
                    ) : (
                      <div className="admin-notifications__field-stack">
                        <FormField
                          label="Mensagem (fallback em texto)"
                          htmlFor="admin-notif-message-fallback"
                        >
                          <Textarea
                            id="admin-notif-message-fallback"
                            ref={messageRef}
                            value={message}
                            onChange={(event) => setMessage(event.target.value)}
                            rows={2}
                            maxLength={500}
                            placeholder="Resumo exibido em clientes sem suporte a HTML"
                          />
                        </FormField>
                        <NotificationVariableToolbar
                          targetRef={messageRef}
                          value={message}
                          onChange={setMessage}
                          scopes={["recipient"]}
                          disabled={isSubmitting}
                        />
                      </div>
                    )}
                  </>
                ) : null}

                <fieldset className="admin-notifications__fieldset">
                  <legend>Ação (opcional)</legend>
                  <div className="admin-notifications__fieldset-grid">
                    <FormField label="Tipo de ação" htmlFor="admin-notif-action-type">
                      <Select
                        id="admin-notif-action-type"
                        value={actionType}
                        onChange={(value) =>
                          setActionType(value as NotificationActionType | "none")
                        }
                        options={ACTION_TYPES.map((item) => ({
                          value: item.value,
                          label: item.label,
                        }))}
                      />
                    </FormField>
                  </div>

                  {actionType !== "none" ? (
                    <FormGrid
                      columns={2}
                      className="admin-notifications__fieldset-grid admin-notifications__fieldset-grid--action"
                    >
                      <FormField label="Rótulo do botão" htmlFor="admin-notif-action-label">
                        <Input
                          id="admin-notif-action-label"
                          value={actionLabel}
                          onChange={(event) => setActionLabel(event.target.value)}
                          placeholder="Abrir aplicativo"
                          maxLength={80}
                        />
                      </FormField>
                      <FormField label="Destino" htmlFor="admin-notif-action-target">
                        <Input
                          id="admin-notif-action-target"
                          value={actionTarget}
                          onChange={(event) => setActionTarget(event.target.value)}
                          placeholder={
                            actionType === "portal_route" ? "/apps/minha-delpi-ai" : "https://..."
                          }
                          maxLength={500}
                        />
                      </FormField>
                    </FormGrid>
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
              {feedback ? <Alert tone="success">{feedback}</Alert> : null}
              {error ? <Alert tone="danger">{error}</Alert> : null}
            </div>

            <div className="admin-notifications__footer-actions">
              <Button
                type="submit"
                variant="primary"
                icon={<Send size={16} />}
                loading={isSubmitting}
                disabled={submitDisabled}
              >
                {isSubmitting
                  ? editingDispatchId
                    ? "Salvando…"
                    : "Enviando…"
                  : editingDispatchId
                    ? "Salvar agendamento"
                    : scheduleEnabled
                      ? "Agendar envio"
                      : "Enviar notificações"}
              </Button>
            </div>
          </footer>
        </div>
      </form>
      ) : null}
    </section>
  );
}
