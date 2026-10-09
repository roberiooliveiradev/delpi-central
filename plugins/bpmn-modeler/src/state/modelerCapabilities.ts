import type { Capabilities } from "@delpi/bpmn-editor";

/**
 * Mapeamento `bpmn-modeler.*` → capabilities de UX (gating visual apenas;
 * autorização efetiva permanece backend-first).
 */
export function capabilitiesFromPermissions(
  permissions: readonly string[] | undefined,
): Capabilities {
  const set = new Set(permissions ?? []);
  return {
    view:
      set.has("bpmn-modeler.view") ||
      set.has("bpmn-modeler.edit") ||
      set.has("bpmn-modeler.manage"),
    edit: set.has("bpmn-modeler.edit") || set.has("bpmn-modeler.manage"),
    manage: set.has("bpmn-modeler.manage"),
  };
}
