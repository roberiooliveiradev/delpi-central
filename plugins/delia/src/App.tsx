import { useEffect, useRef, useState } from "react";

import {
  DELIA_ROOT_CLASS,
  DeliaPageHeader,
  DeliaStatusBadge,
} from "./ui/deliaUi";
import {
  DeliaInteractionError,
  buildInteractionContext,
  submitInteractionTurn,
} from "./api/interactionClient";
import type {
  DeliaConfirmationRequest,
  DeliaInteractionProvenance,
  DeliaWorkspaceContext,
} from "./api/interactionClient";
import {
  dedupeOwnerHintContent,
  presentationOwnerHint,
} from "./api/presentation";
import type {
  DeliaMessageKind,
  DeliaPresentation,
} from "./api/presentation";
import type { StatusBadgeVariant } from "@delpi/plugin-ui/index";

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

/** Transient UI display state only — not session persistence or memory. */
type DisplayTurn = {
  id: string;
  role: "user" | "delia";
  content: string;
  epistemicClass?: string | null;
  limitations?: string[];
  groundingStatus?: "GROUNDED" | "NON_GROUNDED" | null;
  provenance?: DeliaInteractionProvenance | null;
  /** Bounded pending-write confirmation surface (digests only). */
  confirmationRequest?: DeliaConfirmationRequest | null;
  /** The structured decision was already submitted for this request. */
  confirmationAnswered?: boolean;
  /** presentation.v1 projection — semantic state surface only. */
  presentation?: DeliaPresentation | null;
};

/** Semantic state badge per canonical message_kind (RESULT renders
 *  neutral — no badge). Presentation only; never derives state from
 *  prose and never widens authority. */
const MESSAGE_KIND_BADGE: Record<
  Exclude<DeliaMessageKind, "RESULT">,
  { label: string; variant: StatusBadgeVariant }
> = {
  CLARIFICATION_REQUIRED: {
    label: "Esclarecimento necessário",
    variant: "info",
  },
  CONFIRMATION_REQUIRED: {
    label: "Confirmação pendente",
    variant: "warning",
  },
  WRITE_REJECTED: { label: "Operação recusada", variant: "danger" },
  AUTHZ_DENIED: { label: "Acesso não autorizado", variant: "danger" },
  SOURCE_UNAVAILABLE: { label: "Fonte indisponível", variant: "warning" },
  PRECONDITION_REQUIRED: {
    label: "Pré-condição pendente",
    variant: "warning",
  },
};

const TOKEN_UNAVAILABLE_MESSAGE =
  "Token de acesso indisponível. Recarregue pelo Portal.";

/**
 * C3-INTERACTION-RUNTIME-01 + C3-INTERACTION-CONTINUITY-01.
 *
 * Bounded transient multi-turn interaction: rendered turns are kept in
 * React memory only and resent as untrusted prior context on each new
 * turn. No browser storage and no backend persistence — a reload
 * resets the conversation. permissions / isSuperadmin remain host
 * presentation hints and are never sent as backend authority.
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
  const [turns, setTurns] = useState<DisplayTurn[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const turnsEndRef = useRef<HTMLLIElement | null>(null);

  useEffect(() => {
    const end = turnsEndRef.current;
    if (end && typeof end.scrollIntoView === "function") {
      end.scrollIntoView({ block: "end" });
    }
  }, [turns.length, loading]);

  useEffect(
    () => () => {
      abortRef.current?.abort();
    },
    [],
  );

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
      setError(
        submitError instanceof DeliaInteractionError
          ? submitError.message
          : "Erro inesperado ao falar com a DÉLIA.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit() {
    const value = input.trim();
    if (!value || loading) return;
    await sendTurn(value);
  }

  /**
   * Governed-write confirmation (ledger §6.126): the MFE echoes the
   * bounded digests back verbatim — it never sees the raw owner
   * handle and never makes any authorization decision.
   */
  async function handleConfirmation(
    request: DeliaConfirmationRequest,
    decision: "CONFIRM" | "REJECT",
  ) {
    if (loading) return;
    const label =
      decision === "CONFIRM"
        ? "Confirmação da operação solicitada."
        : "Cancelamento da operação solicitada.";
    await sendTurn(label, {
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
          {turns.length > 0 ? (
            <ul className="delia-turns" aria-label="Respostas">
              {turns.map((turn, index) => {
                const ownerHint =
                  turn.role === "delia"
                    ? presentationOwnerHint(turn.presentation ?? null)
                    : null;
                const displayContent = dedupeOwnerHintContent(
                  turn.content,
                  ownerHint,
                );
                const stateBadge =
                  turn.presentation?.messageKind &&
                  turn.presentation.messageKind !== "RESULT"
                    ? MESSAGE_KIND_BADGE[
                        turn.presentation.messageKind as Exclude<
                          DeliaMessageKind,
                          "RESULT"
                        >
                      ]
                    : undefined;
                return (
                <li
                  key={turn.id}
                  ref={
                    index === turns.length - 1 ? turnsEndRef : undefined
                  }
                  className={`delia-turn delia-turn--${turn.role}`}
                >
                  <span className="delia-turn__label">
                    {turn.role === "user" ? "Você" : "DÉLIA"}
                  </span>
                  {stateBadge ? (
                    <DeliaStatusBadge
                      label={stateBadge.label}
                      variant={stateBadge.variant}
                      className="delia-turn__state"
                    />
                  ) : null}
                  <p className="delia-turn__content">{displayContent}</p>
                  {ownerHint ? (
                    <p className="delia-turn__notice">
                      A fonte informou: {ownerHint}
                    </p>
                  ) : null}
                  {turn.epistemicClass ? (
                    <span className="delia-turn__meta">
                      classificação: {turn.epistemicClass}
                    </span>
                  ) : null}
                  {turn.groundingStatus === "GROUNDED" &&
                  turn.provenance?.source ? (
                    <span className="delia-turn__meta">
                      fonte: Cadastro de Produtos DELPI ·{" "}
                      {turn.provenance.specialist_id ?? "especialista"}/
                      {turn.provenance.protocol ?? "MCP"} ·{" "}
                      {turn.provenance.observed_at ?? ""}
                    </span>
                  ) : null}
                  {turn.limitations && turn.limitations.length > 0 ? (
                    <span className="delia-turn__meta">
                      limitações: {turn.limitations.join(", ")}
                    </span>
                  ) : null}
                  {turn.confirmationRequest &&
                  !turn.confirmationAnswered ? (
                    <div
                      className="delia-confirmation"
                      role="group"
                      aria-label="Confirmação pendente"
                    >
                      <button
                        type="button"
                        className="delia-confirmation__confirm"
                        disabled={loading}
                        onClick={() =>
                          void handleConfirmation(
                            turn.confirmationRequest as DeliaConfirmationRequest,
                            "CONFIRM",
                          )
                        }
                      >
                        Confirmar
                      </button>
                      <button
                        type="button"
                        className="delia-confirmation__cancel"
                        disabled={loading}
                        onClick={() =>
                          void handleConfirmation(
                            turn.confirmationRequest as DeliaConfirmationRequest,
                            "REJECT",
                          )
                        }
                      >
                        Cancelar
                      </button>
                    </div>
                  ) : null}
                </li>
                );
              })}
            </ul>
          ) : null}

          {error ? (
            <p className="delia-interaction__error" role="alert">
              {error}
            </p>
          ) : null}

          <form
            className="delia-interaction__form"
            onSubmit={(event) => {
              event.preventDefault();
              void handleSubmit();
            }}
          >
            <label htmlFor="delia-interaction-input">
              Pergunte à DÉLIA
            </label>
            <textarea
              id="delia-interaction-input"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Digite sua pergunta…"
              rows={3}
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
            >
              {loading ? "Enviando…" : "Enviar"}
            </button>
          </form>
        </section>

        <p className="delia-host-meta">
          {routeLabel ? `${routeLabel} · ` : null}
          Contexto de host: <span>{hostPath}</span>
        </p>
      </main>
    </div>
  );
}
