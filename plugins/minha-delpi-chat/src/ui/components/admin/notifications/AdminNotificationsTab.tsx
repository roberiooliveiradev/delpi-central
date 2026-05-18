import { FormEvent, useState } from "react";

import {
  dispatchAdminNotifications,
  type NotificationType,
} from "../../../../data/api/coreApi";

import "./AdminNotificationsTab.css";

type AdminNotificationsTabProps = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

const NOTIFICATION_TYPES: NotificationType[] = ["info", "success", "warning", "error"];

export function AdminNotificationsTab({ getAccessToken }: AdminNotificationsTabProps) {
  const [broadcast, setBroadcast] = useState(false);
  const [userIdsText, setUserIdsText] = useState("");
  const [emailsText, setEmailsText] = useState("");
  const [title, setTitle] = useState("");
  const [message, setMessage] = useState("");
  const [type, setType] = useState<NotificationType>("info");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
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

    try {
      const result = await dispatchAdminNotifications(
        {
          broadcast,
          userIds: broadcast ? undefined : userIds,
          emails: broadcast ? undefined : emails,
          title: title.trim() || null,
          message: message.trim(),
          type,
          sourceApp: "minha-delpi-chat-admin",
        },
        { getAccessToken },
      );

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

  return (
    <section className="mdc-admin-notifications">
      <header className="mdc-admin-notifications__header">
        <h2>Notificações</h2>
        <p>
          Envie avisos gerais para todos os usuários ativos ou mensagens direcionadas por ID/e-mail.
        </p>
      </header>

      <form className="mdc-admin-notifications__form" onSubmit={(event) => void handleSubmit(event)}>
        <label className="mdc-admin-notifications__checkbox">
          <input
            type="checkbox"
            checked={broadcast}
            onChange={(event) => setBroadcast(event.target.checked)}
          />
          Notificação geral (broadcast para usuários ativos)
        </label>

        {!broadcast ? (
          <>
            <label>
              IDs de usuário (um por linha ou separados por vírgula)
              <textarea
                value={userIdsText}
                onChange={(event) => setUserIdsText(event.target.value)}
                rows={4}
                placeholder="550e8400-e29b-41d4-a716-446655440000"
              />
            </label>

            <label>
              E-mails (um por linha ou separados por vírgula)
              <textarea
                value={emailsText}
                onChange={(event) => setEmailsText(event.target.value)}
                rows={3}
                placeholder="usuario@empresa.com"
              />
            </label>
          </>
        ) : null}

        <label>
          Título (opcional)
          <input value={title} onChange={(event) => setTitle(event.target.value)} maxLength={120} />
        </label>

        <label>
          Mensagem
          <textarea
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            rows={4}
            required
            maxLength={500}
          />
        </label>

        <label>
          Tipo
          <select value={type} onChange={(event) => setType(event.target.value as NotificationType)}>
            {NOTIFICATION_TYPES.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
        </label>

        {feedback ? <p className="mdc-admin-notifications__success">{feedback}</p> : null}
        {error ? <p className="mdc-admin-notifications__error">{error}</p> : null}

        <button type="submit" disabled={isSubmitting || !message.trim()}>
          {isSubmitting ? "Enviando..." : "Enviar notificações"}
        </button>
      </form>
    </section>
  );
}
