import type { ConversationQueueItem } from "@delpi/plugin-ui/index";

import { isDemoAllowed } from "./demoMode";

/**
 * Doc 71 (F03-A) — isolated QA fixture for the ConversationQueue
 * presentation surface. Same gate as demo mode: dev builds or bundles
 * deliberately built with `VITE_DELIA_DEMO=1`, plus the explicit
 * `?delia-demo-queue=<variant>` query param. Production bundles never
 * admit it and no fixture item is ever shown in production.
 *
 * The fixture exercises visual states only — reorder/remove callbacks
 * mutate local state and claim nothing about a real queue owner.
 */

export const DELIA_QUEUE_DEMO_QUERY_PARAM = "delia-demo-queue";

export type DeliaQueueDemoVariant =
  | "pending"
  | "one"
  | "blocked"
  | "loading"
  | "error"
  | "unavailable";

export type DeliaQueueDemoState = {
  items: ConversationQueueItem[];
  loading?: boolean;
  unavailable?: boolean;
  error?: string | null;
};

const DEMO_ITEMS: ConversationQueueItem[] = [
  {
    id: "demo-q1",
    label: "Comparar indicadores de SC e ES no período",
    ordinal: 1,
    status: "queued",
    canMoveDown: true,
    canRemove: true,
  },
  {
    id: "demo-q2",
    label: "Consultar chamados de TI abertos esta semana",
    ordinal: 2,
    status: "queued",
    canMoveUp: true,
    canMoveDown: true,
    canRemove: true,
  },
  {
    id: "demo-q3",
    label: "Resumir principais desvios do mês anterior",
    ordinal: 3,
    status: "queued",
    canMoveUp: true,
    canRemove: true,
  },
];

const DEMO_BLOCKED_ITEMS: ConversationQueueItem[] = [
  {
    id: "demo-b1",
    label: "Analisar desvios da fábrica no mês",
    ordinal: 1,
    status: "queued",
    canMoveDown: true,
    canRemove: true,
  },
  {
    id: "demo-b2",
    label: "Consolidar custo por centro de trabalho",
    ordinal: 2,
    status: "blocked",
    reason: "aguardando a solicitação anterior",
    canMoveUp: true,
    canRemove: false,
  },
];

function demoStateFor(variant: DeliaQueueDemoVariant): DeliaQueueDemoState {
  switch (variant) {
    case "one":
      return { items: [DEMO_ITEMS[0]!] };
    case "blocked":
      return { items: DEMO_BLOCKED_ITEMS };
    case "loading":
      return { items: [], loading: true };
    case "error":
      return { items: [], error: "Não foi possível ler a fila agora." };
    case "unavailable":
      return { items: [], unavailable: true };
    case "pending":
    default:
      return { items: DEMO_ITEMS };
  }
}

/**
 * Resolve the QA queue fixture from the URL query. Returns `null`
 * unless the demo gate is open AND the param is present.
 */
export function resolveQueueDemo(
  search: string,
  env: Pick<ImportMetaEnv, "DEV"> & { VITE_DELIA_DEMO?: string } =
    import.meta.env,
): DeliaQueueDemoState | null {
  if (!isDemoAllowed(env)) return null;
  const queryIndex = search.indexOf("?");
  const rawSearch =
    queryIndex >= 0 ? search.slice(queryIndex + 1) : search;
  const params = new URLSearchParams(rawSearch);
  if (!params.has(DELIA_QUEUE_DEMO_QUERY_PARAM)) return null;
  const raw = params.get(DELIA_QUEUE_DEMO_QUERY_PARAM) || "pending";
  const variant = (
    ["pending", "one", "blocked", "loading", "error", "unavailable"].includes(
      raw,
    )
      ? raw
      : "pending"
  ) as DeliaQueueDemoVariant;
  return demoStateFor(variant);
}

/** Fixture-only intents: reorder/remove mutate local demo state. */
export function demoMoveItem(
  items: ConversationQueueItem[],
  itemId: string,
  direction: "up" | "down",
): ConversationQueueItem[] {
  const index = items.findIndex((i) => i.id === itemId);
  const target = direction === "up" ? index - 1 : index + 1;
  if (index < 0 || target < 0 || target >= items.length) return items;
  const next = [...items];
  const [moved] = next.splice(index, 1);
  next.splice(target, 0, moved!);
  return next.map((item, i) => ({
    ...item,
    ordinal: i + 1,
    canMoveUp: i > 0 ? true : undefined,
    canMoveDown: i < next.length - 1 ? true : undefined,
  }));
}

export function demoRemoveItem(
  items: ConversationQueueItem[],
  itemId: string,
): ConversationQueueItem[] {
  return items
    .filter((i) => i.id !== itemId)
    .map((item, i) => ({ ...item, ordinal: i + 1 }));
}
