/**
 * Superfície confiável de consentimento da CLARA (Doc 106 §3.1).
 *
 * O consentimento de um lote/proposta NÃO é dado no chat: esta página
 * re-emite a sessão Keycloak (token fresco) e grava o consent_record
 * via BFF — credencial que o canal do assistente não consegue
 * produzir. Deep link: `closing/clara-consent?batch=<id>` ou
 * `?proposal=<id>`.
 */
import { useCallback, useEffect, useMemo, useState } from "react";

import { ActionButton } from "@delpi/plugin-ui/index";

import { ApiError } from "../../api/httpClient";
import {
  getClaraBatchConsentView,
  getClaraProposalConsentView,
  recordClaraBatchConsent,
  recordClaraProposalConsent,
  type ClaraBatchConsentView,
  type ClaraProposalConsentView,
} from "../../api/claraConsentApi";
import { CfFeedbackMessage } from "../../app/cfFeedbackUi";
import {
  CfEmptyState,
  CfPageHero,
  CfSectionCard,
  CfStatusBadge,
  CfTitleWithHelp,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import { CF_HELP } from "../../content/helpTooltips";
import { formatDateTime } from "../../utils/formatters";

type ConsentTarget =
  | { kind: "batch"; id: string }
  | { kind: "proposal"; id: string }
  | null;

type PanelError = { status: number; code: string | null; message: string };

function parseConsentTarget(): ConsentTarget {
  const params = new URLSearchParams(window.location.search);
  const batch = params.get("batch");
  const proposal = params.get("proposal");
  if (batch) return { kind: "batch", id: batch };
  if (proposal) return { kind: "proposal", id: proposal };
  return null;
}

const STATE_LABELS: Record<string, string> = {
  PREPARED: "Aguardando consentimento",
  CONFIRMED: "Consentimento registrado",
  EXECUTING: "Em execução",
  COMPLETED: "Concluído",
  COMPLETED_WITH_FAILURES: "Concluído com falhas",
  BLOCKED: "Bloqueado",
  EXPIRED: "Expirado",
  VERIFIED: "Verificado",
  CLAIMED: "Em execução",
  APPLIED: "Aplicado",
  FAILED: "Falhou",
  UNKNOWN: "Resultado desconhecido",
};

const ERROR_MESSAGES: Record<string, string> = {
  consent_required: "Este lote/proposta já não aceita consentimento.",
  step_up_token_stale:
    "Sessão anterior à solicitação — recarregue a página e confirme novamente.",
  step_up_unavailable:
    "Não foi possível renovar a sessão para confirmar — recarregue a página.",
  batch_actor_mismatch:
    "Este consentimento pertence a outro usuário.",
  proposal_actor_mismatch:
    "Este consentimento pertence a outro usuário.",
  batch_not_found: "Lote não encontrado.",
  proposal_not_found: "Proposta não encontrada.",
  batch_terminal: "Lote já encerrado — reprepare pela conversa com a CLARA.",
  batch_expired: "Lote expirado — reprepare pela conversa com a CLARA.",
  proposal_stale:
    "Proposta já reivindicada ou consumida — reprepare pela conversa.",
  forbidden: "Você não tem autorização para esta ação.",
  unauthorized: "Sessão expirada — autentique-se novamente.",
};

export function ClaraConsentPage() {
  const target = useMemo(parseConsentTarget, []);
  const [batch, setBatch] = useState<ClaraBatchConsentView | null>(null);
  const [proposal, setProposal] =
    useState<ClaraProposalConsentView | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<PanelError | null>(null);
  const [done, setDone] = useState<string | null>(null);

  const load = useCallback(async (signal?: AbortSignal) => {
    const t = parseConsentTarget();
    if (!t) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      if (t.kind === "batch") {
        setBatch(await getClaraBatchConsentView(t.id, signal));
      } else {
        setProposal(await getClaraProposalConsentView(t.id, signal));
      }
    } catch (err) {
      const apiErr = err as ApiError;
      setError({
        status: apiErr?.status ?? 0,
        code: apiErr?.code ?? null,
        message:
          ERROR_MESSAGES[apiErr?.code ?? ""] ??
          apiErr?.message ??
          "Falha ao carregar o consentimento.",
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal);
    return () => controller.abort();
  }, [load]);

  const confirm = useCallback(async () => {
    if (!target || busy) return;
    setBusy(true);
    setError(null);
    try {
      if (target.kind === "batch") {
        const result = await recordClaraBatchConsent(target.id);
        setDone(
          `Consentimento do lote registrado (${result.consent_mode}) — ` +
            "volte à conversa com a CLARA e peça a execução.",
        );
        setBatch(await getClaraBatchConsentView(target.id));
      } else {
        await recordClaraProposalConsent(target.id);
        setDone(
          "Consentimento da operação registrado — volte à conversa " +
            "com a CLARA e peça a execução.",
        );
        setProposal(await getClaraProposalConsentView(target.id));
      }
    } catch (err) {
      const apiErr = err as ApiError;
      setError({
        status: apiErr?.status ?? 0,
        code: apiErr?.code ?? null,
        message:
          ERROR_MESSAGES[apiErr?.code ?? ""] ??
          apiErr?.message ??
          "Falha ao registrar o consentimento.",
      });
    } finally {
      setBusy(false);
    }
  }, [target, busy]);

  const expiresLabel = (iso: string | undefined) =>
    iso ? formatDateTime(iso) : "—";

  const canConfirm =
    (batch && batch.status === "PREPARED") ||
    (proposal && !proposal.consented_at &&
      proposal.execution_state === "PREPARED");

  return (
    <section
      className="cf-page-stack cf-closing-layout"
      aria-label="Consentimento CLARA"
    >
      <CfPageHero
        eyebrow="Central de Fechamento"
        title={
          <CfTitleWithHelp
            title="Consentimento de ações da CLARA"
            hint={CF_HELP.claraConsent.page}
          />
        }
        description="Confirmação verificável do que você pediu à CLARA — registrada aqui, nunca pelo texto do chat."
      />

      <div className="cf-page-stack" aria-busy={loading}>
        {error ? (
          <CfFeedbackMessage intent="error" title="Consentimento indisponível">
            {error.message}
          </CfFeedbackMessage>
        ) : null}
        {done ? (
          <CfFeedbackMessage intent="success" title="Consentimento registrado">
            {done}
          </CfFeedbackMessage>
        ) : null}

        {!target && !loading ? (
          <CfEmptyState
            classNames={cfEmptyStateClassNames}
            defaultMessage="Nenhum lote ou proposta informado — use o link de consentimento enviado pela CLARA."
          />
        ) : null}

        {loading ? (
          <p aria-live="polite">Carregando consentimento…</p>
        ) : null}

        {batch ? (
          <CfSectionCard
            title={`Lote ${batch.batch_id.slice(0, 8)}…`}
            hint={CF_HELP.claraConsent.batch}
          >
            <p>
              <strong>Estado:</strong>{" "}
              <CfStatusBadge
                label={STATE_LABELS[batch.status] ?? batch.status}
                variant={batch.status === "CONFIRMED" ? "success" : "neutral"}
              />
            </p>
            <p>
              <strong>Plano selado:</strong>{" "}
              <code>{batch.plan_hash.slice(0, 16)}…</code>
            </p>
            <p>
              <strong>Expira em:</strong> {expiresLabel(batch.expires_at)}
            </p>
            <table className="cf-pend-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Operação</th>
                  <th>Recurso</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                {batch.operations.map((op) => (
                  <tr key={op.seq}>
                    <td>{op.seq + 1}</td>
                    <td>{op.capability}</td>
                    <td>
                      {op.resource_type} {op.resource_key}
                    </td>
                    <td>{STATE_LABELS[op.state] ?? op.state}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {canConfirm ? (
              <ActionButton
                type="button"
                onClick={() => void confirm()}
                disabled={busy}
              >
                {busy
                  ? "Registrando…"
                  : `Consentir as ${batch.operations.length} operações`}
              </ActionButton>
            ) : null}
          </CfSectionCard>
        ) : null}

        {proposal ? (
          <CfSectionCard
            title={`Operação ${proposal.capability}`}
            hint={CF_HELP.claraConsent.proposal}
          >
            <p>
              <strong>Recurso:</strong> {proposal.resource_type}{" "}
              {proposal.resource_key}
            </p>
            <p>
              <strong>Estado:</strong>{" "}
              {STATE_LABELS[proposal.execution_state] ??
                proposal.execution_state}
            </p>
            <p>
              <strong>Expira em:</strong>{" "}
              {expiresLabel(proposal.expires_at)}
            </p>
            <p>
              <strong>Parâmetros:</strong>{" "}
              <code>{JSON.stringify(proposal.params)}</code>
            </p>
            {canConfirm ? (
              <ActionButton
                type="button"
                onClick={() => void confirm()}
                disabled={busy}
              >
                {busy ? "Registrando…" : "Consentir esta operação"}
              </ActionButton>
            ) : proposal.consented_at ? (
              <p>Consentimento já registrado — volte à conversa.</p>
            ) : null}
          </CfSectionCard>
        ) : null}
      </div>
    </section>
  );
}
