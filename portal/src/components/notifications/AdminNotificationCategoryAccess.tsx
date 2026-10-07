import { useCallback, useContext, useEffect, useMemo, useState } from "react";
import { Bell, BellOff, Mail, Star, Users } from "lucide-react";

import { AuthContext } from "../../state/AuthContext";
import { ApiClient } from "../../data/apiClient";
import {
  CoreApi,
  type NotificationCategoryUserItem,
} from "../../data/coreApi";
import {
  resolveNotificationCategoryIconComponent,
  resolveNotificationPreferenceDisplay,
} from "../../utils/notificationCatalog";
import { useNotificationCatalog } from "../../state/NotificationCatalogContext";
import { Alert, Button, SearchInput, Spinner } from "../../ui-kit";

import "./AdminNotificationCategoryAccess.css";

type Props = {
  coreApi?: CoreApi;
};

const PAGE_SIZE = 20;

type PreferenceFlag = "enabled" | "important" | "email";

function userStatusLabel(item: NotificationCategoryUserItem, saving: boolean): string {
  if (saving) return "Salvando…";
  if (!item.enabled) return "Silenciada";
  if (item.important && item.emailEnabled) return "Importante · E-mail";
  if (item.important) return "Importante";
  if (item.emailEnabled) return "E-mail";
  return "Recebendo";
}

export function AdminNotificationCategoryAccess({ coreApi: coreApiProp }: Props) {
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

  const [categoryQuery, setCategoryQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [users, setUsers] = useState<NotificationCategoryUserItem[]>([]);
  const [userQuery, setUserQuery] = useState("");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [savingKey, setSavingKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const appRefs = useMemo(
    () => apps.map((app) => ({ id: app.id, name: app.name, icon: app.icon })),
    [apps],
  );

  const filteredCategories = useMemo(() => {
    const query = categoryQuery.trim().toLocaleLowerCase("pt-BR");
    const categories = [...catalog.categories].sort((a, b) =>
      a.notificationLabel.localeCompare(b.notificationLabel, "pt-BR"),
    );
    if (!query) return categories;
    return categories.filter((spec) => {
      const display = resolveNotificationPreferenceDisplay(spec.id, catalog, appRefs);
      const haystack = [display.notificationName, display.applicationName, spec.id]
        .join(" ")
        .toLocaleLowerCase("pt-BR");
      return haystack.includes(query);
    });
  }, [catalog, categoryQuery, appRefs]);

  const loadUsers = useCallback(
    async (category: string, nextPage: number, query: string, append: boolean) => {
      setLoadingUsers(true);
      setError(null);
      try {
        const data = await coreApi.getNotificationCategoryUsers({
          category,
          q: query || undefined,
          page: nextPage,
          pageSize: PAGE_SIZE,
        });
        setUsers((previous) => (append ? [...previous, ...data.items] : data.items));
        setTotal(data.total);
        setHasMore(data.hasMore);
        setPage(nextPage);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Falha ao carregar usuários");
      } finally {
        setLoadingUsers(false);
      }
    },
    [coreApi],
  );

  useEffect(() => {
    if (!selectedCategory) return;
    void loadUsers(selectedCategory, 1, userQuery.trim(), false);
  }, [selectedCategory, userQuery, loadUsers]);

  function handleSelectCategory(category: string) {
    if (category === selectedCategory) {
      setSelectedCategory(null);
      setUsers([]);
      return;
    }
    setSelectedCategory(category);
    setUsers([]);
    setUserQuery("");
    setTotal(0);
    setHasMore(false);
  }

  const applyFlag = useCallback(
    async (item: NotificationCategoryUserItem, flag: PreferenceFlag) => {
      if (!selectedCategory || savingKey || !item.mutable) return;
      const nextValue =
        flag === "enabled" ? !item.enabled : flag === "important" ? !item.important : !item.emailEnabled;
      const key = `${item.id}:${flag}`;
      setSavingKey(key);
      setError(null);
      const payload: {
        category: string;
        enabled?: boolean;
        important?: boolean;
        email?: boolean;
      } = { category: selectedCategory };
      payload[flag] = nextValue;
      try {
        const data = await coreApi.updateUserNotificationCategoryPreference(item.id, payload);
        const muted = new Set(data.mutedCategories);
        const important = new Set(data.importantCategories);
        const email = new Set(data.emailCategories);
        setUsers((previous) =>
          previous.map((entry) =>
            entry.id === item.id
              ? {
                  ...entry,
                  enabled: !muted.has(selectedCategory),
                  important: important.has(selectedCategory),
                  emailEnabled: email.has(selectedCategory),
                }
              : entry,
          ),
        );
      } catch (err) {
        setError(err instanceof Error ? err.message : "Falha ao salvar preferência");
      } finally {
        setSavingKey(null);
      }
    },
    [coreApi, savingKey, selectedCategory],
  );

  return (
    <section className="admin-category-access" aria-labelledby="admin-category-access-title">
      <header className="admin-category-access__header">
        <Users size={18} aria-hidden="true" />
        <div>
          <h2 id="admin-category-access-title">Gestão por usuário</h2>
          <p>
            Escolha uma notificação para ver os usuários com acesso ao aplicativo e ajustar
            recebimento, destaque e e-mail. A alteração é salva na hora.
          </p>
        </div>
      </header>

      <SearchInput
        className="admin-category-access__search"
        value={categoryQuery}
        onChange={(event) => setCategoryQuery(event.target.value)}
        onClear={() => setCategoryQuery("")}
        placeholder="Buscar por notificação ou aplicativo…"
        aria-label="Buscar categoria de notificação"
      />

      <div className="admin-category-access__layout">
        <ul className="admin-category-access__categories" aria-label="Categorias de notificação">
          {filteredCategories.length === 0 ? (
            <li className="admin-category-access__empty" role="status">
              Nenhuma notificação encontrada.
            </li>
          ) : (
            filteredCategories.map((spec) => {
              const display = resolveNotificationPreferenceDisplay(spec.id, catalog, appRefs);
              const CategoryIcon = resolveNotificationCategoryIconComponent(display.iconName);
              const selected = spec.id === selectedCategory;
              return (
                <li key={spec.id}>
                  <button
                    type="button"
                    className={[
                      "admin-category-access__category",
                      selected ? "admin-category-access__category--selected" : "",
                    ].join(" ")}
                    aria-pressed={selected}
                    onClick={() => handleSelectCategory(spec.id)}
                  >
                    <span className="admin-category-access__category-icon" aria-hidden="true">
                      <CategoryIcon size={18} />
                    </span>
                    <span className="admin-category-access__category-copy">
                      <span className="admin-category-access__category-name">
                        {display.notificationName}
                      </span>
                      <span className="admin-category-access__category-app">
                        {display.applicationName}
                        {spec.mutable ? "" : " · não editável"}
                      </span>
                    </span>
                  </button>
                </li>
              );
            })
          )}
        </ul>

        <div className="admin-category-access__users">
          {!selectedCategory ? (
            <p className="admin-category-access__hint" role="status">
              Selecione uma notificação para listar os usuários com acesso.
            </p>
          ) : (
            <>
              <SearchInput
                className="admin-category-access__user-search"
                value={userQuery}
                onChange={(event) => setUserQuery(event.target.value)}
                onClear={() => setUserQuery("")}
                placeholder="Buscar usuário por nome ou e-mail…"
                aria-label="Buscar usuário"
              />

              {error ? <Alert tone="danger">{error}</Alert> : null}
              {loadingUsers && users.length === 0 ? <Spinner label="Carregando…" /> : null}

              {!loadingUsers && users.length === 0 && !error ? (
                <p className="admin-category-access__empty" role="status">
                  Nenhum usuário com acesso a esta notificação.
                </p>
              ) : null}

              {users.length > 0 ? (
                <>
                  <ul className="admin-category-access__user-list">
                    {users.map((item) => {
                      const busy = savingKey !== null && savingKey.startsWith(`${item.id}:`);
                      return (
                        <li key={item.id} className="admin-category-access__user">
                          <span className="admin-category-access__user-copy">
                            <span className="admin-category-access__user-name">{item.name}</span>
                            <span className="admin-category-access__user-email">{item.email}</span>
                            <span className="admin-category-access__user-status">
                              {userStatusLabel(item, busy)}
                            </span>
                          </span>
                          <span className="admin-category-access__user-actions">
                            <Button
                              type="button"
                              variant={item.important ? "primary" : "ghost"}
                              size="sm"
                              pressed={item.important}
                              disabled={!item.mutable || Boolean(savingKey)}
                              onClick={() => void applyFlag(item, "important")}
                              aria-label={
                                item.important
                                  ? `Remover importante: ${item.name}`
                                  : `Marcar como importante: ${item.name}`
                              }
                              title={
                                item.important
                                  ? "Importante — clique para remover."
                                  : "Marcar como importante."
                              }
                              icon={<Star size={18} fill={item.important ? "currentColor" : "none"} />}
                            />
                            <Button
                              type="button"
                              variant={item.enabled ? "ghost" : "danger-soft"}
                              size="sm"
                              pressed={!item.enabled}
                              disabled={!item.mutable || Boolean(savingKey)}
                              onClick={() => void applyFlag(item, "enabled")}
                              aria-label={
                                item.enabled
                                  ? `Silenciar: ${item.name}`
                                  : `Voltar a receber: ${item.name}`
                              }
                              title={
                                item.enabled
                                  ? "Recebendo — clique para silenciar."
                                  : "Silenciada — clique para voltar a receber."
                              }
                              icon={
                                item.enabled ? <Bell size={18} /> : <BellOff size={18} />
                              }
                            />
                            <Button
                              type="button"
                              variant={item.emailEnabled ? "primary" : "ghost"}
                              size="sm"
                              pressed={item.emailEnabled}
                              disabled={!item.mutable || !item.enabled || Boolean(savingKey)}
                              onClick={() => void applyFlag(item, "email")}
                              aria-label={
                                item.emailEnabled
                                  ? `Remover e-mail: ${item.name}`
                                  : `Receber por e-mail: ${item.name}`
                              }
                              title={
                                !item.enabled
                                  ? "Silenciada — o e-mail fica indisponível."
                                  : item.emailEnabled
                                    ? "E-mail ativo — clique para remover."
                                    : "Receber por e-mail."
                              }
                              icon={<Mail size={18} />}
                            />
                          </span>
                        </li>
                      );
                    })}
                  </ul>
                  <footer className="admin-category-access__footer">
                    <span className="admin-category-access__total">
                      {users.length} de {total} usuários
                    </span>
                    {hasMore ? (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        disabled={loadingUsers}
                        onClick={() =>
                          void loadUsers(selectedCategory, page + 1, userQuery.trim(), true)
                        }
                      >
                        {loadingUsers ? "Carregando…" : "Carregar mais"}
                      </Button>
                    ) : null}
                  </footer>
                </>
              ) : null}
            </>
          )}
        </div>
      </div>
    </section>
  );
}
