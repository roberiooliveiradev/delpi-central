import { useCallback, useContext, useEffect, useMemo, useState } from "react";
import { Bell, BellOff, Settings2, Star } from "lucide-react";

import { AuthContext } from "../../state/AuthContext";
import { ApiClient } from "../../data/apiClient";
import { CoreApi, type NotificationCategory, type NotificationCatalogCategoryItem } from "../../data/coreApi";
import {
  resolveNotificationCategoryIconComponent,
  resolveNotificationPreferenceDisplay,
} from "../../utils/notificationCatalog";
import { useNotificationCatalog } from "../../state/NotificationCatalogContext";
import { Alert, Button, SearchInput, Spinner } from "../../ui-kit";

import "./NotificationPreferencesPanel.css";

type Props = {
  coreApi?: CoreApi;
  onSaved?: () => void;
  variant?: "embedded" | "page";
};

function preferenceStatusLabel(
  isImportant: boolean,
  isMuted: boolean,
  isSaving: boolean,
): string {
  if (isSaving) return "Salvando…";
  if (isImportant) return "Importante";
  if (isMuted) return "Silenciada";
  return "Recebendo";
}

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
  const [importantCategories, setImportantCategories] = useState<NotificationCategory[]>([]);
  const [catalogCategories, setCatalogCategories] = useState<NotificationCatalogCategoryItem[]>(
    catalog.categories,
  );
  const [loading, setLoading] = useState(true);
  const [savingCategory, setSavingCategory] = useState<NotificationCategory | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const applyPreferencesResponse = useCallback(
    (data: {
      mutedCategories: NotificationCategory[];
      importantCategories: NotificationCategory[];
      categories: NotificationCatalogCategoryItem[];
    }) => {
      setMutedCategories(data.mutedCategories);
      setImportantCategories(data.importantCategories);
      if (data.categories.length > 0) {
        setCatalogCategories(data.categories);
      }
    },
    [],
  );

  const loadPreferences = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await coreApi.getNotificationPreferences();
      setMutableCategories(data.mutableCategories);
      applyPreferencesResponse(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar preferências");
    } finally {
      setLoading(false);
    }
  }, [applyPreferencesResponse, coreApi]);

  useEffect(() => {
    void loadPreferences();
  }, [loadPreferences]);

  const persistPreferences = useCallback(
    async (
      nextMuted: NotificationCategory[],
      nextImportant: NotificationCategory[],
      category: NotificationCategory,
    ) => {
      const previousMuted = mutedCategories;
      const previousImportant = importantCategories;
      setMutedCategories(nextMuted);
      setImportantCategories(nextImportant);
      setSavingCategory(category);
      setError(null);
      try {
        const data = await coreApi.updateNotificationPreferences(nextMuted, nextImportant);
        applyPreferencesResponse(data);
        onSaved?.();
      } catch (err) {
        setMutedCategories(previousMuted);
        setImportantCategories(previousImportant);
        setError(err instanceof Error ? err.message : "Falha ao salvar preferências");
      } finally {
        setSavingCategory(null);
      }
    },
    [applyPreferencesResponse, coreApi, importantCategories, mutedCategories, onSaved],
  );

  function handleToggleMute(category: NotificationCategory, currentlyMuted: boolean) {
    if (savingCategory) return;
    if (currentlyMuted) {
      void persistPreferences(
        mutedCategories.filter((item) => item !== category),
        importantCategories,
        category,
      );
      return;
    }
    void persistPreferences(
      [...mutedCategories.filter((item) => item !== category), category],
      importantCategories.filter((item) => item !== category),
      category,
    );
  }

  function handleToggleImportant(category: NotificationCategory, currentlyImportant: boolean) {
    if (savingCategory) return;
    if (currentlyImportant) {
      void persistPreferences(
        mutedCategories,
        importantCategories.filter((item) => item !== category),
        category,
      );
      return;
    }
    void persistPreferences(
      mutedCategories.filter((item) => item !== category),
      [...importantCategories.filter((item) => item !== category), category],
      category,
    );
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
    const accessiblePluginIds = new Set(
      apps.map((app) => app.id.trim().toLowerCase()).filter(Boolean),
    );

    const accessibleMutable = mutableCategories.filter((category) => {
      const spec = catalogForLabels.categories.find((item) => item.id === category);
      const kind = (spec?.kind || "platform").toLowerCase();
      if (kind !== "app") return true;
      const pluginId = (spec?.pluginId || "").trim().toLowerCase();
      return Boolean(pluginId && accessiblePluginIds.has(pluginId));
    });

    const query = searchQuery.trim().toLocaleLowerCase("pt-BR");
    if (!query) return accessibleMutable;

    return accessibleMutable.filter((category) => {
      const display = resolveNotificationPreferenceDisplay(
        category,
        catalogForLabels,
        appRefs,
      );
      const haystack = [display.notificationName, display.applicationName, category]
        .join(" ")
        .toLocaleLowerCase("pt-BR");
      return haystack.includes(query);
    });
  }, [mutableCategories, searchQuery, catalogForLabels, appRefs, apps]);

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
            <p>
              Estrela marca como importante; sino silencia. A alteração é salva na hora.
            </p>
          </div>
        </header>
      ) : (
        <>
          <h2 id="notification-preferences-title" className="visually-hidden">
            Preferências de notificação
          </h2>
          <p className="notification-preferences__intro">
            Use a <strong>estrela</strong> para alertas persistentes na tela e o{" "}
            <strong>sino</strong> para silenciar. Importante e silêncio não se combinam; a
            alteração é salva na hora. O histórico anterior permanece na aba Histórico.
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
                const isImportant = importantCategories.includes(category);
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
                          {preferenceStatusLabel(isImportant, isMuted, isSaving)}
                        </span>
                      </span>
                    </span>
                    {isSaving ? (
                      <Spinner size={18} label={`Salvando ${display.notificationName}`} />
                    ) : (
                      <span className="notification-preferences__actions">
                        <Button
                          type="button"
                          variant={isImportant ? "primary" : "ghost"}
                          size="sm"
                          className={[
                            "notification-preferences__important",
                            isImportant
                              ? "notification-preferences__important--on"
                              : "notification-preferences__important--off",
                          ].join(" ")}
                          pressed={isImportant}
                          disabled={Boolean(savingCategory)}
                          onClick={() => handleToggleImportant(category, isImportant)}
                          aria-label={
                            isImportant
                              ? `Remover importante: ${display.notificationName}`
                              : `Marcar como importante: ${display.notificationName}`
                          }
                          title={
                            isImportant
                              ? `Importante — ${display.notificationName}. Clique para remover.`
                              : `Marcar como importante — ${display.notificationName}.`
                          }
                          icon={<Star size={18} fill={isImportant ? "currentColor" : "none"} />}
                        />
                        <Button
                          type="button"
                          variant={isMuted ? "danger-soft" : "ghost"}
                          size="sm"
                          className={[
                            "notification-preferences__mute",
                            isMuted
                              ? "notification-preferences__mute--silenced"
                              : "notification-preferences__mute--receiving",
                          ].join(" ")}
                          pressed={isMuted}
                          disabled={Boolean(savingCategory)}
                          onClick={() => handleToggleMute(category, isMuted)}
                          aria-label={
                            isMuted
                              ? `Voltar a receber: ${display.notificationName}`
                              : `Silenciar: ${display.notificationName}`
                          }
                          title={
                            isMuted
                              ? `Silenciada — ${display.notificationName}. Clique para voltar a receber.`
                              : `Recebendo — ${display.notificationName}. Clique para silenciar.`
                          }
                          icon={
                            <span
                              className="notification-preferences__mute-icons"
                              data-muted={isMuted ? "true" : "false"}
                              aria-hidden="true"
                            >
                              <Bell
                                size={18}
                                className="notification-preferences__mute-icon notification-preferences__mute-icon--bell"
                              />
                              <BellOff
                                size={18}
                                className="notification-preferences__mute-icon notification-preferences__mute-icon--off"
                              />
                            </span>
                          }
                        />
                      </span>
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
