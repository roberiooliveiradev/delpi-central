import type { ConversationStarterSuggestion } from "@delpi/plugin-ui/index";

/**
 * F02-A — starter suggestion fixtures for governed QA (doc 93 §14).
 *
 * These four questions are PRESENTATION FIXTURES, not a capability
 * allowlist: each is an honest discovery/orientation question the user
 * may edit freely before sending. They never claim a specific tool,
 * source or action is authorized for the session — the backend remains
 * the authority on what actually executes.
 *
 * Visibility (spec §16, F02-A-R1): the four questions are shown by
 * default in production to every user already admitted to the app —
 * upstream `delia.access` admission is the only gate, no demo flag,
 * no query param, no invented permission. They remain presentation
 * questions, never capability claims: the backend still decides what
 * actually executes when the user sends the edited draft.
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
 * Resolve the suggestions to render for this session. Single seam for
 * the future per-session eligibility projection (spec §16): today the
 * authorized default list is returned to every admitted user.
 */
export function resolveStarterSuggestions(): readonly ConversationStarterSuggestion[] {
  return DELIA_STARTER_SUGGESTIONS;
}
