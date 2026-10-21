import type { ConversationStarterSuggestion } from "@delpi/plugin-ui/index";

import type { DeliaDemoScenario } from "../demo/demoMode";

/**
 * F02-A — starter suggestion fixtures for governed QA (doc 93 §14).
 *
 * These four questions are PRESENTATION FIXTURES, not a capability
 * allowlist: each is an honest discovery/orientation question the user
 * may edit freely before sending. They never claim a specific tool,
 * source or action is authorized for the session — the backend remains
 * the authority on what actually executes.
 *
 * Production gate (spec §14): without a legitimate per-session
 * eligibility projection, the list ships EMPTY. The fixtures appear
 * only when the governed QA harness is active end-to-end — a bundle
 * admitted via `isDemoAllowed()` AND an explicit `?delia-demo=`
 * scenario in the URL (the same admission demo mode uses). No new
 * permission, no new flag.
 */
export const DELIA_STARTER_SUGGESTIONS: readonly ConversationStarterSuggestion[] =
  [
    {
      id: "data-formats",
      title: "Formatos de dados",
      description: "Ver o que posso consultar",
      draftText: "Quais formatos de dados estão disponíveis?",
      iconKey: "data",
    },
    {
      id: "sipoc-concept",
      title: "O que é SIPOC?",
      description: "Entenda o conceito de processos",
      draftText: "O que é SIPOC?",
      iconKey: "concept",
    },
    {
      id: "available-sources",
      title: "Fontes disponíveis",
      description: "Descobrir o que seu acesso permite",
      draftText: "Quais fontes de informação posso consultar com meu acesso?",
      iconKey: "sources",
    },
    {
      id: "operational-analysis",
      title: "Tipos de análise",
      description: "Explorar o que a DÉLIA pode fazer agora",
      draftText:
        "Que tipos de análise operacional você consegue realizar agora?",
      iconKey: "analysis",
    },
  ];

/**
 * Resolve the suggestions to render for this session. Returns `[]`
 * whenever the governed QA mode is not explicitly active — the
 * reception and composer stay untouched (fail-closed).
 */
export function resolveStarterSuggestions(
  demoScenario: DeliaDemoScenario | null,
): readonly ConversationStarterSuggestion[] {
  return demoScenario != null ? DELIA_STARTER_SUGGESTIONS : [];
}
