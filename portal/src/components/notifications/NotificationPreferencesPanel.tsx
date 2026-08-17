import { useCallback, useContext, useEffect, useMemo, useState } from "react";
import { Settings2 } from "lucide-react";

import { AuthContext } from "../../state/AuthContext";
import { ApiClient } from "../../data/apiClient";
import { CoreApi, type NotificationCategory, type NotificationCatalogCategoryItem } from "../../data/coreApi";
import {
  resolveNotificationCategoryIconComponent,
  resolveNotificationPreferenceDisplay,
} from "../../utils/notificationCatalog";
import { useNotificationCatalog } from "../../state/NotificationCatalogContext";
import { Alert, Button, Checkbox, Spinner } from "../../ui-kit";

import "./NotificationPreferencesPanel.css";

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
  const { getAccessToken, refreshToken, apps } = useContext(AuthContext);
  const { catalog } = useNotificationCatalog();

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
  const [catalogCategories, setCatalogCategories] = useState<NotificationCatalogCategoryItem[]>(
    catalog.categories,
  );
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
      if (data.categories.length > 0) {
        setCatalogCategories(data.categories);
      }
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
      if (data.categories.length > 0) {
        setCatalogCategories(data.categories);
      }
      setSaved(true);
      onSaved?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao salvar preferências");
    } finally {
      setSaving(false);
    }
  }

  const catalogForLabels = useMemo(
    () => ({
      version: catalog.version,
      categories: catalogCategories.length > 0 ? catalogCategories : catalog.categories,
    }),
    [catalog.version, catalog.categories, catalogCategories],
  );

  const appRefs = useMemo(
    () => apps.map((app) => ({ id: app.id, name: app.name, icon: app.icon })),
    [apps],
  );

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

      {loading ? <Spinner label="Carregando…" /> : null}
      {error ? <Alert tone="danger">{error}</Alert> : null}

      {!loading ? (
        <ul className="notification-preferences__list">
          {mutableCategories.map((category) => {
            const isMuted = mutedCategories.includes(category);
            const display = resolveNotificationPreferenceDisplay(
              category,
              catalogForLabels,
              appRefs,
            );
            const AppIcon = resolveNotificationCategoryIconComponent(display.iconName);
            return (
              <li key={category}>
                <Checkbox
                  className="notification-preferences__item"
                  checked={isMuted}
                  onChange={() => toggleCategory(category)}
                  label={
                    <span className="notification-preferences__body">
                      <span className="notification-preferences__app-icon" aria-hidden="true">
                        <AppIcon size={18} />
                      </span>
                      <span className="notification-preferences__copy">
                        <span className="notification-preferences__label">
                          {display.notificationName}
                        </span>
                        <span className="notification-preferences__app">
                          {display.applicationName}
                        </span>
                        <span className="notification-preferences__hint">
                          {isMuted ? "Silenciada" : "Recebendo"}
                        </span>
                      </span>
                    </span>
                  }
                />
              </li>
            );
          })}
        </ul>
      ) : null}

      <footer className="notification-preferences__footer">
        {saved ? <span className="notification-preferences__saved">Preferências salvas.</span> : null}
        <Button
          type="button"
          variant="primary"
          disabled={loading || saving}
          loading={saving}
          onClick={() => void handleSave()}
        >
          {saving ? "Salvando…" : "Salvar preferências"}
        </Button>
      </footer>
    </section>
  );
}
