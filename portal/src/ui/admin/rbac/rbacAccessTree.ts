// portal/src/ui/admin/rbac/rbacAccessTree.ts

import type {
  UserAccessProfile,
  UserAccessProfilePermission,
  UserAccessProfileRole,
  UserAccessRoleSource,
} from "../../../data/userAccessProfileTypes";

export const ORPHAN_APP_ID = "__other_permissions__";
export const ORPHAN_APP_NAME = "Outras permissões";
export const DEFAULT_APP_COLLAPSE_THRESHOLD = 5;

export type RbacTreePermissionNode = {
  kind: "permission";
  key: string;
  code: string;
  name: string;
};

export type RbacTreeAppNode = {
  kind: "app";
  key: string;
  appId: string;
  appName: string;
  permissions: RbacTreePermissionNode[];
  defaultCollapsed: boolean;
};

export type RbacTreeRoleNode = {
  kind: "role";
  key: string;
  roleId: string;
  roleName: string;
  sourceLabels: string[];
  apps: RbacTreeAppNode[];
};

export type RbacTreeGroupNode = {
  kind: "group";
  key: string;
  groupId: string;
  groupName: string;
  description?: string | null;
  roles: RbacTreeRoleNode[];
};

export type RbacUnifiedDirectBranch = {
  kind: "directRole";
  key: string;
  role: RbacTreeRoleNode;
};

export type RbacUnifiedGroupBranch = {
  kind: "groupBranch";
  key: string;
  group: RbacTreeGroupNode;
};

export type RbacUnifiedTree = {
  branches: Array<RbacUnifiedDirectBranch | RbacUnifiedGroupBranch>;
};

export type RbacRolesTree = {
  roles: RbacTreeRoleNode[];
};

export type RbacGroupsTree = {
  groups: RbacTreeGroupNode[];
};

export type RbacAccessTreeVariant = "unified" | "roles" | "groups";

export function formatRoleSourceLabel(source: UserAccessRoleSource): string {
  if (source.type === "direct") {
    return "Direto";
  }
  return `Via ${source.groupName}`;
}

export function groupPermissionsByApp(role: UserAccessProfileRole): RbacTreeAppNode[] {
  const assigned = new Set<string>();
  const apps: RbacTreeAppNode[] = [];

  for (const app of role.apps) {
    const routeCodes = new Set(
      app.routes
        .map((route) => route.permission)
        .filter((code): code is string => Boolean(code)),
    );

    const appPermissions = role.permissions.filter(
      (permission) =>
        routeCodes.has(permission.code) ||
        permission.code.startsWith(`${app.id}.`),
    );

    if (appPermissions.length === 0) {
      continue;
    }

    appPermissions.forEach((permission) => assigned.add(permission.code));
    apps.push(buildAppNode(app.id, app.name, appPermissions));
  }

  const orphanPermissions = role.permissions.filter(
    (permission) => !assigned.has(permission.code),
  );

  if (orphanPermissions.length > 0) {
    apps.push(buildAppNode(ORPHAN_APP_ID, ORPHAN_APP_NAME, orphanPermissions));
  }

  return apps;
}

function buildAppNode(
  appId: string,
  appName: string,
  permissions: UserAccessProfilePermission[],
): RbacTreeAppNode {
  const permissionNodes = permissions.map((permission) => ({
    kind: "permission" as const,
    key: `${appId}:${permission.code}`,
    code: permission.code,
    name: permission.name || permission.code,
  }));

  return {
    kind: "app",
    key: `app:${appId}`,
    appId,
    appName,
    permissions: permissionNodes,
    defaultCollapsed: permissionNodes.length > DEFAULT_APP_COLLAPSE_THRESHOLD,
  };
}

function buildRoleNode(role: UserAccessProfileRole): RbacTreeRoleNode {
  return {
    kind: "role",
    key: `role:${role.id}`,
    roleId: role.id,
    roleName: role.name,
    sourceLabels: role.sources.map(formatRoleSourceLabel),
    apps: groupPermissionsByApp(role),
  };
}

function roleHasDirectSource(role: UserAccessProfileRole): boolean {
  return role.sources.some((source) => source.type === "direct");
}

function roleBelongsToGroup(role: UserAccessProfileRole, groupId: string): boolean {
  return role.sources.some(
    (source) => source.type === "group" && source.groupId === groupId,
  );
}

export function buildUnifiedAccessTree(profile: UserAccessProfile): RbacUnifiedTree {
  const branches: RbacUnifiedTree["branches"] = [];

  for (const role of profile.roles) {
    if (!roleHasDirectSource(role)) {
      continue;
    }

    branches.push({
      kind: "directRole",
      key: `direct:${role.id}`,
      role: {
        ...buildRoleNode(role),
        sourceLabels: ["Direto"],
      },
    });
  }

  for (const group of profile.groups) {
    const inheritedRoles = profile.roles
      .filter((role) => roleBelongsToGroup(role, group.id))
      .map((role) => ({
        ...buildRoleNode(role),
        sourceLabels: ["Herdado"],
      }));

    if (inheritedRoles.length === 0) {
      continue;
    }

    branches.push({
      kind: "groupBranch",
      key: `group:${group.id}`,
      group: {
        kind: "group",
        key: `group:${group.id}`,
        groupId: group.id,
        groupName: group.name,
        description: group.description,
        roles: inheritedRoles,
      },
    });
  }

  return { branches };
}

export function buildRoleCentricTree(profile: UserAccessProfile): RbacRolesTree {
  return {
    roles: profile.roles.map((role) => buildRoleNode(role)),
  };
}

export function buildGroupCentricTree(profile: UserAccessProfile): RbacGroupsTree {
  const groups: RbacTreeGroupNode[] = profile.groups.map((group) => ({
    kind: "group",
    key: `group:${group.id}`,
    groupId: group.id,
    groupName: group.name,
    description: group.description,
    roles: profile.roles
      .filter((role) => roleBelongsToGroup(role, group.id))
      .map((role) => ({
        ...buildRoleNode(role),
        sourceLabels: [],
      })),
  }));

  return { groups: groups.filter((group) => group.roles.length > 0) };
}

export function buildAccessTree(
  variant: RbacAccessTreeVariant,
  profile: UserAccessProfile,
): RbacUnifiedTree | RbacRolesTree | RbacGroupsTree {
  switch (variant) {
    case "unified":
      return buildUnifiedAccessTree(profile);
    case "roles":
      return buildRoleCentricTree(profile);
    case "groups":
      return buildGroupCentricTree(profile);
    default:
      return buildUnifiedAccessTree(profile);
  }
}

function matchesQuery(value: string, query: string): boolean {
  return value.toLowerCase().includes(query.toLowerCase());
}

export function filterUnifiedTree(
  tree: RbacUnifiedTree,
  query: string,
): RbacUnifiedTree {
  const normalized = query.trim();
  if (!normalized) {
    return tree;
  }

  const branches: RbacUnifiedTree["branches"] = [];

  for (const branch of tree.branches) {
    if (branch.kind === "directRole") {
      const role = filterRoleNode(branch.role, normalized);
      if (role) {
        branches.push({ ...branch, role });
      }
      continue;
    }

    const roles = branch.group.roles
      .map((role) => filterRoleNode(role, normalized))
      .filter((role): role is RbacTreeRoleNode => role !== null);

    if (
      roles.length === 0 &&
      !matchesQuery(branch.group.groupName, normalized) &&
      !(branch.group.description && matchesQuery(branch.group.description, normalized))
    ) {
      continue;
    }

    branches.push({ ...branch, group: { ...branch.group, roles } });
  }

  return { branches };
}

export function filterRolesTree(tree: RbacRolesTree, query: string): RbacRolesTree {
  const normalized = query.trim();
  if (!normalized) {
    return tree;
  }

  return {
    roles: tree.roles
      .map((role) => filterRoleNode(role, normalized))
      .filter((role): role is RbacTreeRoleNode => role !== null),
  };
}

export function filterGroupsTree(tree: RbacGroupsTree, query: string): RbacGroupsTree {
  const normalized = query.trim();
  if (!normalized) {
    return tree;
  }

  return {
    groups: tree.groups.flatMap((group) => {
      const roles = group.roles
        .map((role) => filterRoleNode(role, normalized))
        .filter((role): role is RbacTreeRoleNode => role !== null);

      if (
        roles.length === 0 &&
        !matchesQuery(group.groupName, normalized) &&
        !(group.description && matchesQuery(group.description, normalized))
      ) {
        return [];
      }

      return [{ ...group, roles }];
    }),
  };
}

function filterRoleNode(
  role: RbacTreeRoleNode,
  query: string,
): RbacTreeRoleNode | null {
  const apps = role.apps
    .map((app) => filterAppNode(app, query))
    .filter((app): app is RbacTreeAppNode => app !== null);

  const roleMatches =
    matchesQuery(role.roleName, query) ||
    role.sourceLabels.some((label) => matchesQuery(label, query));

  if (!roleMatches && apps.length === 0) {
    return null;
  }

  return { ...role, apps };
}

function filterAppNode(app: RbacTreeAppNode, query: string): RbacTreeAppNode | null {
  const permissions = app.permissions.filter(
    (permission) =>
      matchesQuery(permission.code, query) || matchesQuery(permission.name, query),
  );

  if (!matchesQuery(app.appName, query) && permissions.length === 0) {
    return null;
  }

  return { ...app, permissions };
}

export function countAccessTreeStats(profile: UserAccessProfile) {
  const permissionCodes = new Set<string>();
  profile.roles.forEach((role) => {
    role.permissions.forEach((permission) => permissionCodes.add(permission.code));
  });

  const appIds = new Set<string>();
  profile.roles.forEach((role) => {
    role.apps.forEach((app) => appIds.add(app.id));
  });

  return {
    roleCount: profile.roles.length,
    groupCount: profile.groups.length,
    permissionCount: permissionCodes.size,
    appCount: appIds.size,
  };
}
