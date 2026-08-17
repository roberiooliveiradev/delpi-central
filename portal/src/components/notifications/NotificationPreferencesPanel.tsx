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
import { Alert, SearchInput, Spinner, Switch } from "../../ui-kit";

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
  const [savingCategory, setSavingCategory] = useState<NotificationCategory | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

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

  const persistMuted = useCallback(
    async (nextMuted: NotificationCategory[], category: NotificationCategory) => {
      const previous = mutedCategories;
      setMutedCategories(nextMuted);
      setSavingCategory(category);
      setError(null);
      try {
        const data = await coreApi.updateNotificationPreferences(nextMuted);
        setMutedCategories(data.mutedCategories);
        if (data.categories.length > 0) {
          setCatalogCategories(data.categories);
        }
        onSaved?.();
      } catch (err) {
        setMutedCategories(previous);
        setError(err instanceof Error ? err.message : "Falha ao salvar preferências");
      } finally {
        setSavingCategory(null);
      }
    },
    [coreApi, mutedCategories, onSaved],
  );

  function handleToggle(category: NotificationCategory, currentlyMuted: boolean) {
    if (savingCategory) return;
    const nextMuted = currentlyMuted
      ? mutedCategories.filter((item) => item !== category)
      : [...mutedCategories, category];
    void persistMuted(nextMuted, category);
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

  const filteredCategories = useMemo(() => {
    const query = searchQuery.trim().toLocaleLowerCase("pt-BR");
    if (!query) return mutableCategories;

    return mutableCategories.filter((category) => {
      const display = resolveNotificationPreferenceDisplay(
        category,
        catalogForLabels,
        appRefs,
      );
      const haystack = [
        display.notificationName,
        display.applicationName,
        category,
      ]
        .join(" ")
        .toLocaleLowerCase("pt-BR");
      return haystack.includes(query);
    });
  }, [mutableCategories, searchQuery, catalogForLabels, appRefs]);

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
            <p>Use o interruptor para silenciar ou voltar a receber cada tipo.</p>
          </div>
        </header>
      ) : (
        <>
          <h2 id="notification-preferences-title" className="visually-hidden">
            Preferências de notificação
          </h2>
          <p className="notification-preferences__intro">
            Ative o interruptor para <strong>silenciar</strong> um tipo. A alteração é salva na
            hora; o histórico anterior permanece na aba Histórico.
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
        <>
          <SearchInput
            className="notification-preferences__search"
            value={searchQuery}
            onChange={(event) => setSearchQuery(event.target.value)}
            onClear={() => setSearchQuery("")}
            placeholder="Buscar por notificação ou aplicativo…"
            aria-label="Buscar preferências de notificação"
          />

          {filteredCategories.length === 0 ? (
            <p className="notification-preferences__empty" role="status">
              Nenhuma preferência encontrada para «{searchQuery.trim()}».
            </p>
          ) : (
            <ul className="notification-preferences__list">
              {filteredCategories.map((category) => {
                const isMuted = mutedCategories.includes(category);
                const isSaving = savingCategory === category;
                const display = resolveNotificationPreferenceDisplay(
                  category,
                  catalogForLabels,
                  appRefs,
                );
                const AppIcon = resolveNotificationCategoryIconComponent(display.iconName);
                return (
                  <li key={category} className="notification-preferences__item">
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
                          {isSaving ? "Salvando…" : isMuted ? "Silenciada" : "Recebendo"}
                        </span>
                      </span>
                    </span>
                    {isSaving ? (
                      <Spinner size={18} label={`Salvando ${display.notificationName}`} />
                    ) : (
                      <Switch
                        className="notification-preferences__switch"
                        checked={isMuted}
                        disabled={Boolean(savingCategory)}
                        onChange={() => handleToggle(category, isMuted)}
                        aria-label={
                          isMuted
                            ? `Voltar a receber: ${display.notificationName}`
                            : `Silenciar: ${display.notificationName}`
                        }
                      />
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </>
      ) : null}
    </section>
  );
}
