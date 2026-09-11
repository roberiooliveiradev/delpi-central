import type { AdminHubOpenLayer } from "../utils/adminHubUiState";

const BLOCKING_LAYERS: ReadonlySet<AdminHubOpenLayer> = new Set([
  "menu",
  "summary",
  "inspector",
  "confirm",
  "modal",
  "panel",
]);

export function isHubInteractionBlocking(input: {
  linkMode: boolean;
  dragging: boolean;
  openLayer: AdminHubOpenLayer;
  documentHidden?: boolean;
}): boolean {
  if (input.documentHidden) return true;
  if (input.linkMode) return true;
  if (input.dragging) return true;
  return BLOCKING_LAYERS.has(input.openLayer);
}
