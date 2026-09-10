/**
 * Actions present in `allowed_actions` that are NOT workflow transitions.
 * Calling POST /transitions/{action} for these yields invalid_transition.
 */
export const NON_TRANSITION_ACTIONS = new Set(["view", "edit"]);

/** Detail page already shows the request — `view` must not become a button. */
export const DETAIL_HIDDEN_ACTIONS = new Set(["view"]);

export function isTransitionAction(action: string): boolean {
  return !NON_TRANSITION_ACTIONS.has(action.trim());
}

/** Filter actions for the detail ActionBar (render-only, no local state machine). */
export function filterDetailBarActions(actions: readonly string[]): string[] {
  return actions.filter((action) => !DETAIL_HIDDEN_ACTIONS.has(action.trim()));
}
