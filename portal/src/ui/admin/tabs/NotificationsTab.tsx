// src/ui/admin/tabs/NotificationsTab.tsx

import { useContext, useMemo, useState, type FormEvent } from "react";
import { Bell } from "lucide-react";

import { AuthContext } from "../../../state/AuthContext";
import { ApiClient } from "../../../data/apiClient";
import {
  CoreApi,
  type DispatchNotificationsPayload,
  type NotificationType,
} from "../../../data/coreApi";

import "./NotificationsTab.css";

const NOTIFICATION_TYPES: NotificationType[] = ["info", "success", "warning", "error"];

export function NotificationsTab() {
  const { getAccessToken, refreshToken, user } = useContext(AuthContext);

  const coreApi = useMemo(
    () =>
      new CoreApi(
        new ApiClient("", getAccessToken, {
          refreshToken: async () => {
            await refreshToken();
            return Boolean(getAccessToken());
          },
        })
      ),
    [getAccessToken, refreshToken]
  );

  const [broadcast, setBroadcast] = useState(false);
  const [userIdsText, setUserIdsText] = useState("");
  const [emailsText, setEmailsText] = useState("");
  const [title, setTitle] = useState("");
  const [message, setMessage] = useState("");
  const [type, setType] = useState<NotificationType>("info");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const isSuperadmin = Boolean(user?.is_superadmin);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();

    if (!isSuperadmin) {
      setError("Apenas superadmin pode enviar notificações.");
      return;
    }

    setIsSubmitting(true);
    setFeedback(null);
    setError(null);

    const userIds = userIdsText
      .split(/[\n,;]+/)
      .map((item) => item.trim())
      .filter(Boolean);

    const emails = emailsText
      .split(/[\n,;]+/)
      .map((item) => item.trim())
      .filter(Boolean);

    const payload: DispatchNotificationsPayload = {
      broadcast,
      userIds: broadcast ? undefined : userIds,
      emails: broadcast ? undefined : emails,
      title: title.trim() || null,
      message: message.trim(),
      type,
      sourceApp: "portal-admin",
    };

    try {
      const result = await coreApi.dispatchNotifications(payload);
      setFeedback(`${result.createdCount} notificação(ões) enviada(s).`);

      if (!broadcast) {
        setUserIdsText("");
        setEmailsText("");
      }

      setMessage("");
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
          Usuários recebem avisos no sino da sidebar do Portal. Envie broadcast para todos os
          usuários ativos ou mensagens por ID/e-mail.
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
          <>
            <label className="admin-notifications__field">
              <span>IDs de usuário</span>
              <textarea
                value={userIdsText}
                onChange={(event) => setUserIdsText(event.target.value)}
                rows={4}
                placeholder="550e8400-e29b-41d4-a716-446655440000"
              />
            </label>

            <label className="admin-notifications__field">
              <span>E-mails</span>
              <textarea
                value={emailsText}
                onChange={(event) => setEmailsText(event.target.value)}
                rows={3}
                placeholder="usuario@empresa.com"
              />
            </label>
          </>
        ) : null}

        <label className="admin-notifications__field">
          <span>Título (opcional)</span>
          <input
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            maxLength={120}
          />
        </label>

        <label className="admin-notifications__field">
          <span>Mensagem</span>
          <textarea
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            rows={4}
            required
            maxLength={500}
          />
        </label>

        <label className="admin-notifications__field">
          <span>Tipo</span>
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

        {feedback ? <p className="admin-notifications__success">{feedback}</p> : null}
        {error ? <p className="admin-notifications__error">{error}</p> : null}

        <button type="submit" className="admin-notifications__submit" disabled={isSubmitting || !message.trim()}>
          {isSubmitting ? "Enviando..." : "Enviar notificações"}
        </button>
      </form>
    </section>
  );
}
