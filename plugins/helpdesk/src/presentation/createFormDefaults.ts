/** Etapa 1 — catalog default resolution for the create form.
 *
 * Canonical rule (GLPI `Ticket::getDefaultValues`): a select may only be
 * prefilled by (1) the user's own draft or (2) a proven GLPI default —
 * NEVER by "the first row the catalog returned". Category has no GLPI
 * default (0 = none) so it must stay empty until the user picks.
 */

export type CatalogOption = { id: number; name: string };

/** GLPI canonical defaults proven in `Ticket::getDefaultValues` +
 * entity config (Delpi → incident) + session getFullSession. */
export const GLPI_DEFAULT_URGENCY_ID = 3;
export const GLPI_DEFAULT_IMPACT_ID = 3;
export const GLPI_DEFAULT_TYPE_ID = 1;

export function pickCatalogDefault(
  items: CatalogOption[],
  current: string,
  draftValue: string | undefined,
  canonicalDefaultId: number | null,
): string {
  if (current && items.some((item) => String(item.id) === current)) return current;
  if (draftValue && items.some((item) => String(item.id) === draftValue)) {
    return draftValue;
  }
  if (
    canonicalDefaultId !== null &&
    items.some((item) => item.id === canonicalDefaultId)
  ) {
    return String(canonicalDefaultId);
  }
  return "";
}
