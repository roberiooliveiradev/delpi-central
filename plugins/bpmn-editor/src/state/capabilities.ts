/**
 * Capabilities derivadas de permissões + estado do modelo.
 * Autorização efetiva é backend-first; isto é apenas UX gating.
 */

export type Capabilities = {
  view: boolean;
  edit: boolean;
  manage: boolean;
};

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
