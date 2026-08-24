// portal/src/ui/admin/rbac/RbacAccessTree.tsx

import { useMemo, useState } from "react";
import { ChevronDown, ChevronRight, LayoutGrid, Shield, UsersRound } from "lucide-react";

import type { UserAccessProfile } from "../../../data/userAccessProfileTypes";
import { Alert, Badge, SearchInput } from "../../../ui-kit";

import {
  buildGroupCentricTree,
  buildRoleCentricTree,
  buildUnifiedAccessTree,
  countAccessTreeStats,
  filterGroupsTree,
  filterRolesTree,
  filterUnifiedTree,
  type RbacAccessTreeVariant,
  type RbacGroupsTree,
  type RbacRolesTree,
  type RbacTreeAppNode,
  type RbacTreeGroupNode,
  type RbacTreeRoleNode,
  type RbacUnifiedTree,
} from "./rbacAccessTree";

import "./RbacAccessTree.css";

type Props = {
  variant: RbacAccessTreeVariant;
  profile: UserAccessProfile;
  userDisplayName?: string;
  onOpenRole?: (roleId: string) => void;
  onOpenGroup?: (groupId: string) => void;
};

function PermissionBadges({ app }: { app: RbacTreeAppNode }) {
  return (
    <div className="rbac-access-tree-permissions">
      {app.permissions.map((permission) => (
        <Badge
          key={permission.key}
          tone="default"
          className="rbac-access-tree-permission"
          title={permission.code}
        >
          {permission.name}
        </Badge>
      ))}
    </div>
  );
}

function AppNode({ app }: { app: RbacTreeAppNode }) {
  const [collapsed, setCollapsed] = useState(app.defaultCollapsed);
  const canCollapse = app.permissions.length > 0;

  return (
    <li className="rbac-access-tree__item">
      <div className="rbac-access-tree-node">
        <span className="rbac-access-tree-node__label">
          <LayoutGrid size={13} aria-hidden="true" />
          {canCollapse ? (
            <button
              type="button"
              className="rbac-access-tree-app-toggle"
              onClick={() => setCollapsed((value) => !value)}
              aria-expanded={!collapsed}
            >
              {collapsed ? (
                <ChevronRight size={14} aria-hidden="true" />
              ) : (
                <ChevronDown size={14} aria-hidden="true" />
              )}
              {app.appName}
              <span className="rbac-access-tree-node__muted">
                ({app.permissions.length})
              </span>
            </button>
          ) : (
            <span className="rbac-access-tree-node__static">{app.appName}</span>
          )}
        </span>
      </div>

      {!collapsed && app.permissions.length > 0 ? (
        <ul className="rbac-access-tree rbac-access-tree--nested">
          <li className="rbac-access-tree__item">
            <PermissionBadges app={app} />
          </li>
        </ul>
      ) : null}
    </li>
  );
}

function RoleNode({
  role,
  onOpenRole,
}: {
  role: RbacTreeRoleNode;
  onOpenRole?: (roleId: string) => void;
}) {
  return (
    <li className="rbac-access-tree__item">
      <div className="rbac-access-tree-node">
        <span className="rbac-access-tree-node__label">
          <Shield size={13} aria-hidden="true" />
          {onOpenRole ? (
            <button
              type="button"
              className="rbac-access-tree-node__link"
              onClick={() => onOpenRole(role.roleId)}
            >
              {role.roleName}
            </button>
          ) : (
            <span className="rbac-access-tree-node__static">{role.roleName}</span>
          )}
        </span>
        {role.sourceLabels.map((label) => (
          <Badge key={`${role.key}:${label}`} tone="info">
            {label}
          </Badge>
        ))}
      </div>

      {role.apps.length > 0 ? (
        <ul className="rbac-access-tree rbac-access-tree--nested">
          {role.apps.map((app) => (
            <AppNode key={app.key} app={app} />
          ))}
        </ul>
      ) : null}
    </li>
  );
}

function GroupNode({
  group,
  onOpenGroup,
  onOpenRole,
}: {
  group: RbacTreeGroupNode;
  onOpenGroup?: (groupId: string) => void;
  onOpenRole?: (roleId: string) => void;
}) {
  return (
    <li className="rbac-access-tree__item">
      <div className="rbac-access-tree-node">
        <span className="rbac-access-tree-node__label">
          <UsersRound size={13} aria-hidden="true" />
          {onOpenGroup ? (
            <button
              type="button"
              className="rbac-access-tree-node__link"
              onClick={() => onOpenGroup(group.groupId)}
            >
              {group.groupName}
            </button>
          ) : (
            <span className="rbac-access-tree-node__static">{group.groupName}</span>
          )}
        </span>
        {group.description ? (
          <span className="rbac-access-tree-node__muted">{group.description}</span>
        ) : null}
      </div>

      {group.roles.length > 0 ? (
        <ul className="rbac-access-tree rbac-access-tree--nested">
          {group.roles.map((role) => (
            <RoleNode key={role.key} role={role} onOpenRole={onOpenRole} />
          ))}
        </ul>
      ) : null}
    </li>
  );
}

function variantStatsLabel(
  variant: RbacAccessTreeVariant,
  stats: ReturnType<typeof countAccessTreeStats>,
) {
  if (variant === "groups") {
    return `${stats.groupCount} ${stats.groupCount === 1 ? "grupo" : "grupos"} · ${stats.roleCount} ${stats.roleCount === 1 ? "papel herdado" : "papéis herdados"}`;
  }

  return `${stats.roleCount} ${stats.roleCount === 1 ? "papel" : "papéis"} · ${stats.permissionCount} permissões · ${stats.appCount} apps`;
}

export function RbacAccessTree({
  variant,
  profile,
  userDisplayName,
  onOpenRole,
  onOpenGroup,
}: Props) {
  const [query, setQuery] = useState("");
  const stats = useMemo(() => countAccessTreeStats(profile), [profile]);

  const tree = useMemo(() => {
    const normalized = query.trim();

    if (variant === "unified") {
      const built = buildUnifiedAccessTree(profile);
      return normalized ? filterUnifiedTree(built, normalized) : built;
    }

    if (variant === "roles") {
      const built = buildRoleCentricTree(profile);
      return normalized ? filterRolesTree(built, normalized) : built;
    }

    const built = buildGroupCentricTree(profile);
    return normalized ? filterGroupsTree(built, normalized) : built;
  }, [profile, query, variant]);

  const isEmpty =
    variant === "unified"
      ? (tree as RbacUnifiedTree).branches.length === 0
      : variant === "roles"
        ? (tree as RbacRolesTree).roles.length === 0
        : (tree as RbacGroupsTree).groups.length === 0;

  return (
    <section className="rbac-access-tree-panel">
      <div className="rbac-access-tree-panel__header">
        <p className="rbac-access-tree-panel__stats">{variantStatsLabel(variant, stats)}</p>
        <SearchInput
          className="rbac-access-tree-panel__search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Buscar papel, grupo, app ou permissão…"
          aria-label="Buscar na árvore de acesso"
        />
      </div>

      {profile.isSuperadmin ? (
        <Alert tone="info" className="rbac-access-tree-superadmin-banner">
          Acesso administrativo total — papéis abaixo são informativos.
        </Alert>
      ) : null}

      {userDisplayName ? (
        <div className="rbac-access-tree-node">
          <span className="rbac-access-tree-node__static">Usuário: {userDisplayName}</span>
        </div>
      ) : null}

      {isEmpty ? (
        <p className="rbac-access-tree-empty">Nenhum caminho de acesso encontrado.</p>
      ) : null}

      {variant === "unified" && !isEmpty ? (
        <ul className="rbac-access-tree">
          {(tree as RbacUnifiedTree).branches.map((branch) =>
            branch.kind === "directRole" ? (
              <RoleNode
                key={branch.key}
                role={branch.role}
                onOpenRole={onOpenRole}
              />
            ) : (
              <GroupNode
                key={branch.key}
                group={branch.group}
                onOpenGroup={onOpenGroup}
                onOpenRole={onOpenRole}
              />
            ),
          )}
        </ul>
      ) : null}

      {variant === "roles" && !isEmpty ? (
        <ul className="rbac-access-tree">
          {(tree as RbacRolesTree).roles.map((role) => (
            <RoleNode key={role.key} role={role} onOpenRole={onOpenRole} />
          ))}
        </ul>
      ) : null}

      {variant === "groups" && !isEmpty ? (
        <ul className="rbac-access-tree">
          {(tree as RbacGroupsTree).groups.map((group) => (
            <GroupNode
              key={group.key}
              group={group}
              onOpenGroup={onOpenGroup}
              onOpenRole={onOpenRole}
            />
          ))}
        </ul>
      ) : null}
    </section>
  );
}
