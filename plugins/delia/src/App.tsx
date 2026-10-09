import { useEffect, useRef, useState } from "react";
import type { UIEvent as ReactUIEvent } from "react";

import { DELIA_ROOT_CLASS, DeliaPageHeader } from "./ui/deliaUi";
import { DeliaReception } from "./ui/DeliaReception";
import { DeliaComposer } from "./ui/DeliaComposer";
import { ConversationTimeline } from "./ui/ConversationTimeline";
import type { ConversationDisplayTurn } from "./ui/ConversationTimeline";
import {
  DeliaInteractionError,
  buildInteractionContext,
  submitInteractionTurn,
} from "./api/interactionClient";
import type {
  DeliaConfirmationRequest,
  DeliaWorkspaceContext,
} from "./api/interactionClient";
import { DeliaLoadingBadge } from "./ui/deliaUi";

/** Host props from Portal AppHost — presentation/transport only. */
export type AppProps = {
  getAccessToken?: () => string | undefined;
  basePath?: string;
  pathname?: string;
  search?: string;
  alternateEntry?: string;
  appRoutes?: Array<{ path: string; entry?: string; openInNewTab?: boolean }>;
  routeLabel?: string;
  /** Frontend presentation hint only — never backend authorization authority. */
  permissions?: string[];
  /** Frontend presentation hint only — never backend authorization authority. */
  isSuperadmin?: boolean;
  /** Bounded untrusted workspace hint getter (§6.130) — called per
   *  turn so the freshest published context is sent. Never authority. */
  getWorkspaceContext?: () => DeliaWorkspaceContext | null;
};

const TOKEN_UNAVAILABLE_MESSAGE =
  "Token de acesso indisponível. Recarregue pelo Portal.";

/** Autoscroll engagement threshold — only follow new turns when the
 *  reader is already near the end (doc 69 §10). */
const NEAR_BOTTOM_THRESHOLD_PX = 96;

/**
 * C3-INTERACTION-RUNTIME-01 + C3-INTERACTION-CONTINUITY-01 +
 * DELIA-UX-S2-RECEPTION-CONVERSATION-SHELL-01.
 *
 * Bounded transient multi-turn interaction: rendered turns are kept in
 * React memory only and resent as untrusted prior context on each new
 * turn. No browser storage and no backend persistence — a reload
 * resets the conversation. permissions / isSuperadmin remain host
 * presentation hints and are never sent as backend authority.
 *
 * The same component serves the full page and the global dock: a
 * single shell (reception → timeline → composer) adapts to the
 * container width — no parallel runtime, no fake capabilities.
 */
export default function App({
  pathname,
  basePath,
  routeLabel,
  getAccessToken,
  getWorkspaceContext,
  permissions: _permissions,
  isSuperadmin: _isSuperadmin,
}: AppProps) {
  void _permissions;
  void _isSuperadmin;

  const hostPath = pathname || basePath || "/apps/delia";

  const [input, setInput] = useState("");
  const [turns, setTurns] = useState<ConversationDisplayTurn[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const scrollRegionRef = useRef<HTMLDivElement | null>(null);
  const turnsEndRef = useRef<HTMLDivElement | null>(null);
  const nearBottomRef = useRef(true);

  useEffect(() => {
    const end = turnsEndRef.current;
    const last = turns[turns.length - 1];
    // Follow the log only when the user just sent a turn or was
    // already reading near the end — never hijack scroll position.
    if (!end || !(nearBottomRef.current || last?.role === "user")) {
      return;
    }
    if (typeof end.scrollIntoView === "function") {
      end.scrollIntoView({ block: "end" });
    }
  }, [turns, loading]);

  useEffect(
    () => () => {
      abortRef.current?.abort();
    },
    [],
  );

  function handleTimelineScroll(event: ReactUIEvent<HTMLDivElement>) {
    const el = event.currentTarget;
    nearBottomRef.current =
      el.scrollHeight - el.scrollTop - el.clientHeight <
      NEAR_BOTTOM_THRESHOLD_PX;
  }

  async function sendTurn(
    value: string,
    confirmation?: {
      decision: "CONFIRM" | "REJECT";
      proposal_digest: string;
      preview_fingerprint: string;
      session_id: string;
    },
  ) {
    if (!getAccessToken || !getAccessToken()) {
      setError(TOKEN_UNAVAILABLE_MESSAGE);
      return;
    }

    setLoading(true);
    setError(null);
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const result = await submitInteractionTurn(value, {
        getAccessToken,
        signal: controller.signal,
        context: buildInteractionContext(turns),
        workspace: getWorkspaceContext?.() ?? undefined,
        confirmation,
      });
      setTurns((previous) => [
        // A submitted decision consumes the earlier pending card —
        // the backend is the authority; this is presentation only.
        ...previous.map((turn) =>
          turn.confirmationRequest
            ? { ...turn, confirmationAnswered: true }
            : turn,
        ),
        { id: result.user_turn_id, role: "user", content: value },
        {
          id: result.result_turn_id,
          role: "delia",
          content: result.content,
          epistemicClass: result.epistemic_class,
          limitations: result.limitations,
          groundingStatus: result.grounding_status,
          provenance: result.provenance,
          confirmationRequest: result.confirmation_request,
          presentation: result.presentation,
        },
      ]);
      setInput("");
    } catch (submitError) {
      if (
        submitError instanceof Error &&
        submitError.name === "AbortError"
      ) {
        return;
      }
      // The draft stays in the composer — a failed send never loses
      // what the user typed.
      setError(
        submitError instanceof DeliaInteractionError
          ? submitError.message
          : "Erro inesperado ao falar com a DÉLIA.",
      );
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit() {
    const value = input.trim();
    if (!value || loading) return;
    void sendTurn(value);
  }

  /**
   * Governed-write confirmation (ledger §6.126): the MFE echoes the
   * bounded digests back verbatim — it never sees the raw owner
   * handle and never makes any authorization decision.
   */
  function handleConfirmation(
    request: DeliaConfirmationRequest,
    decision: "CONFIRM" | "REJECT",
  ) {
    if (loading) return;
    const label =
      decision === "CONFIRM"
        ? "Confirmação da operação solicitada."
        : "Cancelamento da operação solicitada.";
    void sendTurn(label, {
      decision,
      proposal_digest: request.proposal_digest,
      preview_fingerprint: request.preview_fingerprint,
      session_id: request.session_id,
    });
  }

  return (
    <div className={`${DELIA_ROOT_CLASS} dashboard-page`}>
      <main className="delia-page-stack" aria-label="DÉLIA">
        <DeliaPageHeader
          title="DÉLIA"
          subtitle="Converse com a inteligência operacional da DELPI. A conversa é mantida apenas nesta tela e não é salva."
        />

        <section
          className="delia-interaction"
          aria-label="Interação com a DÉLIA"
        >
          <div
            className="delia-interaction__body"
            ref={scrollRegionRef}
            onScroll={handleTimelineScroll}
          >
            {turns.length > 0 ? (
              <ConversationTimeline
                turns={turns}
                loading={loading}
                onConfirmation={handleConfirmation}
              />
            ) : (
              <DeliaReception />
            )}
            {loading ? (
              <DeliaLoadingBadge
                className="delia-interaction__loading"
                tone="info"
                label="A DÉLIA está processando sua solicitação…"
              />
            ) : null}
            <div ref={turnsEndRef} aria-hidden="true" />
          </div>

          {error ? (
            <p className="delia-interaction__error" role="alert">
              {error}
            </p>
          ) : null}

          <DeliaComposer
            inputId="delia-interaction-input"
            value={input}
            onChange={setInput}
            onSubmit={handleSubmit}
            loading={loading}
          />
        </section>

        <p className="delia-host-meta">
          {routeLabel ? `${routeLabel} · ` : null}
          Contexto de host: <span>{hostPath}</span>
        </p>
      </main>
    </div>
  );
}
