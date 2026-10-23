import type { ActivityViewerProps } from "@delpi/plugin-ui/index";

import type { ConversationDisplayTurn } from "../ui/ConversationTimeline";
import type { DeliaPresentation } from "../api/presentation";

/**
 * Isolated frontend demo mode — presentation exercise only.
 *
 * Hard gate: the feature exists ONLY when the bundle runs in Vite dev
 * mode (`import.meta.env.DEV`) or was deliberately built with
 * `VITE_DELIA_DEMO=1` (a preview/environment decision). Even then it
 * activates only via the explicit `?delia-demo=<scenario>` query param.
 * Production builds never enter this path.
 *
 * Demo turns never touch the network: no `/interaction/turns`, no
 * provider, no external action. Fixtures are clearly marked as
 * simulated and never claim GROUNDED provenance.
 */

export type DeliaDemoScenario =
  | "simple"
  | "long"
  | "clarification"
  | "source_unavailable"
  | "authz_denied"
  | "precondition"
  | "confirmation"
  | "error"
  | "loading"
  | "activity"
  | "markdown_code"
  | "markdown_full";

export const DELIA_DEMO_BANNER = "Modo demonstração — dados simulados";

export const DELIA_DEMO_QUERY_PARAM = "delia-demo";

/** Short, honest simulated latency so the real loading badge shows. */
const DEMO_LATENCY_MS = 350;
const DEMO_LOADING_LATENCY_MS = 1500;

const DEMO_LIMITATIONS = [
  "resposta simulada — nenhum dado operacional consultado",
];

function demoPresentation(
  messageKind: DeliaPresentation["messageKind"],
  blocks: DeliaPresentation["blocks"] = [],
  allowedInteractions: DeliaPresentation["allowedInteractions"] = [
    "reply",
  ],
): DeliaPresentation {
  return {
    messageKind,
    semanticStatus: null,
    groundingStatus: "NON_GROUNDED",
    blocks,
    allowedInteractions,
  };
}

const DEFAULT_TEXT =
  "Olá! Esta é uma resposta de demonstração da DÉLIA. Estamos testando " +
  "a interface conversacional. Nenhuma informação operacional foi " +
  "consultada e nenhuma ação foi executada.";

const LONG_TEXT = [
  DEFAULT_TEXT,
  "Este é um cenário de resposta longa para exercitar quebras de " +
    "linha, parágrafos e wrapping dentro da coluna de leitura.",
  "Segundo parágrafo de demonstração: a timeline deve rolar " +
    "independentemente do composer, e o conteúdo extenso não deve " +
    "produzir overflow horizontal nem esticar texto pela largura toda " +
    "de um monitor ultrawide.",
  "Terceiro parágrafo: estados semânticos, provenance e limitações " +
    "continuam visuais e honestos — esta resposta é explicitamente " +
    "marcada como simulação e não é uma consulta real.",
].join("\n\n");

export type DemoTurnOutcome = {
  /** Simulated latency before the response lands. */
  delayMs: number;
  /** When set, the simulated turn fails and the draft must be kept. */
  error?: string;
  /** DÉLIA turn to append after the user turn (absent on error). */
  deliaTurn?: Omit<ConversationDisplayTurn, "id">;
};

function deliaTurn(
  content: string,
  presentation?: DeliaPresentation,
  extra?: Partial<ConversationDisplayTurn>,
): Omit<ConversationDisplayTurn, "id"> {
  return {
    role: "delia",
    content,
    epistemicClass: "OBSERVATION",
    limitations: DEMO_LIMITATIONS,
    groundingStatus: "NON_GROUNDED",
    provenance: null,
    presentation,
    ...extra,
  };
}

/** Fictitious multi-step/multi-specialist activity — every element is
 *  explicitly marked as simulation; no real tool ever ran. */
const DEMO_ACTIVITY_VIEW: ActivityViewerProps = {
  title: "Atividade concluída (simulação)",
  state: "completed",
  steps: [
    { id: "demo-1", label: "Solicitação recebida", state: "completed" },
    {
      id: "demo-2",
      label: "Capacidade acionada (simulação)",
      state: "completed",
      capabilityLabel: "Consultar indicador operacional",
      sourceLabel: "especialista-demo-a",
    },
    {
      id: "demo-3",
      label: "Fonte consultada (simulação)",
      state: "completed",
      sourceLabel: "especialista-demo-b",
      timestampLabel: "simulado",
    },
    {
      id: "demo-4",
      label: "Etapa com falha (simulação)",
      state: "failed",
      description: "Falha fictícia para exercitar o estado visual.",
    },
    {
      id: "demo-5",
      label: "Etapa aguardando (simulação)",
      state: "pending",
    },
  ],
  sources: [
    {
      id: "demo-src-1",
      label: "fonte-demo-erp",
      statusLabel: "consultada (simulação)",
    },
    {
      id: "demo-src-2",
      label: "fonte-demo-indicadores",
      statusLabel: "sem dados (simulação)",
    },
  ],
  outcome: {
    label: "SIMULAÇÃO — nenhuma ferramenta real executada.",
    tone: "warning",
    persistent: true,
  },
};

const DEMO_MARKDOWN_CODE_SOURCE = [
  "Segue um bloco SQL de exemplo:",
  "",
  "```sql",
  "SELECT produto, SUM(quantidade)",
  "FROM producao",
  "WHERE quantidade > 100",
  "GROUP BY produto;",
  "```",
  "",
  "Dois blocos independentes, um sem linguagem declarada:",
  "",
  "```json",
  '{"produto": "A", "quantidade": 42}',
  "```",
  "",
  "```",
  "linha sem linguagem declarada",
  "```",
  "",
  "Linguagem fora da allowlist:",
  "",
  "```cobol",
  "DISPLAY TOTAL.",
  "```",
  "",
  "Linha longa para scroll horizontal interno:",
  "",
  "```text",
  "X".padEnd(300, "X"),
  "```",
  "",
  "Conteúdo HTML literal dentro da fence:",
  "",
  "```html",
  '<script>alert("demo")</script><img src=x onerror=alert(1)>',
  "```",
].join("\n");

const DEMO_MARKDOWN_CODE_FALLBACK =
  "Resposta simulada com exemplos de código (demonstração — veja os blocos).";

// QA-only fixture for admitted prose structure (spec 96 §17): headings,
// bold, ordered/unordered lists and a code block — never real backend
// output.
const DEMO_MARKDOWN_FULL_SOURCE = [
  "## Resumo da operação",
  "",
  "O turno estruturado preserva **fatos**, IDs e unidades.",
  "",
  "### Itens encontrados",
  "",
  "- Primeiro item com **ênfase**",
  "- Segundo item com valor 42",
  "- Terceiro item",
  "",
  "### Próximos passos",
  "",
  "1. Revisar a evidência",
  "2. Confirmar a proveniência",
  "3. Registrar a limitação",
  "",
  "Trecho técnico inerte:",
  "",
  "```text",
  "SELECT campo FROM tabela WHERE id = 1;",
  "```",
  "",
  "Nenhum link é emitido sem fonte admitida.",
].join("\n");

const DEMO_MARKDOWN_FULL_FALLBACK =
  "Resposta simulada com estrutura Markdown (demonstração).";

const SCENARIO_OUTCOMES: Record<DeliaDemoScenario, DemoTurnOutcome> = {
  simple: {
    delayMs: DEMO_LATENCY_MS,
    deliaTurn: deliaTurn(
      DEFAULT_TEXT,
      demoPresentation("RESULT", [{ kind: "text", text: DEFAULT_TEXT }]),
    ),
  },
  long: {
    delayMs: DEMO_LATENCY_MS,
    deliaTurn: deliaTurn(
      LONG_TEXT,
      demoPresentation("RESULT", [{ kind: "text", text: LONG_TEXT }]),
    ),
  },
  clarification: {
    delayMs: DEMO_LATENCY_MS,
    deliaTurn: deliaTurn(
      "Para ajudar você com precisão, preciso de um esclarecimento. " +
        "(resposta simulada — demonstração)",
      demoPresentation("CLARIFICATION_REQUIRED"),
    ),
  },
  source_unavailable: {
    delayMs: DEMO_LATENCY_MS,
    deliaTurn: deliaTurn(
      "A fonte necessária para esta consulta está indisponível neste " +
        "momento; nenhum resultado operacional foi verificado nesta " +
        "tentativa. (resposta simulada — demonstração)",
      demoPresentation("SOURCE_UNAVAILABLE"),
    ),
  },
  authz_denied: {
    delayMs: DEMO_LATENCY_MS,
    deliaTurn: deliaTurn(
      "Você não possui autorização para esta operação. " +
        "(resposta simulada — demonstração)",
      demoPresentation("AUTHZ_DENIED"),
    ),
  },
  precondition: {
    delayMs: DEMO_LATENCY_MS,
    deliaTurn: deliaTurn(
      "Não foi possível concluir. A fonte informou: " +
        "demo_precondition_required.",
      demoPresentation("PRECONDITION_REQUIRED", [
        { kind: "text", text: "Não foi possível concluir." },
        {
          kind: "notice",
          role: "owner_hint",
          text: "demo_precondition_required.",
        },
      ]),
    ),
  },
  // Visual-only governed confirmation — the digest fields are marked
  // demo values and are never echoed to any backend.
  confirmation: {
    delayMs: DEMO_LATENCY_MS,
    deliaTurn: deliaTurn(
      "Esta é uma confirmação governada simulada. Confirmar ou " +
        "Cancelar produzem apenas um retorno visual de demonstração.",
      demoPresentation("CONFIRMATION_REQUIRED", [], [
        "reply",
        "confirm",
        "reject",
      ]),
      {
        confirmationRequest: {
          session_id: "demo-session",
          proposal_digest: "demo_digest_not_authoritative",
          preview_fingerprint: "demo_fingerprint_not_authoritative",
        },
      },
    ),
  },
  // QA-only fixture for the shared ConversationCodeBlock (spec 96 §17):
  // exercises admitted presentation.v2 wiring — never real backend output.
  markdown_code: {
    delayMs: DEMO_LATENCY_MS,
    deliaTurn: deliaTurn(
      DEMO_MARKDOWN_CODE_FALLBACK,
      demoPresentation("RESULT", [
        { kind: "text", text: DEMO_MARKDOWN_CODE_FALLBACK },
      ]),
      {
        contentFormat: "markdown_safe",
        markdownSource: DEMO_MARKDOWN_CODE_SOURCE,
        authorizedLinks: [],
      },
    ),
  },
  markdown_full: {
    delayMs: DEMO_LATENCY_MS,
    deliaTurn: deliaTurn(
      DEMO_MARKDOWN_FULL_FALLBACK,
      demoPresentation("RESULT", [
        { kind: "text", text: DEMO_MARKDOWN_FULL_FALLBACK },
      ]),
      {
        contentFormat: "markdown_safe",
        markdownSource: DEMO_MARKDOWN_FULL_SOURCE,
        authorizedLinks: [],
      },
    ),
  },
  activity: {
    delayMs: DEMO_LATENCY_MS,
    deliaTurn: deliaTurn(
      DEFAULT_TEXT +
        " (cenário de atividade simulada — expanda a linha de atividade)",
      demoPresentation("RESULT", [{ kind: "text", text: DEFAULT_TEXT }]),
      { activityView: DEMO_ACTIVITY_VIEW },
    ),
  },
  error: {
    delayMs: DEMO_LATENCY_MS,
    error: "Falha simulada de demonstração — rascunho preservado.",
  },
  loading: {
    delayMs: DEMO_LOADING_LATENCY_MS,
    deliaTurn: deliaTurn(
      DEFAULT_TEXT + " (cenário de espera simulada)",
      demoPresentation("RESULT", [
        {
          kind: "text",
          text: DEFAULT_TEXT + " (cenário de espera simulada)",
        },
      ]),
    ),
  },
};

/** Whether this bundle is even allowed to entertain demo mode. */
export function isDemoAllowed(
  env: Pick<ImportMetaEnv, "DEV"> & { VITE_DELIA_DEMO?: string } =
    import.meta.env,
): boolean {
  return Boolean(env.DEV) || env.VITE_DELIA_DEMO === "1";
}

/**
 * Resolve the active demo scenario from the URL query. Returns `null`
 * when the gate is closed or the param is absent. Unknown values fall
 * back to the simple scenario — demo is never silently activated.
 */
export function resolveDemoScenario(
  search: string,
): DeliaDemoScenario | null {
  if (!isDemoAllowed()) return null;
  // Accept either a bare query string ("?a=b") or a path with query
  // ("/?a=b") — the caller normally passes `location.search`.
  const queryIndex = search.indexOf("?");
  const rawSearch =
    queryIndex >= 0 ? search.slice(queryIndex + 1) : search;
  const params = new URLSearchParams(rawSearch);
  if (!params.has(DELIA_DEMO_QUERY_PARAM)) return null;
  const raw = params.get(DELIA_DEMO_QUERY_PARAM) || "simple";
  return raw in SCENARIO_OUTCOMES
    ? (raw as DeliaDemoScenario)
    : "simple";
}

export function demoTurnOutcome(
  scenario: DeliaDemoScenario,
): DemoTurnOutcome {
  return SCENARIO_OUTCOMES[scenario];
}

/** Visual-only acknowledgement for a demo confirmation decision. */
export function demoConfirmationAck(
  decision: "CONFIRM" | "REJECT",
): Omit<ConversationDisplayTurn, "id"> {
  const verb =
    decision === "CONFIRM" ? "confirmada" : "cancelada";
  return deliaTurn(
    `Operação ${verb} apenas visualmente — nenhuma decisão foi ` +
      "enviada a nenhum sistema. (resposta simulada — demonstração)",
    demoPresentation("RESULT"),
  );
}
