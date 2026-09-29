/**
 * Shared governed-action shell for Diagnostic material actions.
 *
 *   form → PREPARE → exact_change review → explicit confirmation
 *        → COMMIT → canonical GET read-back → verified outcome
 *
 * No direct writes, no client-side technical ids, no optimistic success.
 * The payload is built only from the closed allowlist action + its
 * canonical fields; the backend remains the final authority.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  FieldLabel,
  NativeSelectControl,
} from "@delpi/plugin-ui/index";

import { StateBox } from "../../../components/StateBox";
import {
  commitGovernedProposal,
  fetchDiagnostic,
  isDiagnosticManageAction,
  prepareManageDiagnostic,
  type DiagnosticManageAction,
  type DiagnosticProposal,
  type DiagnosticReadContext,
  type DiagnosticEvidenceRelation,
  type DiagnosticEpistemicState,
} from "../../../data/api/transformometroDiagnosticApi";
import type { RevisaoEvidence } from "../../../types/revisaoEvidence";
import {
  CAUSAL_RELATION_LABEL,
  DIAGNOSTIC_ACTION_LABELS,
  EPISTEMIC_LABELS,
  EVIDENCE_RELATION_LABELS,
  EXACT_CHANGE_FIELD_LABELS,
} from "./diagnosticDisplay";
import { verifyDiagnosticOutcome } from "./diagnosticVerification";

const STALE_PROPOSAL_MESSAGE =
  "Este diagnóstico foi alterado desde a preparação da mudança. " +
  "Recarregue e revise antes de confirmar novamente.";

const OUTCOME_FAILED_MESSAGE =
  "A mudança foi enviada, mas a leitura canônica não confirmou o resultado " +
  "esperado (OUTCOME_VERIFICATION_FAILED). Recarregue e revise o estado atual.";

const EVIDENCE_RELATION_OPTIONS = [
  { value: "SUPPORTS", label: EVIDENCE_RELATION_LABELS.SUPPORTS },
  { value: "CONTRADICTS", label: EVIDENCE_RELATION_LABELS.CONTRADICTS },
  { value: "CONTEXTUALIZES", label: EVIDENCE_RELATION_LABELS.CONTEXTUALIZES },
] satisfies Array<{ value: DiagnosticEvidenceRelation; label: string }>;

const EPISTEMIC_OPTIONS = [
  { value: "OBSERVED", label: EPISTEMIC_LABELS.OBSERVED },
  { value: "CALCULATED", label: EPISTEMIC_LABELS.CALCULATED },
  { value: "UNKNOWN", label: EPISTEMIC_LABELS.UNKNOWN },
] satisfies Array<{ value: DiagnosticEpistemicState; label: string }>;

type ActionDraft = {
  statement: string;
  epistemic_state: string;
  role: string;
  source_hypothesis_id: string;
  target_id: string;
  evidence_id: string;
  relation: string;
  note: string;
  rationale: string;
  hypothesis_ids: string[];
  finding_ids: string[];
  root_cause_hypothesis_id: string;
};

const EMPTY_DRAFT: ActionDraft = {
  statement: "",
  epistemic_state: "OBSERVED",
  role: "",
  source_hypothesis_id: "",
  target_id: "",
  evidence_id: "",
  relation: "SUPPORTS",
  note: "",
  rationale: "",
  hypothesis_ids: [],
  finding_ids: [],
  root_cause_hypothesis_id: "",
};

type Stage = "form" | "review" | "stale";

type Props = {
  diagnosticId: string;
  action: DiagnosticManageAction;
  /** Target id for claim actions (hypothesis_id / conclusion_id). */
  targetId?: string | null;
  /** Human-readable target context for the heading. */
  targetLabel?: string | null;
  detail: DiagnosticReadContext;
  /** Revision Evidence options — loaded lazily for the evidence picker. */
  evidences: RevisaoEvidence[] | null;
  evidencesLoading?: boolean;
  /** Set when a remote update arrived — blocks commit until reprepare. */
  remoteStale: boolean;
  getAccessToken?: () => string | undefined;
  onCancel: () => void;
  /** Called after verified outcome — parent refetches canonically. */
  onApplied: () => void;
};

function buildManagePayload(
  action: DiagnosticManageAction,
  draft: ActionDraft,
  targetId?: string | null,
): Record<string, unknown> {
  switch (action) {
    case "add_finding": {
      const payload: Record<string, unknown> = {
        statement: draft.statement.trim(),
      };
      if (draft.role) payload.role = draft.role;
      if (draft.epistemic_state) payload.epistemic_state = draft.epistemic_state;
      return payload;
    }
    case "add_hypothesis":
      return { statement: draft.statement.trim() };
    case "add_causal_link":
      return {
        source_hypothesis_id: draft.source_hypothesis_id,
        target_id: draft.target_id,
      };
    case "add_evidence_link": {
      const payload: Record<string, unknown> = {
        evidence_id: draft.evidence_id,
        relation: draft.relation,
      };
      if (draft.target_id) payload.target_id = draft.target_id;
      return payload;
    }
    case "add_conclusion": {
      const payload: Record<string, unknown> = {
        statement: draft.statement.trim(),
        hypothesis_ids: draft.hypothesis_ids,
        finding_ids: draft.finding_ids,
      };
      if (draft.rationale.trim()) payload.rationale = draft.rationale.trim();
      if (draft.root_cause_hypothesis_id) {
        payload.root_cause_hypothesis_id = draft.root_cause_hypothesis_id;
      }
      return payload;
    }
    case "validate_hypothesis":
    case "reject_hypothesis":
    case "supersede_hypothesis":
    case "mark_hypothesis_stale_evidence":
    case "mark_hypothesis_revalidation_required": {
      const payload: Record<string, unknown> = { hypothesis_id: targetId };
      if (draft.note.trim()) payload.note = draft.note.trim();
      return payload;
    }
    case "validate_conclusion":
    case "reject_conclusion":
    case "supersede_conclusion": {
      const payload: Record<string, unknown> = { conclusion_id: targetId };
      if (draft.note.trim()) payload.note = draft.note.trim();
      return payload;
    }
  }
}

function draftValid(action: DiagnosticManageAction, draft: ActionDraft, targetId?: string | null): boolean {
  switch (action) {
    case "add_finding":
    case "add_hypothesis":
    case "add_conclusion":
      return draft.statement.trim().length > 0;
    case "add_causal_link":
      return Boolean(draft.source_hypothesis_id && draft.target_id);
    case "add_evidence_link":
      return Boolean(draft.evidence_id && draft.relation);
    default:
      return Boolean(targetId);
  }
}

function exactChangeEntries(proposal: DiagnosticProposal): Array<[string, unknown]> {
  const change = proposal.exact_change ?? {};
  const payload = (change.payload ?? {}) as Record<string, unknown>;
  const entries: Array<[string, unknown]> = [];
  for (const [key, value] of Object.entries(payload)) {
    if (value === null || value === undefined || value === "") continue;
    entries.push([key, value]);
  }
  if (change.action === "create" && typeof change.problem_statement === "string") {
    entries.unshift(["problem_statement", change.problem_statement]);
  }
  return entries;
}

function renderChangeValue(key: string, value: unknown): string {
  if (key === "epistemic_state" && typeof value === "string") {
    return EPISTEMIC_LABELS[value as DiagnosticEpistemicState] ?? value;
  }
  if (key === "relation" && typeof value === "string") {
    return EVIDENCE_RELATION_LABELS[value as DiagnosticEvidenceRelation] ?? value;
  }
  if (key === "role" && typeof value === "string") {
    return value === "SYMPTOM" ? "Sintoma" : value;
  }
  if (Array.isArray(value)) return value.map((v) => String(v)).join(", ");
  if (value && typeof value === "object") return JSON.stringify(value);
  return String(value);
}

export function DiagnosticActionPanel({
  diagnosticId,
  action,
  targetId = null,
  targetLabel = null,
  detail,
  evidences,
  evidencesLoading = false,
  remoteStale,
  getAccessToken,
  onCancel,
  onApplied,
}: Props) {
  const [draft, setDraft] = useState<ActionDraft>(EMPTY_DRAFT);
  const [stage, setStage] = useState<Stage>("form");
  const [proposal, setProposal] = useState<DiagnosticProposal | null>(null);
  const [busy, setBusy] = useState<"prepare" | "commit" | "verify" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [staleNotice, setStaleNotice] = useState<string | null>(null);
  const reviewHeadingRef = useRef<HTMLHeadingElement>(null);
  const errorRef = useRef<HTMLDivElement>(null);

  // A remote update invalidates any pending proposal — reprepare required.
  useEffect(() => {
    if (remoteStale && proposal) {
      setStage("stale");
      setStaleNotice(STALE_PROPOSAL_MESSAGE);
    }
  }, [remoteStale, proposal]);

  const set = useCallback(<K extends keyof ActionDraft>(key: K, value: ActionDraft[K]) => {
    setDraft((prev) => ({ ...prev, [key]: value }));
  }, []);

  const targetOptions = useMemo(() => {
    const diagnostic = detail.diagnostic;
    return [
      { value: "", label: "Nenhum destino específico" },
      ...diagnostic.findings.map((f) => ({
        value: f.finding_id,
        label: `Achado — ${f.statement.slice(0, 60)}`,
      })),
      ...diagnostic.hypotheses.map((h) => ({
        value: h.hypothesis_id,
        label: `Hipótese — ${h.statement.slice(0, 60)}`,
      })),
      ...diagnostic.conclusions.map((c) => ({
        value: c.conclusion_id,
        label: `Conclusão — ${c.statement.slice(0, 60)}`,
      })),
    ];
  }, [detail]);

  const causalTargetOptions = useMemo(() => {
    const diagnostic = detail.diagnostic;
    return [
      { value: "", label: "Selecione o destino" },
      ...diagnostic.hypotheses.map((h) => ({
        value: h.hypothesis_id,
        label: `Hipótese — ${h.statement.slice(0, 60)}`,
      })),
      ...diagnostic.findings.map((f) => ({
        value: f.finding_id,
        label: `Achado — ${f.statement.slice(0, 60)}`,
      })),
    ];
  }, [detail]);

  const hypothesisOptions = useMemo(
    () =>
      detail.diagnostic.hypotheses.map((h) => ({
        value: h.hypothesis_id,
        label: h.statement.slice(0, 80),
      })),
    [detail],
  );

  const evidenceOptions = useMemo(
    () =>
      (evidences ?? []).map((ev) => ({
        value: ev.evidencia_id,
        label: ev.descricao || ev.nome_arquivo || ev.evidencia_id,
      })),
    [evidences],
  );

  const handlePrepare = useCallback(async () => {
    if (!isDiagnosticManageAction(action)) return;
    setBusy("prepare");
    setError(null);
    try {
      const payload = buildManagePayload(action, draft, targetId);
      const prepared = await prepareManageDiagnostic(
        diagnosticId,
        action,
        payload,
        getAccessToken,
      );
      setProposal(prepared);
      setStage("review");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao preparar a mudança.");
    } finally {
      setBusy(null);
    }
  }, [action, diagnosticId, draft, getAccessToken, targetId]);

  const handleConfirm = useCallback(async () => {
    if (!proposal) return;
    setBusy("commit");
    setError(null);
    try {
      await commitGovernedProposal(proposal.proposal_handle, getAccessToken);
    } catch (err) {
      setBusy(null);
      const status = (err as { status?: number })?.status;
      const code = (err as { code?: string })?.code;
      if (status === 409 || code === "PROPOSAL_STALE" || code === "proposal_stale") {
        setStage("stale");
        setStaleNotice(STALE_PROPOSAL_MESSAGE);
        return;
      }
      setError(err instanceof Error ? err.message : "Falha ao confirmar a mudança.");
      return;
    }
    // COMMIT 2xx ≠ success — verify via canonical read-back.
    setBusy("verify");
    try {
      const ctx = await fetchDiagnostic(diagnosticId, getAccessToken);
      const outcome = verifyDiagnosticOutcome(proposal, ctx.diagnostic);
      if (!outcome.ok) {
        setError(OUTCOME_FAILED_MESSAGE);
        setStage("form");
        setProposal(null);
        return;
      }
      onApplied();
    } catch {
      setError(OUTCOME_FAILED_MESSAGE);
      setStage("form");
      setProposal(null);
    } finally {
      setBusy(null);
    }
  }, [diagnosticId, getAccessToken, onApplied, proposal]);

  useEffect(() => {
    if (stage === "review" && reviewHeadingRef.current) {
      reviewHeadingRef.current.focus();
    }
  }, [stage]);

  useEffect(() => {
    if (error && errorRef.current) errorRef.current.focus();
  }, [error]);

  const actionLabel = DIAGNOSTIC_ACTION_LABELS[action];
  const isClaimAction =
    action.endsWith("_hypothesis") ||
    action.startsWith("mark_hypothesis") ||
    action.endsWith("_conclusion");
  const needsEvidencePicker = action === "add_evidence_link";

  return (
    <div className="tm-diagnostic-action" data-diagnostic-action={action}>
      <h4 className="tm-diagnostic-action__title">
        {actionLabel}
        {targetLabel ? <span className="ds-hint"> — {targetLabel}</span> : null}
      </h4>

      {staleNotice ? (
        <StateBox variant="warning">
          {staleNotice}
        </StateBox>
      ) : null}

      {error ? (
        <div ref={errorRef} tabIndex={-1}>
          <StateBox variant="error">{error}</StateBox>
        </div>
      ) : null}

      {stage === "form" && !staleNotice ? (
        <div className="tm-diagnostic-action__form">
          {(action === "add_finding" ||
            action === "add_hypothesis" ||
            action === "add_conclusion") ? (
            <div className="ds-field">
              <FieldLabel label="Enunciado" htmlFor={`diag-${action}-statement`} />
              <textarea
                id={`diag-${action}-statement`}
                className="delpi-ui-native-control tm-diagnostic-textarea"
                value={draft.statement}
                onChange={(e) => set("statement", e.target.value)}
                rows={action === "add_conclusion" ? 3 : 2}
                aria-label="Enunciado"
              />
            </div>
          ) : null}

          {action === "add_finding" ? (
            <>
              <div className="ds-field">
                <FieldLabel label="Natureza epistêmica" htmlFor={`diag-${action}-epistemic`} />
                <NativeSelectControl
                  id={`diag-${action}-epistemic`}
                  value={draft.epistemic_state}
                  onChange={(v) => set("epistemic_state", v)}
                  options={EPISTEMIC_OPTIONS}
                />
              </div>
              <div className="ds-field">
                <FieldLabel label="Papel do achado" htmlFor={`diag-${action}-role`} />
                <NativeSelectControl
                  id={`diag-${action}-role`}
                  value={draft.role}
                  onChange={(v) => set("role", v)}
                  options={[{ value: "SYMPTOM", label: "Sintoma" }]}
                  placeholderOption="Nenhum"
                />
              </div>
            </>
          ) : null}

          {action === "add_causal_link" ? (
            <>
              <p className="ds-hint">
                A única relação causal disponível é “{CAUSAL_RELATION_LABEL}” — a
                hipótese de origem contribui para o destino, sem afirmar causa ou prova.
              </p>
              <div className="ds-field">
                <FieldLabel label="Hipótese de origem" htmlFor={`diag-${action}-source`} />
                <NativeSelectControl
                  id={`diag-${action}-source`}
                  value={draft.source_hypothesis_id}
                  onChange={(v) => set("source_hypothesis_id", v)}
                  options={hypothesisOptions}
                  placeholderOption="Selecione a hipótese"
                />
              </div>
              <div className="ds-field">
                <FieldLabel label={`${CAUSAL_RELATION_LABEL} (destino)`} htmlFor={`diag-${action}-target`} />
                <NativeSelectControl
                  id={`diag-${action}-target`}
                  value={draft.target_id}
                  onChange={(v) => set("target_id", v)}
                  options={causalTargetOptions}
                />
              </div>
            </>
          ) : null}

          {action === "add_evidence_link" ? (
            <>
              {evidencesLoading ? (
                <p className="ds-hint">Carregando evidências da revisão…</p>
              ) : null}
              {evidences && evidences.length === 0 ? (
                <StateBox variant="default">
                  Nenhuma evidência registrada nesta revisão. Registre a evidência na seção
                  Evidências antes de vinculá-la ao diagnóstico.
                </StateBox>
              ) : null}
              <div className="ds-field">
                <FieldLabel label="Evidência existente" htmlFor={`diag-${action}-evidence`} />
                <NativeSelectControl
                  id={`diag-${action}-evidence`}
                  value={draft.evidence_id}
                  onChange={(v) => set("evidence_id", v)}
                  options={evidenceOptions}
                  placeholderOption="Selecione a evidência"
                  disabled={!evidences || evidences.length === 0}
                />
              </div>
              <div className="ds-field">
                <FieldLabel label="Relação com o item" htmlFor={`diag-${action}-relation`} />
                <NativeSelectControl
                  id={`diag-${action}-relation`}
                  value={draft.relation}
                  onChange={(v) => set("relation", v)}
                  options={EVIDENCE_RELATION_OPTIONS}
                />
              </div>
              <div className="ds-field">
                <FieldLabel label="Item relacionado" htmlFor={`diag-${action}-target`} />
                <NativeSelectControl
                  id={`diag-${action}-target`}
                  value={draft.target_id}
                  onChange={(v) => set("target_id", v)}
                  options={targetOptions}
                />
              </div>
            </>
          ) : null}

          {action === "add_conclusion" ? (
            <>
              <div className="ds-field">
                <FieldLabel label="Justificativa" htmlFor={`diag-${action}-rationale`} />
                <textarea
                  id={`diag-${action}-rationale`}
                  className="delpi-ui-native-control tm-diagnostic-textarea"
                  value={draft.rationale}
                  onChange={(e) => set("rationale", e.target.value)}
                  rows={2}
                  aria-label="Justificativa"
                />
              </div>
              {hypothesisOptions.length ? (
                <fieldset className="ds-field">
                  <legend className="ds-field__label">Hipóteses referenciadas</legend>
                  {detail.diagnostic.hypotheses.map((h) => (
                    <label key={h.hypothesis_id} className="tm-diagnostic-check">
                      <input
                        type="checkbox"
                        checked={draft.hypothesis_ids.includes(h.hypothesis_id)}
                        onChange={(e) =>
                          set(
                            "hypothesis_ids",
                            e.target.checked
                              ? [...draft.hypothesis_ids, h.hypothesis_id]
                              : draft.hypothesis_ids.filter((id) => id !== h.hypothesis_id),
                          )
                        }
                      />
                      <span>{h.statement}</span>
                    </label>
                  ))}
                </fieldset>
              ) : null}
              {detail.diagnostic.findings.length ? (
                <fieldset className="ds-field">
                  <legend className="ds-field__label">Achados referenciados</legend>
                  {detail.diagnostic.findings.map((f) => (
                    <label key={f.finding_id} className="tm-diagnostic-check">
                      <input
                        type="checkbox"
                        checked={draft.finding_ids.includes(f.finding_id)}
                        onChange={(e) =>
                          set(
                            "finding_ids",
                            e.target.checked
                              ? [...draft.finding_ids, f.finding_id]
                              : draft.finding_ids.filter((id) => id !== f.finding_id),
                          )
                        }
                      />
                      <span>{f.statement}</span>
                    </label>
                  ))}
                </fieldset>
              ) : null}
              {draft.hypothesis_ids.length ? (
                <div className="ds-field">
                  <FieldLabel label="Hipótese causa-raiz" htmlFor={`diag-${action}-root`} />
                  <NativeSelectControl
                    id={`diag-${action}-root`}
                    value={draft.root_cause_hypothesis_id}
                    onChange={(v) => set("root_cause_hypothesis_id", v)}
                    options={detail.diagnostic.hypotheses
                      .filter((h) => draft.hypothesis_ids.includes(h.hypothesis_id))
                      .map((h) => ({ value: h.hypothesis_id, label: h.statement.slice(0, 80) }))}
                    placeholderOption="Nenhuma"
                  />
                </div>
              ) : null}
            </>
          ) : null}

          {isClaimAction ? (
            <div className="ds-field">
              <FieldLabel label="Nota (opcional)" htmlFor={`diag-${action}-note`} />
              <textarea
                id={`diag-${action}-note`}
                className="delpi-ui-native-control tm-diagnostic-textarea"
                value={draft.note}
                onChange={(e) => set("note", e.target.value)}
                rows={2}
                aria-label="Nota"
              />
            </div>
          ) : null}

          {needsEvidencePicker && !evidences ? (
            <p className="ds-hint">Carregue as evidências para vincular.</p>
          ) : null}

          <div className="tm-diagnostic-action__actions">
            <button
              type="button"
              className="ds-btn ds-btn--primary"
              disabled={busy != null || !draftValid(action, draft, targetId)}
              onClick={() => void handlePrepare()}
            >
              {busy === "prepare" ? "Preparando…" : "Preparar alteração"}
            </button>
            <button
              type="button"
              className="ds-btn ds-btn--ghost"
              disabled={busy != null}
              onClick={onCancel}
            >
              Cancelar
            </button>
          </div>
        </div>
      ) : null}

      {stage === "review" && proposal ? (
        <div className="tm-diagnostic-action__review">
          <h4 ref={reviewHeadingRef} tabIndex={-1} className="tm-diagnostic-action__review-title">
            Revise a alteração preparada
          </h4>
          <p className="ds-hint">
            Confirme a alteração preparada abaixo. Ela só é aplicada após a confirmação
            explícita e a verificação da leitura canônica.
          </p>
          <dl className="tm-diagnostic-action__change">
            <div>
              <dt>Ação</dt>
              <dd>{actionLabel}</dd>
            </div>
            {exactChangeEntries(proposal).map(([key, value]) => (
              <div key={key}>
                <dt>{EXACT_CHANGE_FIELD_LABELS[key] ?? key}</dt>
                <dd>{renderChangeValue(key, value)}</dd>
              </div>
            ))}
          </dl>
          {proposal.validation_result && proposal.validation_result.ready === false ? (
            <StateBox variant="warning">
              Esta proposta não está pronta para aplicação
              {proposal.validation_result.missing?.length
                ? `: ${proposal.validation_result.missing.join(", ")}`
                : "."}
            </StateBox>
          ) : null}
          <div className="tm-diagnostic-action__actions">
            <button
              type="button"
              className="ds-btn ds-btn--primary"
              disabled={busy != null || remoteStale || proposal.act_allowed === false}
              onClick={() => void handleConfirm()}
            >
              {busy === "commit"
                ? "Confirmando…"
                : busy === "verify"
                  ? "Verificando…"
                  : "Confirmar alteração"}
            </button>
            <button
              type="button"
              className="ds-btn ds-btn--ghost"
              disabled={busy != null}
              onClick={() => {
                setProposal(null);
                setStage("form");
              }}
            >
              Voltar e editar
            </button>
          </div>
        </div>
      ) : null}

      {stage === "stale" ? (
        <div className="tm-diagnostic-action__actions">
          <button
            type="button"
            className="ds-btn ds-btn--secondary"
            onClick={() => {
              setProposal(null);
              setStaleNotice(null);
              setStage("form");
            }}
          >
            Revisar e preparar novamente
          </button>
          <button
            type="button"
            className="ds-btn ds-btn--ghost"
            onClick={onCancel}
          >
            Cancelar
          </button>
        </div>
      ) : null}
    </div>
  );
}
