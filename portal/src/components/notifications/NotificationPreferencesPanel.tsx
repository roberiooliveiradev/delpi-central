import { useCallback, useContext, useEffect, useMemo, useState } from "react";
import { Settings2 } from "lucide-react";

import { AuthContext } from "../../state/AuthContext";
import { ApiClient } from "../../data/apiClient";
import { CoreApi, type NotificationCategory } from "../../data/coreApi";

import "./NotificationPreferencesPanel.css";

const CATEGORY_LABELS: Record<NotificationCategory, string> = {
  system: "Sistema",
  welcome: "Boas-vindas",
  birthday: "Aniversário",
  company_event: "Evento",
  announcement: "Comunicado",
  access: "Acesso",
  custom: "Personalizada",
  controle_mp: "Controle MP",
};

type Props = {
  coreApi?: CoreApi;
  onSaved?: () => void;
  variant?: "embedded" | "page";
};

export function NotificationPreferencesPanel({
  coreApi: coreApiProp,
  onSaved,
  variant = "embedded",
}: Props) {
  const { getAccessToken, refreshToken } = useContext(AuthContext);

  const coreApi = useMemo(() => {
    if (coreApiProp) {
      return coreApiProp;
    }
    return new CoreApi(
      new ApiClient("", getAccessToken, {
        refreshToken: async () => {
          await refreshToken();
          return Boolean(getAccessToken());
        },
      }),
    );
  }, [coreApiProp, getAccessToken, refreshToken]);

  const [mutableCategories, setMutableCategories] = useState<NotificationCategory[]>([]);
  const [mutedCategories, setMutedCategories] = useState<NotificationCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  const loadPreferences = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await coreApi.getNotificationPreferences();
      setMutableCategories(data.mutableCategories);
      setMutedCategories(data.mutedCategories);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar preferências");
    } finally {
      setLoading(false);
    }
  }, [coreApi]);

  useEffect(() => {
    void loadPreferences();
  }, [loadPreferences]);

  function toggleCategory(category: NotificationCategory) {
    setSaved(false);
    setMutedCategories((current) =>
      current.includes(category)
        ? current.filter((item) => item !== category)
        : [...current, category],
    );
  }

  async function handleSave() {
    setSaving(true);
    setError(null);
    setSaved(false);
    try {
      const data = await coreApi.updateNotificationPreferences(mutedCategories);
      setMutedCategories(data.mutedCategories);
      setSaved(true);
      onSaved?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao salvar preferências");
    } finally {
      setSaving(false);
    }
  }

  const rootClassName =
    variant === "page"
      ? "notification-preferences notification-preferences--page"
      : "notification-preferences";

  return (
    <section className={rootClassName} aria-labelledby="notification-preferences-title">
      {variant === "embedded" ? (
        <header className="notification-preferences__header">
          <Settings2 size={18} aria-hidden="true" />
          <div>
            <h2 id="notification-preferences-title">Preferências</h2>
            <p>Escolha quais tipos de mensagem você não deseja receber.</p>
          </div>
        </header>
      ) : (
        <>
          <h2 id="notification-preferences-title" className="visually-hidden">
            Preferências de notificação
          </h2>
          <p className="notification-preferences__intro">
            Marque as categorias que deseja <strong>silenciar</strong>. Você deixa de receber novos
            envios desses tipos; o histórico anterior permanece disponível na aba Histórico.
          </p>
        </>
      )}

      <p className="notification-preferences__note">
        Notificações de <strong>sistema</strong> não podem ser desativadas (segurança e avisos
        críticos).
      </p>

      {loading ? <p className="notification-preferences__loading">Carregando…</p> : null}
      {error ? <p className="notification-preferences__error">{error}</p> : null}

      {!loading ? (
        <ul className="notification-preferences__list">
          {mutableCategories.map((category) => {
            const isMuted = mutedCategories.includes(category);
            return (
              <li key={category}>
                <label className="notification-preferences__item">
                  <input
                    type="checkbox"
                    checked={isMuted}
                    onChange={() => toggleCategory(category)}
                  />
                  <span>
                    <span className="notification-preferences__label">
                      {CATEGORY_LABELS[category]}
                    </span>
                    <span className="notification-preferences__hint">
                      {isMuted ? "Silenciada — não receberá novos envios" : "Recebendo"}
                    </span>
                  </span>
                </label>
              </li>
            );
          })}
        </ul>
      ) : null}

      <footer className="notification-preferences__footer">
        {saved ? <span className="notification-preferences__saved">Preferências salvas.</span> : null}
        <button
          type="button"
          className="notification-preferences__save"
          disabled={loading || saving}
          onClick={() => void handleSave()}
        >
          {saving ? "Salvando…" : "Salvar preferências"}
        </button>
      </footer>
    </section>
  );
}
