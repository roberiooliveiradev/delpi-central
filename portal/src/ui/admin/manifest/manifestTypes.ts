// portal/src/ui/admin/manifest/manifestTypes.ts

export type ManifestType = "microfrontend" | "iframe" | "backend-only";

export type ManifestPermission = {
  code: string;
  name?: string | null;
  description?: string | null;
  module: string;
};

export type ManifestRoute = {
  path: string;
  label?: string | null;
  permission?: string | null;
  icon?: string | null;
  entry?: string | null;
  order?: number | null;
  showInMenu?: boolean | null;
};

export type ManifestUI = {
  renderMode?: "embedded" | "external" | "federated";
};

export type ManifestSchema = {
  schemaVersion: "1.0.0";
  id: string;
  name: string;
  description?: string | null;
  icon?: string | null;
  version: string;
  type: ManifestType;
  basePath: string;
  entry?: string | null;
  permissions: ManifestPermission[];
  routes: ManifestRoute[];
  backend?: Record<string, unknown>;
  lifecycle?: Record<string, unknown>;
  security?: Record<string, unknown>;
  observability?: Record<string, unknown>;
  ui?: ManifestUI;
  dependencies?: string[];
};

export type LocalError = { path: string; message: string };

export type ManifestEditorTab =
  | "base"
  | "ui"
  | "backend"
  | "permissions"
  | "routes"
  | "access"
  | "preview";
