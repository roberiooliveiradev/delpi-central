// src/ui/admin/tabs/PermissionsTab.tsx

import { useContext, useEffect, useMemo, useState } from "react";
import { Package } from "lucide-react";
import { AuthContext } from "../../../state/AuthContext";
import { ApiClient } from "../../../data/apiClient";
import { AdminApi } from "../../../data/adminApi";
import type { AdminApp, AdminPermission } from "../../../data/adminApi";
import { usePaginatedResource } from "../../../hooks/usePaginatedResource";
import { resolveIcon } from "../../../utils/iconResolver";
import "./PermissionsTab.css";

type AppInfoByModule = Record<
  string,
  {
    name?: string | null;
    icon?: string | null;
  }
>;

type GroupedPermissionModule = {
  moduleName: string;
  appName: string;
  icon?: string | null;
  permissions: AdminPermission[];
};

const MODULES_PER_PAGE = 6;

const normalizeText = (value: string | null | undefined) => {
  return (value ?? "").trim().toLowerCase();
};

const normalizeModuleKey = (value: string | null | undefined) => {
  return (value ?? "")
    .trim()
    .toLowerCase()
    .replace(/^\/+/, "")
    .replace(/^apps\//, "");
};

const buildAppInfoByModule = (apps: AdminApp[]): AppInfoByModule => {
  const result: AppInfoByModule = {};

  apps.forEach((app) => {
    const info = {
      name: app.name ?? app.id,
      icon: app.icon ?? null,
    };

    const idKey = normalizeModuleKey(app.id);
    const basePathKey = normalizeModuleKey(app.base_path);

    if (idKey) {
      result[idKey] = info;
    }

    if (basePathKey) {
      result[basePathKey] = info;
    }
  });

  return result;
};

export const PermissionsTab = () => {
  const { getAccessToken } = useContext(AuthContext);

  const [search, setSearch] = useState("");
  const [expandedModules, setExpandedModules] = useState<string[]>([]);
  const [appInfoByModule, setAppInfoByModule] = useState<AppInfoByModule>({});
  const [modulePage, setModulePage] = useState(1);

  const api = useMemo(() => {
    return new AdminApi(new ApiClient("", getAccessToken));
  }, [getAccessToken]);

  const permsResource = usePaginatedResource<AdminPermission>(
    ({ page, pageSize }) =>
      api.listPermissions({
        page,
        pageSize,
        sort: "module",
        direction: "asc",
      }),
    999,
    []
  );

  useEffect(() => {
    let cancelled = false;

    const loadApps = async () => {
      try {
        const appsRes = await api.listApps({
          page: 1,
          pageSize: 999,
          sort: "name",
          direction: "asc",
        });

        if (cancelled) return;

        setAppInfoByModule(buildAppInfoByModule(appsRes.data ?? []));
      } catch {
        if (cancelled) return;

        setAppInfoByModule({});
      }
    };

    loadApps();

    return () => {
      cancelled = true;
    };
  }, [api]);

  useEffect(() => {
    setModulePage(1);
  }, [search]);

  const getPermissionAppInfo = (permission: AdminPermission) => {
    const moduleKey = normalizeModuleKey(permission.module);

    if (!moduleKey) return null;

    return appInfoByModule[moduleKey] ?? null;
  };

  const filteredPermissions = useMemo(() => {
    const term = normalizeText(search);

    const permissions = permsResource.data ?? [];

    if (!term) return permissions;

    return permissions.filter((permission) => {
      const appInfo = getPermissionAppInfo(permission);

      return (
        normalizeText(permission.code).includes(term) ||
        normalizeText(permission.name).includes(term) ||
        normalizeText(permission.description).includes(term) ||
        normalizeText(permission.module).includes(term) ||
        normalizeText(appInfo?.name).includes(term)
      );
    });
  }, [permsResource.data, search, appInfoByModule]);

  const groupedPermissions = useMemo<GroupedPermissionModule[]>(() => {
    const groups = new Map<string, AdminPermission[]>();

    for (const permission of filteredPermissions) {
      const moduleName = permission.module || "Sem módulo";

      if (!groups.has(moduleName)) {
        groups.set(moduleName, []);
      }

      groups.get(moduleName)!.push(permission);
    }

    return Array.from(groups.entries())
      .map(([moduleName, permissions]) => {
        const firstPermission = permissions[0];
        const appInfo = firstPermission
          ? getPermissionAppInfo(firstPermission)
          : null;

        return {
          moduleName,
          appName: appInfo?.name || moduleName,
          icon: appInfo?.icon ?? null,
          permissions: permissions.sort((a, b) =>
            a.code.localeCompare(b.code)
          ),
        };
      })
      .sort((a, b) => a.appName.localeCompare(b.appName));
  }, [filteredPermissions, appInfoByModule]);

  const totalModules = groupedPermissions.length;
  const totalPages = Math.max(1, Math.ceil(totalModules / MODULES_PER_PAGE));
  const safePage = Math.min(modulePage, totalPages);

  useEffect(() => {
    if (modulePage > totalPages) {
      setModulePage(totalPages);
    }
  }, [modulePage, totalPages]);

  const paginatedModules = useMemo(() => {
    const start = (safePage - 1) * MODULES_PER_PAGE;
    const end = start + MODULES_PER_PAGE;

    return groupedPermissions.slice(start, end);
  }, [groupedPermissions, safePage]);

  const totalPermissions =
    permsResource.pagination?.total ?? permsResource.data.length ?? 0;

  const visiblePermissions = filteredPermissions.length;

  const firstModuleIndex =
    totalModules === 0 ? 0 : (safePage - 1) * MODULES_PER_PAGE + 1;

  const lastModuleIndex = Math.min(safePage * MODULES_PER_PAGE, totalModules);

  const toggleModule = (moduleName: string) => {
    setExpandedModules((prev) =>
      prev.includes(moduleName)
        ? prev.filter((x) => x !== moduleName)
        : [...prev, moduleName]
    );
  };

  const expandCurrentPage = () => {
    const pageModuleNames = paginatedModules.map((group) => group.moduleName);

    setExpandedModules((prev) => {
      const next = new Set(prev);

      pageModuleNames.forEach((moduleName) => {
        next.add(moduleName);
      });

      return Array.from(next);
    });
  };

  const collapseCurrentPage = () => {
    const pageModuleNames = new Set(
      paginatedModules.map((group) => group.moduleName)
    );

    setExpandedModules((prev) =>
      prev.filter((moduleName) => !pageModuleNames.has(moduleName))
    );
  };

  const goToPreviousPage = () => {
    setModulePage((prev) => Math.max(1, prev - 1));
  };

  const goToNextPage = () => {
    setModulePage((prev) => Math.min(totalPages, prev + 1));
  };

  const getModuleIcon = (icon?: string | null) => {
    return resolveIcon(icon) || Package;
  };

  const renderPermissionMeta = (permission: AdminPermission) => {
    const appInfo = getPermissionAppInfo(permission);
    const meta: string[] = [];

    if (appInfo?.name) {
      meta.push(appInfo.name);
    }

    if (
      permission.module &&
      normalizeModuleKey(appInfo?.name) !== normalizeModuleKey(permission.module)
    ) {
      meta.push(permission.module);
    }

    if (meta.length === 0) {
      meta.push("Sem módulo");
    }

    return meta;
  };

  return (
    <div className="permissions-page">
      <div className="permissions-header">
        <div>
          <h3>Permissões</h3>
          <p>
            Permissões são criadas e atualizadas via manifesto dos plugins.
            Para conceder acesso, vincule permissões aos papéis.
          </p>
        </div>

        <div className="permissions-summary">
          <strong>{totalPermissions}</strong>
          <span>permissões</span>
        </div>
      </div>

      <div className="permissions-toolbar">
        <label className="permissions-search">
          <span aria-hidden="true">⌕</span>
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Buscar por código, nome, descrição, app ou módulo..."
          />
        </label>

        <div className="permissions-toolbar-actions">
          <button
            type="button"
            onClick={expandCurrentPage}
            disabled={paginatedModules.length === 0}
          >
            Expandir página
          </button>

          <button
            type="button"
            onClick={collapseCurrentPage}
            disabled={expandedModules.length === 0}
          >
            Recolher página
          </button>
        </div>
      </div>

      <div className="permissions-list-summary">
        <span>
          Exibindo <strong>{firstModuleIndex}</strong>–
          <strong>{lastModuleIndex}</strong> de <strong>{totalModules}</strong>{" "}
          apps/módulos
        </span>

        {!permsResource.loading && search.trim() && (
          <span>
            <strong>{visiblePermissions}</strong> permissões encontradas para{" "}
            <em>{search}</em>
          </span>
        )}
      </div>

      {permsResource.loading && (
        <div className="permissions-state">Carregando permissões...</div>
      )}

      {!permsResource.loading && groupedPermissions.length === 0 && (
        <div className="permissions-state">Nenhuma permissão encontrada.</div>
      )}

      {!permsResource.loading && groupedPermissions.length > 0 && (
        <>
          <div className="permissions-modules">
            {paginatedModules.map((group) => {
              const expanded = expandedModules.includes(group.moduleName);
              const ModuleIcon = getModuleIcon(group.icon);

              return (
                <section key={group.moduleName} className="permissions-module">
                  <button
                    type="button"
                    className="permissions-module-header"
                    onClick={() => toggleModule(group.moduleName)}
                  >
                    <div className="permissions-module-title">
                      <div
                        className="permissions-module-icon"
                        aria-hidden="true"
                      >
                        <ModuleIcon size={20} strokeWidth={2.2} />
                      </div>

                      <div>
                        <strong>{group.appName}</strong>
                        <span>
                          {group.moduleName !== group.appName && (
                            <>módulo: {group.moduleName} · </>
                          )}
                          {group.permissions.length} permissões
                        </span>
                      </div>
                    </div>

                    <span className="permissions-module-toggle">
                      {expanded ? "Recolher" : "Expandir"}
                    </span>
                  </button>

                  {expanded && (
                    <div className="permissions-grid">
                      {group.permissions.map((permission) => {
                        const appInfo = getPermissionAppInfo(permission);
                        const PermissionIcon = getModuleIcon(appInfo?.icon);

                        return (
                          <article
                            key={permission.id}
                            className="permission-card"
                          >
                            <div className="permission-card-header">
                              <div
                                className="permission-card-icon"
                                aria-hidden="true"
                              >
                                <PermissionIcon size={18} strokeWidth={2.25} />
                              </div>

                              <div className="permission-card-heading">
                                <div className="permission-card-code">
                                  {permission.code}
                                </div>

                                <div className="permission-card-name">
                                  {permission.name || "Sem nome"}
                                </div>
                              </div>
                            </div>

                            {permission.description && (
                              <div className="permission-card-description">
                                {permission.description}
                              </div>
                            )}

                            <div className="permission-card-meta">
                              {renderPermissionMeta(permission).map((label) => (
                                <span key={`${permission.id}-${label}`}>
                                  {label}
                                </span>
                              ))}
                            </div>
                          </article>
                        );
                      })}
                    </div>
                  )}
                </section>
              );
            })}
          </div>

          {totalPages > 1 && (
            <div className="permissions-pagination">
              <button
                type="button"
                onClick={goToPreviousPage}
                disabled={safePage <= 1}
              >
                Anterior
              </button>

              <span>
                Página <strong>{safePage}</strong> de{" "}
                <strong>{totalPages}</strong>
              </span>

              <button
                type="button"
                onClick={goToNextPage}
                disabled={safePage >= totalPages}
              >
                Próxima
              </button>
            </div>
          )}
        </>
      )}

      <div className="permissions-tip">
        Dica: esta página é de consulta. Use a tela de <strong>Papéis</strong>{" "}
        para conceder permissões.
      </div>
    </div>
  );
};