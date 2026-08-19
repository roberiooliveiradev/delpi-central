import type { InteractionInboxFilter } from "../../api/interactionRoomsApi";

const FILTERS = new Set(["all", "unread", "mentioned", "process", "wall"]);

export function parseInteractionRoomSearch(search: string | undefined): {
  filter: InteractionInboxFilter;
  q: string;
} {
  const params = new URLSearchParams(
    (search ?? "").startsWith("?") ? search.slice(1) : search ?? "",
  );
  const raw = (params.get("filter") ?? "all").trim().toLowerCase();
  const filter = FILTERS.has(raw) ? raw : "all";
  return { filter, q: (params.get("q") ?? "").trim() };
}

export function buildInteractionRoomSearch(options: {
  filter: InteractionInboxFilter;
  q: string;
}): string {
  const params = new URLSearchParams();
  if (options.filter && options.filter !== "all") {
    params.set("filter", options.filter);
  }
  const q = options.q.trim();
  if (q) params.set("q", q);
  const raw = params.toString();
  return raw ? `?${raw}` : "";
}
