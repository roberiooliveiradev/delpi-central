// src/components/AppGroupedPermissionPicker.tsx

import { Package } from "lucide-react";
import type { ReactNode } from "react";
import { useMemo, useState } from "react";
import type { AdminPermission } from "../data/adminApi";
import { resolveIcon } from "../utils/iconResolver";
import type { AppInfoByModule } from "../ui/admin/tabs/RolesTab";
import "./RelationshipPicker.css";
import "./AppGroupedPermissionPicker.css";

type PermissionAppGroup = {
  moduleKey: string;
  moduleName: string;
  appName: string;
  icon: string | null;
  permissions: AdminPermission[];
};

type AppGroupedPermissionPickerProps = {
  title?: string;
  availableTitle?: string;
  selectedTitle?: string;
  searchPlaceholder?: string;
  emptyAvailableText?: string;
  emptySelectedText?: string;
  permissions: AdminPermission[];
  selectedIds: string[];
  appInfoByModule?: AppInfoByModule;
  disabled?: boolean;
  onChange: (nextIds: string[]) => void;
};

const normalize = (value: string | null | undefined) => {
  return (value ?? "").toLowerCase().trim();
};

const normalizeModuleKey = (value: string | null | undefined) => {
  return (value ?? "")
    .trim()
    .toLowerCase()
    .replace(/^\/+/, "")
    .replace(/^apps\//, "");
};

const getPermissionAppInfo = (
  permission: AdminPermission,
  appInfoByModule: AppInfoByModule
) => {
  const moduleKey = normalizeModuleKey(permission.module);

  if (!moduleKey) return null;

  return appInfoByModule[moduleKey] ?? null;
};

const buildPermissionGroups = (
  items: AdminPermission[],
  appInfoByModule: AppInfoByModule
): PermissionAppGroup[] => {
  const groups = new Map<string, AdminPermission[]>();

  for (const permission of items) {
    const moduleName = permission.module || "Sem módulo";

    if (!groups.has(moduleName)) {
      groups.set(moduleName, []);
    }

    groups.get(moduleName)!.push(permission);
  }

  return Array.from(groups.entries())
    .map(([moduleName, groupPermissions]) => {
      const firstPermission = groupPermissions[0];
      const appInfo = firstPermission
        ? getPermissionAppInfo(firstPermission, appInfoByModule)
        : null;

      return {
        moduleKey: moduleName,
        moduleName,
        appName: appInfo?.name || moduleName,
        icon: appInfo?.icon ?? null,
        permissions: groupPermissions.sort((a, b) => a.code.localeCompare(b.code)),
      };
    })
    .sort((a, b) => a.appName.localeCompare(b.appName));
};

export function AppGroupedPermissionPicker({
  title,
  availableTitle = "Apps disponíveis",
  selectedTitle = "Apps vinculados",
  searchPlaceholder = "Buscar por código, nome, app ou módulo...",
  emptyAvailableText = "Nenhuma permissão disponível para adicionar.",
  emptySelectedText = "Nenhuma permissão vinculada a este papel.",
  permissions,
  selectedIds,
  appInfoByModule = {},
  disabled = false,
  onChange,
}: AppGroupedPermissionPickerProps) {
  const [availableSearch, setAvailableSearch] = useState("");
  const [selectedSearch, setSelectedSearch] = useState("");
  const [expandedAvailableApps, setExpandedAvailableApps] = useState<string[]>(
    []
  );
  const [expandedSelectedApps, setExpandedSelectedApps] = useState<string[]>(
    []
  );

  const selectedIdSet = useMemo(() => new Set(selectedIds), [selectedIds]);

  const matchesSearch = (permission: AdminPermission, search: string) => {
    const term = normalize(search);

    if (!term) return true;

    const appInfo = getPermissionAppInfo(permission, appInfoByModule);

    return (
      normalize(permission.code).includes(term) ||
      normalize(permission.name).includes(term) ||
      normalize(permission.description).includes(term) ||
      normalize(permission.module).includes(term) ||
      normalize(appInfo?.name).includes(term)
    );
  };

  const availablePermissions = useMemo(() => {
    return permissions
      .filter((permission) => !selectedIdSet.has(permission.id))
      .filter((permission) => matchesSearch(permission, availableSearch));
  }, [permissions, selectedIdSet, availableSearch, appInfoByModule]);

  const linkedPermissions = useMemo(() => {
    return permissions
      .filter((permission) => selectedIdSet.has(permission.id))
      .filter((permission) => matchesSearch(permission, selectedSearch));
  }, [permissions, selectedIdSet, selectedSearch, appInfoByModule]);

  const availableGroups = useMemo(
    () => buildPermissionGroups(availablePermissions, appInfoByModule),
    [availablePermissions, appInfoByModule]
  );

  const linkedGroups = useMemo(
    () => buildPermissionGroups(linkedPermissions, appInfoByModule),
    [linkedPermissions, appInfoByModule]
  );

  const addOne = (id: string) => {
    if (disabled || selectedIdSet.has(id)) return;
    onChange([...selectedIds, id]);
  };

  const removeOne = (id: string) => {
    if (disabled) return;
    onChange(selectedIds.filter((selectedId) => selectedId !== id));
  };

  const addAllFiltered = () => {
    if (disabled || availablePermissions.length === 0) return;

    const next = new Set(selectedIds);

    availablePermissions.forEach((permission) => {
      next.add(permission.id);
    });

    onChange(Array.from(next));
  };

  const removeAllFiltered = () => {
    if (disabled || linkedPermissions.length === 0) return;

    const removeIds = new Set(linkedPermissions.map((permission) => permission.id));

    onChange(selectedIds.filter((id) => !removeIds.has(id)));
  };

  const addGroupPermissions = (groupPermissions: AdminPermission[]) => {
    if (disabled || groupPermissions.length === 0) return;

    const next = new Set(selectedIds);

    groupPermissions.forEach((permission) => {
      next.add(permission.id);
    });

    onChange(Array.from(next));
  };

  const removeGroupPermissions = (groupPermissions: AdminPermission[]) => {
    if (disabled || groupPermissions.length === 0) return;

    const removeIds = new Set(groupPermissions.map((permission) => permission.id));

    onChange(selectedIds.filter((id) => !removeIds.has(id)));
  };

  const toggleAvailableApp = (moduleKey: string) => {
    setExpandedAvailableApps((prev) =>
      prev.includes(moduleKey)
        ? prev.filter((key) => key !== moduleKey)
        : [...prev, moduleKey]
    );
  };

  const toggleSelectedApp = (moduleKey: string) => {
    setExpandedSelectedApps((prev) =>
      prev.includes(moduleKey)
        ? prev.filter((key) => key !== moduleKey)
        : [...prev, moduleKey]
    );
  };

  const getPermissionAvatar = (permission: AdminPermission): ReactNode => {
    const appInfo = getPermissionAppInfo(permission, appInfoByModule);
    const Icon = resolveIcon(appInfo?.icon);

    if (!Icon) {
      return permission.code?.[0]?.toUpperCase() ?? "•";
    }

    return <Icon size={18} />;
  };

  const getPermissionMeta = (permission: AdminPermission) => {
    const appInfo = getPermissionAppInfo(permission, appInfoByModule);
    const meta: {
      label: string;
      tone?: "default" | "success" | "warning" | "danger";
    }[] = [];

    if (
      permission.module &&
      normalizeModuleKey(appInfo?.name) !== normalizeModuleKey(permission.module)
    ) {
      meta.push({
        label: permission.module,
        tone: "default",
      });
    }

    return meta;
  };

  const renderMeta = (permission: AdminPermission) => {
    const meta = getPermissionMeta(permission);

    if (meta.length === 0) return null;

    return (
      <div className="relationship-card-meta">
        {meta.map((item) => (
          <span
            key={`${permission.id}-${item.label}`}
            className={[
              "relationship-pill",
              item.tone ? `relationship-pill-${item.tone}` : "",
            ]
              .filter(Boolean)
              .join(" ")}
          >
            {item.label}
          </span>
        ))}
      </div>
    );
  };

  const renderPermissionCard = (
    permission: AdminPermission,
    mode: "available" | "selected"
  ) => {
    const isAvailable = mode === "available";

    return (
      <article
        key={permission.id}
        className={[
          "relationship-card",
          "app-grouped-permission-card",
          isAvailable
            ? "relationship-card-available"
            : "relationship-card-selected",
        ]
          .filter(Boolean)
          .join(" ")}
      >
        <div className="relationship-card-icon" aria-hidden="true">
          {getPermissionAvatar(permission)}
        </div>

        <div className="relationship-card-main">
          <div className="relationship-card-title-row">
            <strong className="relationship-card-title">
              {permission.code}
            </strong>
          </div>

          {(permission.name || permission.module) && (
            <div className="relationship-card-subtitle">
              {permission.name ?? permission.module ?? ""}
            </div>
          )}

          {permission.description && (
            <div className="relationship-card-description">
              {permission.description}
            </div>
          )}

          {renderMeta(permission)}
        </div>

        <button
          type="button"
          className={[
            "relationship-action",
            isAvailable
              ? "relationship-action-add"
              : "relationship-action-remove",
          ]
            .filter(Boolean)
            .join(" ")}
          disabled={disabled}
          onClick={() =>
            isAvailable ? addOne(permission.id) : removeOne(permission.id)
          }
          aria-label={
            isAvailable
              ? `Adicionar ${permission.code}`
              : `Remover ${permission.code}`
          }
        >
          <span>{isAvailable ? "Adicionar" : "Remover"}</span>
          <strong aria-hidden="true">{isAvailable ? "→" : "×"}</strong>
        </button>
      </article>
    );
  };

  const renderAppGroup = (
    group: PermissionAppGroup,
    mode: "available" | "selected"
  ) => {
    const isAvailable = mode === "available";
    const expanded = isAvailable
      ? expandedAvailableApps.includes(group.moduleKey)
      : expandedSelectedApps.includes(group.moduleKey);

    const ModuleIcon = resolveIcon(group.icon) || Package;

    const toggle = () => {
      if (isAvailable) {
        toggleAvailableApp(group.moduleKey);
      } else {
        toggleSelectedApp(group.moduleKey);
      }
    };

    const bulkAction = () => {
      if (isAvailable) {
        addGroupPermissions(group.permissions);
      } else {
        removeGroupPermissions(group.permissions);
      }
    };

    return (
      <section
        key={`${mode}-${group.moduleKey}`}
        className={[
          "app-grouped-permission-app",
          expanded ? "is-expanded" : "",
          isAvailable
            ? "app-grouped-permission-app-available"
            : "app-grouped-permission-app-selected",
        ]
          .filter(Boolean)
          .join(" ")}
      >
        <div className="app-grouped-permission-app-header">
          <button
            type="button"
            className="app-grouped-permission-app-toggle"
            onClick={toggle}
            aria-expanded={expanded}
          >
            <div className="app-grouped-permission-app-title">
              <div
                className="app-grouped-permission-app-icon"
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
                  {group.permissions.length}{" "}
                  {group.permissions.length === 1 ? "permissão" : "permissões"}
                </span>
              </div>
            </div>

            <span className="app-grouped-permission-app-chevron">
              {expanded ? "Recolher" : "Expandir"}
            </span>
          </button>

          <button
            type="button"
            className={[
              "relationship-mini-button",
              !isAvailable ? "relationship-mini-danger" : "",
            ]
              .filter(Boolean)
              .join(" ")}
            disabled={disabled || group.permissions.length === 0}
            onClick={bulkAction}
          >
            {isAvailable ? "Adicionar todas" : "Remover todas"}
          </button>
        </div>

        {expanded && (
          <div className="app-grouped-permission-list">
            {group.permissions.map((permission) =>
              renderPermissionCard(permission, mode)
            )}
          </div>
        )}
      </section>
    );
  };

  return (
    <section className="relationship-picker app-grouped-permission-picker">
      {title && (
        <header className="relationship-picker-header">
          <div className="relationship-picker-heading">
            <h4>{title}</h4>
          </div>

          <div className="relationship-picker-summary">
            <span>
              <strong>{selectedIds.length}</strong>
              vinculados
            </span>
            <span>
              <strong>{permissions.length}</strong>
              no catálogo
            </span>
          </div>
        </header>
      )}

      <div className="relationship-columns">
        <section className="relationship-column relationship-column-available">
          <div className="relationship-column-header">
            <div>
              <strong>{availableTitle}</strong>
              <span>
                {availableGroups.length}{" "}
                {availableGroups.length === 1 ? "app" : "apps"} ·{" "}
                {availablePermissions.length}{" "}
                {availablePermissions.length === 1
                  ? "permissão"
                  : "permissões"}
              </span>
            </div>

            <button
              type="button"
              className="relationship-mini-button"
              disabled={disabled || availablePermissions.length === 0}
              onClick={addAllFiltered}
            >
              Adicionar filtrados
            </button>
          </div>

          <div className="relationship-searchbar">
            <span aria-hidden="true">⌕</span>
            <input
              value={availableSearch}
              onChange={(event) => setAvailableSearch(event.target.value)}
              placeholder={searchPlaceholder}
              disabled={disabled}
              aria-label={availableTitle}
            />
          </div>

          <div className="relationship-list app-grouped-permission-apps">
            {availableGroups.length === 0 ? (
              <div className="relationship-empty">
                <div className="relationship-empty-icon">+</div>
                <strong>Nada por aqui</strong>
                <span>{emptyAvailableText}</span>
              </div>
            ) : (
              availableGroups.map((group) => renderAppGroup(group, "available"))
            )}
          </div>
        </section>

        <section className="relationship-column relationship-column-selected">
          <div className="relationship-column-header">
            <div>
              <strong>{selectedTitle}</strong>
              <span>
                {linkedGroups.length}{" "}
                {linkedGroups.length === 1 ? "app" : "apps"} ·{" "}
                {linkedPermissions.length}{" "}
                {linkedPermissions.length === 1 ? "permissão" : "permissões"}
              </span>
            </div>

            <button
              type="button"
              className="relationship-mini-button relationship-mini-danger"
              disabled={disabled || linkedPermissions.length === 0}
              onClick={removeAllFiltered}
            >
              Remover filtrados
            </button>
          </div>

          <div className="relationship-searchbar">
            <span aria-hidden="true">⌕</span>
            <input
              value={selectedSearch}
              onChange={(event) => setSelectedSearch(event.target.value)}
              placeholder={searchPlaceholder}
              disabled={disabled}
              aria-label={selectedTitle}
            />
          </div>

          <div className="relationship-list app-grouped-permission-apps">
            {linkedGroups.length === 0 ? (
              <div className="relationship-empty relationship-empty-selected">
                <div className="relationship-empty-icon">✓</div>
                <strong>Nenhum vínculo</strong>
                <span>{emptySelectedText}</span>
              </div>
            ) : (
              linkedGroups.map((group) => renderAppGroup(group, "selected"))
            )}
          </div>
        </section>
      </div>
    </section>
  );
}
