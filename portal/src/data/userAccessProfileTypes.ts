// portal/src/data/userAccessProfileTypes.ts

export type UserAccessProfilePermission = {
  code: string;
  name: string;
  description?: string | null;
  module?: string | null;
};

export type UserAccessProfileRoute = {
  path: string;
  label: string;
  permission: string;
  showInMenu: boolean;
};

export type UserAccessProfileApp = {
  id: string;
  name: string;
  basePath: string;
  icon?: string | null;
  type?: string | null;
  routes: UserAccessProfileRoute[];
};

export type UserAccessRoleSource =
  | { type: "direct" }
  | { type: "group"; groupName: string; groupId?: string };

export type UserAccessProfileRole = {
  id: string;
  name: string;
  description?: string | null;
  sources: UserAccessRoleSource[];
  permissions: UserAccessProfilePermission[];
  apps: UserAccessProfileApp[];
};

export type UserAccessProfileGroup = {
  id: string;
  name: string;
  description?: string | null;
  roles: string[];
};

export type UserAccessProfile = {
  isSuperadmin: boolean;
  roles: UserAccessProfileRole[];
  groups: UserAccessProfileGroup[];
  effectivePermissions: string[];
  effectiveApps: UserAccessProfileApp[];
};
