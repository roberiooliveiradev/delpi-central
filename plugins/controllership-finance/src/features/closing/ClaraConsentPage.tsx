/**
 * Superfície confiável de consentimento da CLARA (Doc 106 §3.1,
 * R-CLARA-01/02).
 *
 * O consentimento de um lote/proposta NÃO é dado no chat: esta página
 * apresenta o plano selado por inteiro (desafio emitido no PREPARE),
 * renova a sessão Keycloak e devolve o `challenge_id` à BFF — prova
 * de autorização vinculada ao plano exato, ao ator e à expiração.
 * Deep link: `closing/clara-consent?batch=<id>` ou `?proposal=<id>`.
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
  type ClaraBatchOperation,
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
  PREPARED: "Aguardando autorização",
  CONFIRMED: "Autorização registrada",
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
  PENDING: "Pendente",
  APPROVED: "Aprovado",
  CONSUMED: "Utilizado",
  REVOKED: "Revogado",
};

const ERROR_MESSAGES: Record<string, string> = {
  consent_required: "Este lote/proposta já não aceita consentimento.",
  consent_challenge_required:
    "Autorização incompleta — recarregue a página e confirme pelo botão de autorização.",
  consent_challenge_not_found:
    "Autorização não encontrada — reprepare a solicitação com a CLARA.",
  consent_challenge_mismatch:
    "Esta autorização pertence a outro plano ou outro usuário — reprepare a solicitação.",
  consent_challenge_consumed:
    "Esta autorização já foi utilizada ou expirou — reprepare a solicitação com a CLARA.",
  consent_challenge_expired:
    "A autorização expirou — reprepare a solicitação com a CLARA.",
  consent_not_displayable:
    "Há operação sem descrição clara — a autorização foi bloqueada para sua proteção.",
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

const CONSENT_BLOCK_MESSAGES: Record<string, string> = {
  expired:
    "Este plano expirou — peça à CLARA para prepará-lo novamente.",
  not_prepared: "Este plano já não está aguardando autorização.",
  no_executable_operations:
    "Nenhuma operação executável neste plano — revise as bloqueadas.",
  operation_not_displayable:
    "Há operação sem descrição clara — a autorização foi bloqueada para sua proteção.",
  batch_owned:
    "Esta operação pertence a um lote — autorize o lote completo.",
};

function OperationCard({
  op,
  position,
}: {
  op: ClaraBatchOperation;
  position: number;
}) {
  const blocked = op.viability === "blocked";
  const deps = op.depends_on ?? [];
  return (
    <li
      className="cf-list-row"
      aria-label={`Operação ${position}`}
    >
      <div className="cf-page-stack" style={{ gap: "0.35rem" }}>
        <p>
          <strong>{position}.</strong>{" "}
          <CfStatusBadge
            label={blocked ? "Bloqueada" : "Executável"}
            variant={blocked ? "warning" : "success"}
          />{" "}
          {op.presentation?.summary ?? op.capability}
        </p>
        {op.presentation?.effect ? (
          <p>
            <strong>Efeito:</strong> {op.presentation.effect}.
          </p>
        ) : null}
        {op.presentation?.motivation ? (
          <p>
            <strong>Motivo:</strong> {op.presentation.motivation}
          </p>
        ) : null}
        {blocked && op.block_message ? (
          <p>
            <strong>Impedimento:</strong> {op.block_message}
            {op.missing_params?.length
              ? ` (${op.missing_params.join(", ")})`
              : ""}
          </p>
        ) : null}
        {deps.length ? (
          <p>
            <strong>Depende de:</strong>{" "}
            {deps.map((d) => `operação ${d + 1}`).join(", ")}
          </p>
        ) : null}
      </div>
    </li>
  );
}

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
    const challengeId =
      target.kind === "batch"
        ? batch?.challenge?.challenge_id
        : proposal?.challenge?.challenge_id;
    if (!challengeId) {
      setError({
        status: 0,
        code: "consent_challenge_required",
        message: ERROR_MESSAGES.consent_challenge_required,
      });
      return;
    }
    setBusy(true);
    setError(null);
    try {
      if (target.kind === "batch") {
        const result = await recordClaraBatchConsent(
          target.id,
          challengeId,
        );
        setDone(
          `Autorização do lote registrada (${result.consent_mode}) — ` +
            "volte à conversa com a CLARA e peça a execução.",
        );
        setBatch(await getClaraBatchConsentView(target.id));
      } else {
        await recordClaraProposalConsent(target.id, challengeId);
        setDone(
          "Autorização da operação registrada — volte à conversa " +
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
  }, [target, busy, batch, proposal]);

  const expiresLabel = (iso: string | undefined) =>
    iso ? formatDateTime(iso) : "—";

  const canConfirm =
    (batch && batch.status === "PREPARED" && batch.consentable) ||
    (proposal && proposal.consentable && !proposal.consented_at);

  const consentBlockMessage = batch?.consent_block_reason
    ? CONSENT_BLOCK_MESSAGES[batch.consent_block_reason] ??
      batch.consent_block_reason
    : proposal?.consent_block_reason
      ? CONSENT_BLOCK_MESSAGES[proposal.consent_block_reason] ??
        proposal.consent_block_reason
      : null;

  return (
    <section
      className="cf-page-stack cf-closing-layout"
      aria-label="Consentimento CLARA"
    >
      <CfPageHero
        eyebrow="Central de Fechamento"
        title={
          <CfTitleWithHelp
            title="Autorização de ações da CLARA"
            hint={CF_HELP.claraConsent.page}
          />
        }
        description="Revisão e autorização verificável do que você pediu à CLARA — registrada aqui, nunca pelo texto do chat."
      />

      <div className="cf-page-stack" aria-busy={loading}>
        {error ? (
          <CfFeedbackMessage intent="error" title="Consentimento indisponível">
            {error.message}
          </CfFeedbackMessage>
        ) : null}
        {done ? (
          <CfFeedbackMessage intent="success" title="Autorização registrada">
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
            title={`Plano da CLARA — lote ${batch.batch_id.slice(0, 8)}…`}
            hint={CF_HELP.claraConsent.batch}
          >
            <p>
              <strong>Competência:</strong>{" "}
              {batch.competence?.period_label ?? "—"}
            </p>
            <p>
              <strong>Estado:</strong>{" "}
              <CfStatusBadge
                label={STATE_LABELS[batch.status] ?? batch.status}
                variant={batch.status === "CONFIRMED" ? "success" : "neutral"}
              />
            </p>
            <p>
              <strong>Operações:</strong> {batch.totals.total} no total —{" "}
              {batch.totals.executable} executáveis,{" "}
              {batch.totals.blocked} bloqueadas
              {batch.totals.dependent
                ? `, ${batch.totals.dependent} com dependências`
                : ""}
              .
            </p>
            <p>
              <strong>Expira em:</strong> {expiresLabel(batch.expires_at)}
            </p>
            <p>
              <strong>Plano selado:</strong>{" "}
              <code>{batch.plan_hash.slice(0, 16)}…</code>
            </p>
            <ol
              className="cf-page-stack"
              aria-label="Operações do lote"
            >
              {batch.operations.map((op) => (
                <OperationCard key={op.index} op={op} position={op.index + 1} />
              ))}
            </ol>
            {consentBlockMessage && !done ? (
              <CfFeedbackMessage
                intent="warning"
                title="Autorização indisponível"
              >
                {consentBlockMessage}
              </CfFeedbackMessage>
            ) : null}
            {canConfirm ? (
              <ActionButton
                type="button"
                onClick={() => void confirm()}
                disabled={busy}
              >
                {busy
                  ? "Registrando…"
                  : `Autorizar as ${batch.totals.executable} operações executáveis`}
              </ActionButton>
            ) : null}
          </CfSectionCard>
        ) : null}

        {proposal ? (
          <CfSectionCard
            title="Operação solicitada"
            hint={CF_HELP.claraConsent.proposal}
          >
            <p>
              <strong>Competência:</strong>{" "}
              {proposal.period_label ?? "—"}
            </p>
            <p>{proposal.presentation?.summary ?? proposal.capability}</p>
            {proposal.presentation?.effect ? (
              <p>
                <strong>Efeito:</strong> {proposal.presentation.effect}.
              </p>
            ) : null}
            {proposal.presentation?.motivation ? (
              <p>
                <strong>Motivo:</strong> {proposal.presentation.motivation}
              </p>
            ) : null}
            <p>
              <strong>Estado:</strong>{" "}
              {STATE_LABELS[proposal.execution_state] ??
                proposal.execution_state}
            </p>
            <p>
              <strong>Expira em:</strong>{" "}
              {expiresLabel(proposal.expires_at)}
            </p>
            {consentBlockMessage && !done ? (
              <CfFeedbackMessage
                intent="warning"
                title="Autorização indisponível"
              >
                {consentBlockMessage}
              </CfFeedbackMessage>
            ) : null}
            {canConfirm ? (
              <ActionButton
                type="button"
                onClick={() => void confirm()}
                disabled={busy}
              >
                {busy ? "Registrando…" : "Autorizar esta operação"}
              </ActionButton>
            ) : proposal.consented_at ? (
              <p>Autorização já registrada — volte à conversa.</p>
            ) : null}
          </CfSectionCard>
        ) : null}
      </div>
    </section>
  );
}
