/**
 * Presentational read view of one Diagnostic — renders only canonical
 * contract fields. INFERRED ≠ FACT, VALIDATED ≠ FACT, CONTRIBUTES_TO is the
 * only causal relation, CONTRADICTS evidence is first-class, and no generic
 * edit/remove affordances exist here.
 */
import type { ReactNode } from "react";

import {
  ActionButton,
  EmptyState,
  emptyStateCardBemClasses,
} from "@delpi/plugin-ui/index";

import { StateBox } from "../../../components/StateBox";
import { TmSectionCard, TmStatusBadge } from "../../../components/tmChromeUi";
import type {
  DiagnosticConclusion,
  DiagnosticEvidenceLinkView,
  DiagnosticFinding,
  DiagnosticHypothesis,
  DiagnosticManageAction,
  DiagnosticReadContext,
} from "../../../data/api/transformometroDiagnosticApi";
import {
  CAUSAL_RELATION_LABEL,
  DIAGNOSTIC_ACTION_LABELS,
  EFFECTIVE_VALIDATION_HELP,
  EFFECTIVE_VALIDATION_LABELS,
  FINDING_ROLE_LABELS,
  effectiveValidationLabel,
  epistemicLabel,
  evidenceRelationLabel,
  lifecycleLabel,
} from "./diagnosticDisplay";

const EMPTY_CARD_CLASSES = emptyStateCardBemClasses("ds");

type StartAction = (
  action: DiagnosticManageAction,
  targetId?: string | null,
  targetLabel?: string | null,
) => void;

type DiagnosticActionFamily =
  | "findings"
  | "hypotheses"
  | "causal"
  | "evidence"
  | "conclusion";

/** Maps the 13 canonical actions to the section that owns the inline form. */
function diagnosticActionFamily(
  action: DiagnosticManageAction,
): DiagnosticActionFamily {
  switch (action) {
    case "add_finding":
      return "findings";
    case "add_causal_link":
      return "causal";
    case "add_evidence_link":
      return "evidence";
    case "add_conclusion":
    case "validate_conclusion":
    case "reject_conclusion":
    case "supersede_conclusion":
      return "conclusion";
    default:
      return "hypotheses";
  }
}

function EffectiveBadge({ value }: { value: string }) {
  const variant =
    value === "STALE_EVIDENCE"
      ? "warning"
      : value === "REVALIDATION_REQUIRED"
        ? "danger"
        : "success";
  return (
    <TmStatusBadge
      label={`Validação efetiva: ${effectiveValidationLabel(value)}`}
      variant={variant}
    />
  );
}

function epistemicBadgeVariant(value: string): "neutral" | "info" | "warning" {
  if (value === "OBSERVED") return "info";
  if (value === "CALCULATED" || value === "INFERRED") return "neutral";
  return "warning";
}

function lifecycleBadgeVariant(value: string): "neutral" | "success" | "danger" | "info" {
  if (value === "VALIDATED") return "info";
  if (value === "REJECTED") return "danger";
  if (value === "SUPERSEDED") return "neutral";
  return "neutral";
}

function statementOf(
  detail: DiagnosticReadContext,
  targetId: string | null,
): string {
  if (!targetId) return "Diagnóstico";
  const d = detail.diagnostic;
  const found =
    d.findings.find((f) => f.finding_id === targetId)?.statement ??
    d.hypotheses.find((h) => h.hypothesis_id === targetId)?.statement ??
    d.conclusions.find((c) => c.conclusion_id === targetId)?.statement;
  return found ?? targetId;
}

function EvidenceLinkRow({
  link,
  unresolved,
  detail,
}: {
  link: DiagnosticEvidenceLinkView;
  unresolved: boolean;
  detail: DiagnosticReadContext;
}) {
  const isContradicts = link.relation === "CONTRADICTS";
  return (
    <li
      className={[
        "tm-diagnostic-evidence",
        isContradicts ? "tm-diagnostic-evidence--contradicts" : "",
        unresolved ? "tm-diagnostic-evidence--unresolved" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <TmStatusBadge
        label={evidenceRelationLabel(link.relation)}
        variant={
          link.relation === "CONTRADICTS"
            ? "danger"
            : link.relation === "SUPPORTS"
              ? "info"
              : "neutral"
        }
      />
      <span className="tm-diagnostic-evidence__name">
        {link.evidence?.descricao || link.evidence?.nome_arquivo || link.evidence_id}
      </span>
      <span className="ds-hint">
        {link.target_id ? `→ ${statementOf(detail, link.target_id)}` : ""}
      </span>
      {unresolved || link.resolved_in_revision === false ? (
        <TmStatusBadge label="Vínculo não resolvido nesta revisão" variant="warning" />
      ) : null}
    </li>
  );
}

function ClaimActions({
  claimId,
  claimLabel,
  actions,
  onStartAction,
}: {
  claimId: string;
  claimLabel: string;
  actions: DiagnosticManageAction[];
  onStartAction: StartAction;
}) {
  return (
    <div className="tm-diagnostic-item__actions" role="group" aria-label={`Ações: ${claimLabel}`}>
      {actions.map((action) => (
        <ActionButton
          key={action}
          variant="ghost"
          onClick={() => onStartAction(action, claimId, claimLabel)}
        >
          {DIAGNOSTIC_ACTION_LABELS[action]}
        </ActionButton>
      ))}
    </div>
  );
}

const HYPOTHESIS_ACTIONS: DiagnosticManageAction[] = [
  "validate_hypothesis",
  "reject_hypothesis",
  "supersede_hypothesis",
  "mark_hypothesis_stale_evidence",
  "mark_hypothesis_revalidation_required",
];

const CONCLUSION_ACTIONS: DiagnosticManageAction[] = [
  "validate_conclusion",
  "reject_conclusion",
  "supersede_conclusion",
];

export function DiagnosticContent({
  detail,
  busy = false,
  activeAction = null,
  actionSlot = null,
  onStartAction,
}: {
  detail: DiagnosticReadContext;
  busy?: boolean;
  /** Action whose inline form is open; rendered inside its owning section. */
  activeAction?: DiagnosticManageAction | null;
  /** Governed action panel node, injected into the owning SectionCard. */
  actionSlot?: ReactNode;
  onStartAction: StartAction;
}) {
  const d = detail.diagnostic;
  const unresolvedLinks = new Set(detail.data_quality?.unresolved_evidence_links ?? []);
  const signals = detail.data_quality?.signals ?? [];

  const hasStale = d.hypotheses.some((h) => h.effective_validation === "STALE_EVIDENCE") ||
    d.conclusions.some((c) => c.effective_validation === "STALE_EVIDENCE");
  const hasRevalidation =
    d.hypotheses.some((h) => h.effective_validation === "REVALIDATION_REQUIRED") ||
    d.conclusions.some((c) => c.effective_validation === "REVALIDATION_REQUIRED");

  const family = activeAction ? diagnosticActionFamily(activeAction) : null;
  const inlinePanel = (target: DiagnosticActionFamily) =>
    family === target ? actionSlot : null;

  return (
    <div className="tm-diagnostic" aria-busy={busy || undefined}>
      {hasRevalidation ? (
        <StateBox variant="warning">
          {EFFECTIVE_VALIDATION_HELP.REVALIDATION_REQUIRED} Há itens marcados como
          “{EFFECTIVE_VALIDATION_LABELS.REVALIDATION_REQUIRED}”.
        </StateBox>
      ) : hasStale ? (
        <StateBox variant="warning">
          {EFFECTIVE_VALIDATION_HELP.STALE_EVIDENCE} Há itens marcados como
          “{EFFECTIVE_VALIDATION_LABELS.STALE_EVIDENCE}”.
        </StateBox>
      ) : null}

      {signals.length ? (
        <StateBox variant="default">
          Sinais de qualidade dos dados: {signals.map((s) => s.detail || s.code).join("; ")}
        </StateBox>
      ) : null}

      <TmSectionCard
        title="Problema investigado"
        hint="Problema que orienta este diagnóstico. Registrado na criação e mantido somente leitura nesta versão."
      >
        <p className="tm-diagnostic__statement">{d.problem_statement}</p>
      </TmSectionCard>

      <TmSectionCard
        title="Achados"
        hint="Achados são registros do que se observa. “Observado” veio da operação; “Calculado” deriva de cálculo — nenhum dos dois é opinião. “Sintoma” é o papel do achado, separado da natureza epistêmica."
        actions={
          <ActionButton variant="ghost" onClick={() => onStartAction("add_finding")}>
            {DIAGNOSTIC_ACTION_LABELS.add_finding}
          </ActionButton>
        }
      >
        {d.findings.length === 0 ? (
          <EmptyState
            classNames={EMPTY_CARD_CLASSES}
            defaultMessage="Nenhum achado registrado."
          />
        ) : (
          <ul className="tm-diagnostic__list">
            {d.findings.map((f: DiagnosticFinding) => (
              <li key={f.finding_id} className="tm-diagnostic-item">
                <p className="tm-diagnostic-item__statement">{f.statement}</p>
                <div className="tm-diagnostic-item__meta">
                  <TmStatusBadge
                    label={epistemicLabel(f.epistemic_state)}
                    variant={epistemicBadgeVariant(f.epistemic_state)}
                  />
                  {f.role ? (
                    <TmStatusBadge
                      label={`Papel: ${FINDING_ROLE_LABELS[f.role] ?? f.role}`}
                      variant="neutral"
                    />
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
        )}
        {inlinePanel("findings")}
      </TmSectionCard>

      <TmSectionCard
        title="Hipóteses"
        hint="Hipóteses são interpretações — sempre “Inferido”, mesmo quando validadas. “Validada” indica revisão registrada; não transforma a hipótese em fato."
        actions={
          <ActionButton variant="ghost" onClick={() => onStartAction("add_hypothesis")}>
            {DIAGNOSTIC_ACTION_LABELS.add_hypothesis}
          </ActionButton>
        }
      >
        {d.hypotheses.length === 0 ? (
          <EmptyState
            classNames={EMPTY_CARD_CLASSES}
            defaultMessage="Nenhuma hipótese formulada."
          />
        ) : (
          <ul className="tm-diagnostic__list">
            {d.hypotheses.map((h: DiagnosticHypothesis) => (
              <li key={h.hypothesis_id} className="tm-diagnostic-item">
                <p className="tm-diagnostic-item__statement">{h.statement}</p>
                <div className="tm-diagnostic-item__meta">
                  {/* INFERRED stays visible even when lifecycle is VALIDATED */}
                  <TmStatusBadge
                    label={epistemicLabel(h.epistemic_state ?? "INFERRED")}
                    variant="neutral"
                  />
                  <TmStatusBadge
                    label={`Status: ${lifecycleLabel(h.lifecycle)}`}
                    variant={lifecycleBadgeVariant(h.lifecycle)}
                  />
                  {h.effective_validation && h.effective_validation !== "CURRENT" ? (
                    <EffectiveBadge value={h.effective_validation} />
                  ) : null}
                </div>
                <ClaimActions
                  claimId={h.hypothesis_id}
                  claimLabel={h.statement}
                  actions={HYPOTHESIS_ACTIONS}
                  onStartAction={onStartAction}
                />
              </li>
            ))}
          </ul>
        )}
        {inlinePanel("hypotheses")}
      </TmSectionCard>

      <TmSectionCard
        title="Análise causal"
        hint="Relações causais indicam apenas que uma hipótese contribui para outra ou para um achado — nunca que ela causa ou prova."
        actions={
          <ActionButton
            variant="ghost"
            disabled={d.hypotheses.length === 0}
            onClick={() => onStartAction("add_causal_link")}
          >
            {DIAGNOSTIC_ACTION_LABELS.add_causal_link}
          </ActionButton>
        }
      >
        {d.causal_links.length === 0 ? (
          <EmptyState
            classNames={EMPTY_CARD_CLASSES}
            defaultMessage="Nenhuma relação causal registrada."
          />
        ) : (
          <ul className="tm-diagnostic__list tm-diagnostic-causal">
            {d.causal_links.map((link) => (
              <li key={link.link_id} className="tm-diagnostic-causal__row">
                <span className="tm-diagnostic-causal__source">
                  {statementOf(detail, link.source_hypothesis_id)}
                </span>
                <span className="tm-diagnostic-causal__arrow" aria-hidden="true">→</span>
                <span className="tm-diagnostic-causal__relation">{CAUSAL_RELATION_LABEL}</span>
                <span className="tm-diagnostic-causal__target">
                  {statementOf(detail, link.target_id)}
                </span>
              </li>
            ))}
          </ul>
        )}
        {inlinePanel("causal")}
      </TmSectionCard>

      <TmSectionCard
        title="Evidências vinculadas"
        hint="Somente evidências já registradas na revisão podem ser vinculadas — sustentam, contradizem ou contextualizam o item. “Contradiz” é exibido explicitamente."
        actions={
          <ActionButton variant="ghost" onClick={() => onStartAction("add_evidence_link")}>
            {DIAGNOSTIC_ACTION_LABELS.add_evidence_link}
          </ActionButton>
        }
      >
        {detail.evidence_links.length === 0 ? (
          <EmptyState
            classNames={EMPTY_CARD_CLASSES}
            defaultMessage="Nenhuma evidência vinculada."
          />
        ) : (
          <ul className="tm-diagnostic__list">
            {detail.evidence_links.map((link) => (
              <EvidenceLinkRow
                key={link.link_id}
                link={link}
                detail={detail}
                unresolved={unresolvedLinks.has(link.link_id)}
              />
            ))}
          </ul>
        )}
        {inlinePanel("evidence")}
      </TmSectionCard>

      <TmSectionCard
        title="Conclusão diagnóstica"
        hint="A conclusão é sempre uma interpretação (“Inferido”). Status e validação efetiva aparecem separados; conclusão validada não é fato."
        actions={
          <ActionButton variant="ghost" onClick={() => onStartAction("add_conclusion")}>
            {DIAGNOSTIC_ACTION_LABELS.add_conclusion}
          </ActionButton>
        }
      >
        {d.conclusions.length === 0 ? (
          <EmptyState
            classNames={EMPTY_CARD_CLASSES}
            defaultMessage="Nenhuma conclusão registrada."
          />
        ) : (
          <ul className="tm-diagnostic__list">
            {d.conclusions.map((c: DiagnosticConclusion) => (
              <li key={c.conclusion_id} className="tm-diagnostic-item">
                <p className="tm-diagnostic-item__statement">{c.statement}</p>
                {c.rationale ? (
                  <p className="tm-diagnostic-item__rationale ds-hint">
                    Justificativa: {c.rationale}
                  </p>
                ) : null}
                <div className="tm-diagnostic-item__meta">
                  <TmStatusBadge
                    label={epistemicLabel(c.epistemic_state ?? "INFERRED")}
                    variant="neutral"
                  />
                  <TmStatusBadge
                    label={`Status: ${lifecycleLabel(c.lifecycle)}`}
                    variant={lifecycleBadgeVariant(c.lifecycle)}
                  />
                  <EffectiveBadge value={c.effective_validation ?? "CURRENT"} />
                </div>
                {(c.hypothesis_ids.length > 0 ||
                  c.finding_ids.length > 0 ||
                  c.root_cause_hypothesis_id) ? (
                  <p className="tm-diagnostic-item__refs ds-hint">
                    {c.hypothesis_ids.length
                      ? `Hipóteses: ${c.hypothesis_ids
                          .map((id) => statementOf(detail, id))
                          .join("; ")}. `
                      : ""}
                    {c.finding_ids.length
                      ? `Achados: ${c.finding_ids
                          .map((id) => statementOf(detail, id))
                          .join("; ")}. `
                      : ""}
                    {c.root_cause_hypothesis_id
                      ? `Causa-raiz apontada: ${statementOf(detail, c.root_cause_hypothesis_id)}.`
                      : ""}
                  </p>
                ) : null}
                <ClaimActions
                  claimId={c.conclusion_id}
                  claimLabel={c.statement}
                  actions={CONCLUSION_ACTIONS}
                  onStartAction={onStartAction}
                />
              </li>
            ))}
          </ul>
        )}
        {inlinePanel("conclusion")}
      </TmSectionCard>
    </div>
  );
}
