import { useCallback, useContext, useEffect, useMemo, useState } from "react";
import { Bell, BellOff, Mail, Settings2, Star } from "lucide-react";

import { AuthContext } from "../../state/AuthContext";
import { ApiClient } from "../../data/apiClient";
import { CoreApi, type NotificationCategory, type NotificationCatalogCategoryItem } from "../../data/coreApi";
import {
  resolveNotificationCategoryIconComponent,
  resolveNotificationPreferenceDisplay,
} from "../../utils/notificationCatalog";
import { useNotificationCatalog } from "../../state/NotificationCatalogContext";
import { Alert, Button, SearchInput, Spinner } from "../../ui-kit";
import {
  DESKTOP_TOASTS_ENABLED_KEY,
  getDesktopNotificationPermission,
  isDesktopNotificationSupported,
  isDesktopToastsEnabled,
  requestDesktopNotificationPermission,
  setDesktopToastsEnabled,
} from "../../utils/desktopNotificationToast";

import "./NotificationPreferencesPanel.css";

type Props = {
  coreApi?: CoreApi;
  onSaved?: () => void;
  variant?: "embedded" | "page";
};

function preferenceStatusLabel(
  isImportant: boolean,
  isMuted: boolean,
  isEmail: boolean,
  isSaving: boolean,
): string {
  if (isSaving) return "Salvando…";
  if (isMuted) return "Silenciada";
  if (isImportant) return "Importante";
  if (isEmail) return "E-mail";
  return "Recebendo";
}

function desktopToastStatusLabel(
  supported: boolean,
  enabled: boolean,
  permission: NotificationPermission | "unsupported",
): string {
  if (!supported || permission === "unsupported") return "Não suportados neste navegador";
  if (permission === "denied") return "Bloqueados pelo navegador";
  if (permission === "granted" && enabled) return "Ativados";
  if (permission === "granted") return "Permissão concedida (toasts desativados)";
  return "Não solicitados";
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
  const [emailCategories, setEmailCategories] = useState<NotificationCategory[]>([]);
  const [catalogCategories, setCatalogCategories] = useState<NotificationCatalogCategoryItem[]>(
    catalog.categories,
  );
  const [loading, setLoading] = useState(true);
  const [savingCategory, setSavingCategory] = useState<NotificationCategory | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [desktopSupported] = useState(() => isDesktopNotificationSupported());
  const [desktopEnabled, setDesktopEnabled] = useState(() => isDesktopToastsEnabled());
  const [desktopPermission, setDesktopPermission] = useState<NotificationPermission | "unsupported">(
    () => getDesktopNotificationPermission(),
  );

  const applyPreferencesResponse = useCallback(
    (data: {
      mutedCategories: NotificationCategory[];
      importantCategories: NotificationCategory[];
      emailCategories: NotificationCategory[];
      categories: NotificationCatalogCategoryItem[];
    }) => {
      setMutedCategories(data.mutedCategories);
      setImportantCategories(data.importantCategories);
      setEmailCategories(data.emailCategories);
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

  useEffect(() => {
    const onStorage = (event: StorageEvent) => {
      if (event.key === DESKTOP_TOASTS_ENABLED_KEY) {
        setDesktopEnabled(isDesktopToastsEnabled());
      }
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const persistPreferences = useCallback(
    async (
      nextMuted: NotificationCategory[],
      nextImportant: NotificationCategory[],
      nextEmail: NotificationCategory[],
      category: NotificationCategory,
    ) => {
      const previousMuted = mutedCategories;
      const previousImportant = importantCategories;
      const previousEmail = emailCategories;
      setMutedCategories(nextMuted);
      setImportantCategories(nextImportant);
      setEmailCategories(nextEmail);
      setSavingCategory(category);
      setError(null);
      try {
        const data = await coreApi.updateNotificationPreferences(
          nextMuted,
          nextImportant,
          nextEmail,
        );
        applyPreferencesResponse(data);
        onSaved?.();
      } catch (err) {
        setMutedCategories(previousMuted);
        setImportantCategories(previousImportant);
        setEmailCategories(previousEmail);
        setError(err instanceof Error ? err.message : "Falha ao salvar preferências");
      } finally {
        setSavingCategory(null);
      }
    },
    [
      applyPreferencesResponse,
      coreApi,
      emailCategories,
      importantCategories,
      mutedCategories,
      onSaved,
    ],
  );

  function handleToggleMute(category: NotificationCategory, currentlyMuted: boolean) {
    if (savingCategory) return;
    if (currentlyMuted) {
      void persistPreferences(
        mutedCategories.filter((item) => item !== category),
        importantCategories,
        emailCategories,
        category,
      );
      return;
    }
    void persistPreferences(
      [...mutedCategories.filter((item) => item !== category), category],
      importantCategories.filter((item) => item !== category),
      emailCategories.filter((item) => item !== category),
      category,
    );
  }

  function handleToggleImportant(category: NotificationCategory, currentlyImportant: boolean) {
    if (savingCategory) return;
    if (currentlyImportant) {
      void persistPreferences(
        mutedCategories,
        importantCategories.filter((item) => item !== category),
        emailCategories,
        category,
      );
      return;
    }
    void persistPreferences(
      mutedCategories.filter((item) => item !== category),
      [...importantCategories.filter((item) => item !== category), category],
      emailCategories.filter((item) => item !== category),
      category,
    );
  }

  function handleToggleEmail(category: NotificationCategory, currentlyEmail: boolean) {
    if (savingCategory) return;
    if (currentlyEmail) {
      void persistPreferences(
        mutedCategories,
        importantCategories,
        emailCategories.filter((item) => item !== category),
        category,
      );
      return;
    }
    void persistPreferences(
      mutedCategories.filter((item) => item !== category),
      importantCategories,
      [...emailCategories.filter((item) => item !== category), category],
      category,
    );
  }

  async function handleEnableDesktopToasts() {
    setError(null);
    const permission = await requestDesktopNotificationPermission();
    setDesktopPermission(permission);
    if (permission === "granted") {
      setDesktopToastsEnabled(true);
      setDesktopEnabled(true);
      return;
    }
    if (permission === "denied") {
      setDesktopToastsEnabled(false);
      setDesktopEnabled(false);
      setError(
        "O navegador bloqueou alertas do sistema. Libere a permissão nas configurações do site.",
      );
      return;
    }
    setError("Não foi possível ativar os alertas do sistema neste navegador.");
  }

  function handleDisableDesktopToasts() {
    setDesktopToastsEnabled(false);
    setDesktopEnabled(false);
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

  const toastStatus = desktopToastStatusLabel(desktopSupported, desktopEnabled, desktopPermission);

  return (
    <section className={rootClassName} aria-labelledby="notification-preferences-title">
      {variant === "embedded" ? (
        <header className="notification-preferences__header">
          <Settings2 size={18} aria-hidden="true" />
          <div>
            <h2 id="notification-preferences-title">Preferências</h2>
            <p>
              Estrela (importante), sino (silêncio) e envelope (e-mail). A alteração é salva na
              hora.
            </p>
          </div>
        </header>
      ) : (
        <>
          <h2 id="notification-preferences-title" className="visually-hidden">
            Preferências de notificação
          </h2>
          <p className="notification-preferences__intro">
            Use a <strong>estrela</strong> para alertas na tela e e-mail automático, o{" "}
            <strong>envelope</strong> para e-mail opt-in e o <strong>sino</strong> para silenciar.
            Silêncio remove os demais canais daquele tipo; a alteração é salva na hora.
          </p>
        </>
      )}

      <div
        className="notification-preferences__desktop"
        data-tour="notification-pref-desktop-toasts"
      >
        <div className="notification-preferences__desktop-copy">
          <h3 className="notification-preferences__desktop-title">
            Alertas do sistema (Windows / macOS / Linux)
          </h3>
          <p className="notification-preferences__desktop-status">Status: {toastStatus}</p>
          <p className="notification-preferences__desktop-hint">
            Com a Minha DELPI aberta, novas notificações também aparecem como toast do sistema
            operacional.
          </p>
        </div>
        <div className="notification-preferences__desktop-actions">
          {desktopSupported && desktopPermission === "granted" && desktopEnabled ? (
            <Button type="button" variant="ghost" size="sm" onClick={handleDisableDesktopToasts}>
              Desativar toasts
            </Button>
          ) : (
            <Button
              type="button"
              variant="primary"
              size="sm"
              disabled={!desktopSupported || desktopPermission === "denied"}
              onClick={() => void handleEnableDesktopToasts()}
            >
              Ativar alertas do sistema
            </Button>
          )}
        </div>
      </div>

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
                const isEmail = emailCategories.includes(category) || isImportant;
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
                          {preferenceStatusLabel(
                            isImportant,
                            isMuted,
                            emailCategories.includes(category),
                            isSaving,
                          )}
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
                          data-tour="notification-pref-important"
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
                          data-tour="notification-pref-mute"
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
                        <Button
                          type="button"
                          variant={isEmail ? "primary" : "ghost"}
                          size="sm"
                          className={[
                            "notification-preferences__email",
                            isEmail
                              ? "notification-preferences__email--on"
                              : "notification-preferences__email--off",
                          ].join(" ")}
                          data-tour="notification-pref-email"
                          pressed={isEmail}
                          disabled={Boolean(savingCategory) || isMuted}
                          onClick={() =>
                            handleToggleEmail(category, emailCategories.includes(category))
                          }
                          aria-label={
                            emailCategories.includes(category) || isImportant
                              ? `E-mail ativo: ${display.notificationName}`
                              : `Receber por e-mail: ${display.notificationName}`
                          }
                          title={
                            isImportant
                              ? `Importante já envia e-mail — ${display.notificationName}.`
                              : emailCategories.includes(category)
                                ? `E-mail opt-in — ${display.notificationName}. Clique para remover.`
                                : `Receber por e-mail — ${display.notificationName}.`
                          }
                          icon={<Mail size={18} />}
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
