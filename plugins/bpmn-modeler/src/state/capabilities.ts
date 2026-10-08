/**
 * Capabilities derivadas de permissões + estado do modelo.
 * Autorização efetiva é backend-first; isto é apenas UX gating.
 */

export type Capabilities = {
  view: boolean;
  edit: boolean;
  manage: boolean;
};

export function capabilitiesFromPermissions(
  permissions: readonly string[] | undefined,
): Capabilities {
  const set = new Set(permissions ?? []);
  return {
    view: set.has("bpmn-modeler.view") || set.has("bpmn-modeler.edit") || set.has("bpmn-modeler.manage"),
    edit: set.has("bpmn-modeler.edit") || set.has("bpmn-modeler.manage"),
    manage: set.has("bpmn-modeler.manage"),
  };
}

export type ReadOnlyReason =
  | "ARCHIVED"
  | "NO_EDIT_PERMISSION"
  | "UNSUPPORTED_MUST_UNDERSTAND"
  | "UNSUPPORTED_EXTENSION_SERIALIZATION"
  | "EDITOR_CAPABILITY_FAILURE"
  | "REVISION_VIEW"
  | null;

export function editableMode(
  capabilities: Capabilities,
  archived: boolean,
  readOnlyReason: ReadOnlyReason,
): boolean {
  return (
    capabilities.edit && !archived && readOnlyReason === null
  );
}
