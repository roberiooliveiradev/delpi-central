/**
 * Validação humana do item — P2 (A2).
 *
 * Consome as rotas de validação da BFF (`decide`, `reverse`, `not-applicable`,
 * `cancel`, `corrections`). «Anexado» não é «validado»: cada evidência exige
 * decisão humana explícita — por anexo (`PER_ATTACHMENT`) ou por conjunto
 * (`WHOLE_SET`). Toda decisão é append-only e visível no histórico.
 */
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { ActionButton } from "@delpi/plugin-ui/index";

import { ApiError } from "../../api/httpClient";
import {
  cancelChecklistItem,
  decideDocumentEvidence,
  decideItemEvidenceSet,
  getItemValidation,
  listItemCorrections,
  markItemNotApplicable,
  requestItemCorrection,
  reverseRejection,
  reviewItemCorrection,
  revertItemNotApplicable,
  type CompetenceChecklistItemDetail,
  type ItemCorrection,
  type ItemValidation,
  type RejectionReason,
} from "../../api/competencesApi";
import {
  listClosingDocuments,
  type ClosingDocument,
} from "../../api/documentsApi";
import {
  CfFeedbackMessage,
  CfQueryErrorBanner,
  CfSectionLoading,
} from "../../app/cfFeedbackUi";
import {
  CfDialog,
  CfEmptyState,
  CfStatusBadge,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import { formatDateTime } from "../../utils/formatters";

type PanelError = { status: number; code: string | null; message: string };

const ERROR_MESSAGES: Record<string, string> = {
  forbidden: "Você não tem autorização para esta decisão de validação.",
  unauthorized: "Sessão expirada — autentique-se novamente.",
  competence_not_opened: "Competência não aberta.",
  item_not_found: "Item fora do escopo desta competência ou filial.",
  document_not_found:
    "Documento fora do escopo desta competência ou filial.",
  decision_not_found: "Decisão não encontrada.",
  invalid_decision:
    "Transição não permitida para o estado atual da evidência.",
  rejection_reason_required:
    "Informe o motivo estruturado da rejeição.",
  comment_required: "Motivo «Outro» exige comentário explicativo.",
  not_applicable_not_allowed:
    "Somente itens condicionais podem ser marcados como N/A.",
  already_not_applicable: "O item já está marcado como N/A.",
  not_not_applicable: "O item não está marcado como N/A.",
  item_cancelled: "Item cancelado não aceita novas decisões.",
  set_composition_changed:
    "O conjunto mudou desde a decisão — valide a composição atual.",
  replacement_requires_revalidation:
    "Nova versão anexada — revalide antes de reverter.",
  reversal_not_allowed:
    "Somente o mesmo validador pode reverter, sem nova versão anexada.",
  no_correction_pending: "Não há correção pendente neste item.",
  correction_field_not_allowed: "Campo não elegível para correção.",
  justification_required: "Justificativa obrigatória.",
};

function toPanelError(error: unknown, fallback: string): PanelError {
  if (error instanceof ApiError) {
    return {
      status: error.status,
      code: error.code,
      message:
        (error.code && ERROR_MESSAGES[error.code]) || error.message,
    };
  }
  return { status: 0, code: null, message: fallback };
}

export const REJECTION_REASON_LABELS: Record<RejectionReason, string> = {
  WRONG_COMPETENCE: "Competência incorreta",
  INCOMPLETE: "Documento incompleto",
  ILLEGIBLE: "Arquivo ilegível",
  DIVERGENT: "Informação divergente",
  WRONG_DOCUMENT: "Documento incorreto",
  OTHER: "Outro",
};

const DECISION_LABELS: Record<string, string> = {
  ACCEPTED: "Aceito",
  REJECTED: "Rejeitado",
  REVERSED: "Rejeição revertida",
};

const CORRECTION_STATUS_LABELS: Record<string, string> = {
  PENDING: "Aguardando revisão",
  APPROVED: "Aprovada",
  REJECTED: "Rejeitada",
};

const CORRECTION_FIELDS: {
  value: string;
  label: string;
  options?: { value: string; label: string }[];
}[] = [
  { value: "name", label: "Nome do entregável" },
  { value: "purpose", label: "Finalidade" },
  { value: "requirement_notes", label: "Notas de exigência" },
  {
    value: "validation_scope",
    label: "Regra de validação",
    options: [
      { value: "PER_ATTACHMENT", label: "Por anexo" },
      { value: "WHOLE_SET", label: "Conjunto" },
    ],
  },
  {
    value: "applicability",
    label: "Obrigatoriedade",
    options: [
      { value: "REQUIRED", label: "Obrigatório" },
      { value: "CONDITIONAL", label: "Condicional" },
      { value: "OPTIONAL", label: "Opcional" },
    ],
  },
  {
    value: "branch_scope",
    label: "Escopo de filial",
    options: [
      { value: "MATRIX", label: "Matriz" },
      { value: "BRANCH", label: "Filial" },
      { value: "BOTH", label: "Matriz e filiais" },
    ],
  },
  {
    value: "recipient_area",
    label: "Destinatário",
    options: [
      { value: "CONTABIL", label: "Contábil" },
      { value: "FISCAL", label: "Fiscal" },
    ],
  },
  { value: "totvs_report_ref", label: "Relatório TOTVS (referência)" },
];

function decisionBadge(decision: string | null | undefined) {
  if (!decision) {
    return <CfStatusBadge label="Aguardando validação" variant="neutral" />;
  }
  const variant =
    decision === "ACCEPTED"
      ? "success"
      : decision === "REJECTED"
        ? "danger"
        : "neutral";
  return (
    <CfStatusBadge
      label={DECISION_LABELS[decision] ?? decision}
      variant={variant}
    />
  );
}

type Props = {
  period: string;
  item: CompetenceChecklistItemDetail;
  onChanged: () => void;
};

type RejectTarget =
  | { kind: "doc"; documentId: string; label: string }
  | { kind: "set" };

type JustificationAction = "na" | "revert_na" | "cancel";

export function ItemValidationPanel({ period, item, onChanged }: Props) {
  const [nonce, setNonce] = useState(0);
  const [validation, setValidation] = useState<{
    key: string;
    data: ItemValidation;
  } | null>(null);
  const [documents, setDocuments] = useState<{
    key: string;
    items: ClosingDocument[];
  } | null>(null);
  const [corrections, setCorrections] = useState<{
    key: string;
    items: ItemCorrection[];
  } | null>(null);
  const [error, setError] = useState<{ key: string; error: PanelError } | null>(
    null,
  );
  const [actionError, setActionError] = useState<PanelError | null>(null);
  const [busy, setBusy] = useState(false);

  const [rejectTarget, setRejectTarget] = useState<RejectTarget | null>(null);
  const [rejectReason, setRejectReason] = useState<RejectionReason | "">("");
  const [rejectComment, setRejectComment] = useState("");

  const [reverseTargetId, setReverseTargetId] = useState<string | null>(
    null,
  );
  const [reverseResult, setReverseResult] = useState<
    "UNDER_REVIEW" | "ACCEPTED"
  >("UNDER_REVIEW");
  const [reverseJustification, setReverseJustification] = useState("");

  const [justifyAction, setJustifyAction] =
    useState<JustificationAction | null>(null);
  const [justification, setJustification] = useState("");

  const [correctionOpen, setCorrectionOpen] = useState(false);
  const [correctionField, setCorrectionField] = useState("name");
  const [correctionValue, setCorrectionValue] = useState("");
  const [correctionJustification, setCorrectionJustification] = useState("");

  const [reviewTarget, setReviewTarget] = useState<ItemCorrection | null>(null);
  const [reviewReason, setReviewReason] = useState("");

  const requestId = useRef(0);
  const itemKey = item.item_key;
  const dataKey = `${period}:${itemKey}:${nonce}`;

  const currentValidation =
    validation?.key === dataKey ? validation.data : null;
  const currentDocs =
    documents?.key === dataKey ? documents.items : null;
  const currentCorrections =
    corrections?.key === dataKey ? corrections.items : null;
  const currentError = error?.key === dataKey ? error.error : null;
  const loading = currentValidation === null && !currentError;

  const docNames = useMemo(() => {
    const map = new Map<string, string>();
    for (const doc of currentDocs ?? []) {
      map.set(
        doc.document_id,
        doc.original_name ?? doc.title ?? "Documento",
      );
    }
    return map;
  }, [currentDocs]);

  useEffect(() => {
    const id = ++requestId.current;
    const controller = new AbortController();
    const opts = { signal: controller.signal };
    Promise.all([
      getItemValidation(period, itemKey, opts),
      listClosingDocuments(
        period,
        { snapshotItemId: item.snapshot_item_id },
        opts,
      ),
      listItemCorrections(period, itemKey, opts),
    ])
      .then(([validationData, docsResult, correctionItems]) => {
        if (controller.signal.aborted || requestId.current !== id) return;
        setValidation({ key: dataKey, data: validationData });
        setDocuments({ key: dataKey, items: docsResult.documents });
        setCorrections({ key: dataKey, items: correctionItems });
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted || requestId.current !== id) return;
        setError({
          key: dataKey,
          error: toPanelError(
            err,
            "Falha ao consultar a validação do item.",
          ),
        });
      });
    return () => controller.abort();
  }, [period, itemKey, item.snapshot_item_id, dataKey]);

  const run = useCallback(
    (work: () => Promise<unknown>) => {
      setBusy(true);
      setActionError(null);
      work()
        .then(() => {
          setBusy(false);
          setNonce((n) => n + 1);
          onChanged();
        })
        .catch((err: unknown) => {
          setBusy(false);
          setActionError(
            toPanelError(err, "A ação não pôde ser concluída."),
          );
        });
    },
    [onChanged],
  );

  const decideDoc = useCallback(
    (documentId: string, decision: "ACCEPTED" | "REJECTED", payload = {}) =>
      run(() =>
        decideDocumentEvidence(period, documentId, {
          decision,
          ...payload,
        }),
      ),
    [period, run],
  );

  const decideSet = useCallback(
    (decision: "ACCEPTED" | "REJECTED", payload = {}) =>
      run(() =>
        decideItemEvidenceSet(period, itemKey, { decision, ...payload }),
      ),
    [period, itemKey, run],
  );

  const submitReject = useCallback(() => {
    if (!rejectTarget || !rejectReason) return;
    const payload = {
      reason_code: rejectReason,
      ...(rejectReason === "OTHER" ? { comment: rejectComment } : {}),
    };
    if (rejectTarget.kind === "doc") {
      decideDoc(rejectTarget.documentId, "REJECTED", payload);
    } else {
      decideSet("REJECTED", payload);
    }
    setRejectTarget(null);
    setRejectReason("");
    setRejectComment("");
  }, [rejectTarget, rejectReason, rejectComment, decideDoc, decideSet]);

  const submitReverse = useCallback(() => {
    if (!reverseTargetId || !reverseJustification.trim()) return;
    run(() =>
      reverseRejection(period, reverseTargetId, {
        result_state: reverseResult,
        justification: reverseJustification.trim(),
      }),
    );
    setReverseTargetId(null);
    setReverseJustification("");
  }, [period, reverseTargetId, reverseResult, reverseJustification, run]);

  const submitJustification = useCallback(() => {
    if (!justifyAction || !justification.trim()) return;
    const text = justification.trim();
    const work =
      justifyAction === "na"
        ? () => markItemNotApplicable(period, itemKey, text)
        : justifyAction === "revert_na"
          ? () => revertItemNotApplicable(period, itemKey, text)
          : () => cancelChecklistItem(period, itemKey, text);
    run(work);
    setJustifyAction(null);
    setJustification("");
  }, [period, itemKey, justifyAction, justification, run]);

  const submitCorrection = useCallback(() => {
    if (!correctionValue || !correctionJustification.trim()) return;
    run(() =>
      requestItemCorrection(period, itemKey, {
        changes: { [correctionField]: correctionValue },
        justification: correctionJustification.trim(),
      }),
    );
    setCorrectionOpen(false);
    setCorrectionValue("");
    setCorrectionJustification("");
  }, [
    period,
    itemKey,
    correctionField,
    correctionValue,
    correctionJustification,
    run,
  ]);

  const submitReview = useCallback(
    (approve: boolean) => {
      if (!reviewTarget) return;
      run(() =>
        reviewItemCorrection(period, itemKey, reviewTarget.correction_id, {
          approve,
          ...(reviewReason.trim() ? { review_reason: reviewReason } : {}),
        }),
      );
      setReviewTarget(null);
      setReviewReason("");
    },
    [period, itemKey, reviewTarget, reviewReason, run],
  );

  const activeDocs = useMemo(
    () =>
      (currentValidation?.documents ?? []).filter(
        (d) => d.state !== "CANCELLED",
      ),
    [currentValidation],
  );

  const latestSetDecision = useMemo(
    () =>
      [...(currentValidation?.decisions ?? [])]
        .filter((d) => d.scope === "WHOLE_SET")
        .sort((a, b) => b.created_at.localeCompare(a.created_at))[0] ?? null,
    [currentValidation],
  );

  const terminal =
    item.state === "CANCELLED" || item.state === "NOT_APPLICABLE";

  const fieldSpec = CORRECTION_FIELDS.find(
    (f) => f.value === correctionField,
  );

  return (
    <div className="cf-validation-panel">
      {actionError ? (
        <CfFeedbackMessage intent="error" title="Ação não concluída">
          {actionError.message}
        </CfFeedbackMessage>
      ) : null}

      {currentError ? (
        <CfQueryErrorBanner
          error={currentError}
          dataset="a validação do item"
          onRetry={() => setNonce((n) => n + 1)}
        />
      ) : loading ? (
        <CfSectionLoading label="Carregando validação…" variant="compact" />
      ) : (
        <>
          <p className="cf-validation-panel__scope">
            Regra de validação:{" "}
            {currentValidation?.validation_scope === "WHOLE_SET"
              ? "conjunto (a composição inteira é avaliada de uma vez)"
              : "por anexo (cada arquivo é avaliado individualmente)"}
            .
          </p>

          {activeDocs.length > 0 ? (
            <ul className="cf-validation-panel__docs">
              {activeDocs.map((doc) => {
                const decision = doc.current_version_decision;
                const name =
                  docNames.get(doc.document_id) ?? doc.document_id;
                return (
                  <li
                    key={doc.document_id}
                    className="cf-validation-panel__doc"
                  >
                    <div className="cf-validation-panel__doc-meta">
                      <p className="cf-validation-panel__doc-name">
                        {name} · v{doc.current_version_no}
                      </p>
                      {decision ? (
                        <p className="cf-validation-panel__doc-detail">
                          {decision.reason_code
                            ? `${
                                REJECTION_REASON_LABELS[
                                  decision.reason_code
                                ] ?? decision.reason_code
                              } · `
                            : ""}
                          {decision.decided_by} ·{" "}
                          {formatDateTime(decision.created_at)}
                        </p>
                      ) : null}
                    </div>
                    <div className="cf-validation-panel__doc-actions">
                      {decisionBadge(decision?.decision)}
                      {currentValidation?.validation_scope ===
                        "PER_ATTACHMENT" && !terminal ? (
                        <>
                          <ActionButton
                            variant="ghost"
                            disabled={busy}
                            onClick={() =>
                              decideDoc(doc.document_id, "ACCEPTED")
                            }
                          >
                            Aceitar
                          </ActionButton>
                          <ActionButton
                            variant="ghost"
                            disabled={busy}
                            onClick={() =>
                              setRejectTarget({
                                kind: "doc",
                                documentId: doc.document_id,
                                label: name,
                              })
                            }
                          >
                            Rejeitar
                          </ActionButton>
                        </>
                      ) : null}
                      {decision?.decision === "REJECTED" && !terminal ? (
                        <ActionButton
                          variant="ghost"
                          disabled={busy}
                          onClick={() => {
                            setReverseTargetId(decision.decision_id);
                            setReverseResult("UNDER_REVIEW");
                            setReverseJustification("");
                          }}
                        >
                          Reverter rejeição
                        </ActionButton>
                      ) : null}
                    </div>
                  </li>
                );
              })}
            </ul>
          ) : (
            <CfEmptyState
              classNames={cfEmptyStateClassNames}
              defaultMessage="Nenhuma evidência ativa vinculada ao item."
            />
          )}

          {currentValidation?.validation_scope === "WHOLE_SET" &&
          !terminal ? (
            <div className="cf-validation-panel__set-actions">
              {latestSetDecision
                ? decisionBadge(latestSetDecision.decision)
                : null}
              <ActionButton
                variant="ghost"
                disabled={busy || activeDocs.length === 0}
                onClick={() => decideSet("ACCEPTED")}
              >
                Aceitar conjunto
              </ActionButton>
              <ActionButton
                variant="ghost"
                disabled={busy || activeDocs.length === 0}
                onClick={() => setRejectTarget({ kind: "set" })}
              >
                Rejeitar conjunto
              </ActionButton>
              {latestSetDecision?.decision === "REJECTED" ? (
                <ActionButton
                  variant="ghost"
                  disabled={busy}
                  onClick={() => {
                    setReverseTargetId(latestSetDecision.decision_id);
                    setReverseResult("UNDER_REVIEW");
                    setReverseJustification("");
                  }}
                >
                  Reverter rejeição
                </ActionButton>
              ) : null}
            </div>
          ) : null}

          <div className="cf-validation-panel__item-actions">
            {item.applicability === "CONDITIONAL" &&
            item.state !== "NOT_APPLICABLE" &&
            item.state !== "CANCELLED" ? (
              <ActionButton
                variant="ghost"
                disabled={busy}
                onClick={() => setJustifyAction("na")}
              >
                Marcar como não aplicável
              </ActionButton>
            ) : null}
            {item.state === "NOT_APPLICABLE" ? (
              <ActionButton
                variant="ghost"
                disabled={busy}
                onClick={() => setJustifyAction("revert_na")}
              >
                Reverter N/A
              </ActionButton>
            ) : null}
            {item.state === "EXPECTED" ? (
              <ActionButton
                variant="ghost"
                disabled={busy}
                onClick={() => setJustifyAction("cancel")}
              >
                Cancelar item
              </ActionButton>
            ) : null}
            {!terminal ? (
              <ActionButton
                variant="ghost"
                disabled={busy}
                onClick={() => setCorrectionOpen(true)}
              >
                Solicitar correção
              </ActionButton>
            ) : null}
          </div>

          {(currentCorrections ?? []).length > 0 ? (
            <div className="cf-validation-panel__corrections">
              <h4>Correções estruturais</h4>
              <ul>
                {(currentCorrections ?? []).map((correction) => (
                  <li key={correction.correction_id}>
                    <div className="cf-validation-panel__correction-meta">
                      <p>
                        <CfStatusBadge
                          label={
                            CORRECTION_STATUS_LABELS[
                              correction.status
                            ] ?? correction.status
                          }
                          variant={
                            correction.status === "APPROVED"
                              ? "success"
                              : correction.status === "REJECTED"
                                ? "danger"
                                : "neutral"
                          }
                        />{" "}
                        {Object.entries(correction.changes)
                          .map(([field, value]) => `${field} → ${value}`)
                          .join("; ")}
                      </p>
                      <p className="cf-validation-panel__doc-detail">
                        {correction.justification} ·{" "}
                        {correction.requested_by} ·{" "}
                        {formatDateTime(correction.requested_at)}
                      </p>
                    </div>
                    {correction.status === "PENDING" ? (
                      <div className="cf-validation-panel__doc-actions">
                        <ActionButton
                          variant="ghost"
                          disabled={busy}
                          onClick={() => {
                            setReviewTarget(correction);
                            setReviewReason("");
                          }}
                        >
                          Revisar
                        </ActionButton>
                      </div>
                    ) : null}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {(currentValidation?.decisions ?? []).length > 0 ? (
            <div className="cf-validation-panel__history">
              <h4>Histórico de decisões</h4>
              <ul>
                {(currentValidation?.decisions ?? []).map((decision) => (
                  <li key={decision.decision_id}>
                    {decisionBadge(decision.decision)}{" "}
                    {decision.reason_code
                      ? `· ${
                          REJECTION_REASON_LABELS[decision.reason_code] ??
                          decision.reason_code
                        }`
                      : ""}
                    {decision.comment ? ` — ${decision.comment}` : ""}
                    {decision.result_state
                      ? ` → ${
                          decision.result_state === "ACCEPTED"
                            ? "Aceito"
                            : "Em revisão"
                        }`
                      : ""}
                    <span className="cf-validation-panel__doc-detail">
                      {" "}
                      · {decision.decided_by} ·{" "}
                      {formatDateTime(decision.created_at)}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </>
      )}

      {rejectTarget ? (
        <CfDialog
          open
          title={
            rejectTarget.kind === "doc"
              ? `Rejeitar evidência — ${rejectTarget.label}`
              : "Rejeitar conjunto de evidências"
          }
          onClose={() => !busy && setRejectTarget(null)}
          closeAriaLabel="Fechar rejeição"
        >
          <div className="cf-validation-panel__form">
            <label>
              Motivo da rejeição
              <select
                value={rejectReason}
                disabled={busy}
                onChange={(e) =>
                  setRejectReason(e.target.value as RejectionReason)
                }
              >
                <option value="">Selecione…</option>
                {Object.entries(REJECTION_REASON_LABELS).map(
                  ([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ),
                )}
              </select>
            </label>
            {rejectReason === "OTHER" ? (
              <label>
                Comentário (obrigatório para «Outro»)
                <textarea
                  value={rejectComment}
                  disabled={busy}
                  rows={3}
                  onChange={(e) => setRejectComment(e.target.value)}
                />
              </label>
            ) : null}
            <div className="cf-validation-panel__form-actions">
              <ActionButton
                variant="primary"
                disabled={
                  busy ||
                  !rejectReason ||
                  (rejectReason === "OTHER" && !rejectComment.trim())
                }
                onClick={submitReject}
              >
                Confirmar rejeição
              </ActionButton>
              <ActionButton
                variant="ghost"
                disabled={busy}
                onClick={() => setRejectTarget(null)}
              >
                Voltar
              </ActionButton>
            </div>
          </div>
        </CfDialog>
      ) : null}

      {reverseTargetId ? (
        <CfDialog
          open
          title="Reverter rejeição"
          onClose={() => !busy && setReverseTargetId(null)}
          closeAriaLabel="Fechar reversão"
        >
          <div className="cf-validation-panel__form">
            <label>
              Estado resultante
              <select
                value={reverseResult}
                disabled={busy}
                onChange={(e) =>
                  setReverseResult(
                    e.target.value as "UNDER_REVIEW" | "ACCEPTED",
                  )
                }
              >
                <option value="UNDER_REVIEW">Em revisão</option>
                <option value="ACCEPTED">Aceito</option>
              </select>
            </label>
            <label>
              Justificativa da reversão
              <textarea
                value={reverseJustification}
                disabled={busy}
                rows={3}
                onChange={(e) => setReverseJustification(e.target.value)}
              />
            </label>
            <div className="cf-validation-panel__form-actions">
              <ActionButton
                variant="primary"
                disabled={busy || !reverseJustification.trim()}
                onClick={submitReverse}
              >
                Confirmar reversão
              </ActionButton>
              <ActionButton
                variant="ghost"
                disabled={busy}
                onClick={() => setReverseTargetId(null)}
              >
                Voltar
              </ActionButton>
            </div>
          </div>
        </CfDialog>
      ) : null}

      {justifyAction ? (
        <CfDialog
          open
          title={
            justifyAction === "na"
              ? "Marcar como não aplicável"
              : justifyAction === "revert_na"
                ? "Reverter N/A"
                : "Cancelar item do checklist"
          }
          onClose={() => !busy && setJustifyAction(null)}
          closeAriaLabel="Fechar justificativa"
        >
          <div className="cf-validation-panel__form">
            <p className="cf-validation-panel__doc-detail">
              {justifyAction === "cancel"
                ? "Cancelamento é lógico e terminal — o item sai da lista ativa, mas histórico e evidências são preservados."
                : "A justificativa fica registrada em auditoria."}
            </p>
            <label>
              Justificativa
              <textarea
                value={justification}
                disabled={busy}
                rows={3}
                onChange={(e) => setJustification(e.target.value)}
              />
            </label>
            <div className="cf-validation-panel__form-actions">
              <ActionButton
                variant="primary"
                disabled={busy || !justification.trim()}
                onClick={submitJustification}
              >
                Confirmar
              </ActionButton>
              <ActionButton
                variant="ghost"
                disabled={busy}
                onClick={() => setJustifyAction(null)}
              >
                Voltar
              </ActionButton>
            </div>
          </div>
        </CfDialog>
      ) : null}

      {correctionOpen ? (
        <CfDialog
          open
          title="Solicitar correção estrutural"
          onClose={() => !busy && setCorrectionOpen(false)}
          closeAriaLabel="Fechar correção"
        >
          <div className="cf-validation-panel__form">
            <p className="cf-validation-panel__doc-detail">
              A correção entra em revisão (ACCESS solicita → MANAGE
              revisa). O item original permanece íntegro até a aprovação,
              que gera nova revisão.
            </p>
            <label>
              Campo a corrigir
              <select
                value={correctionField}
                disabled={busy}
                onChange={(e) => {
                  setCorrectionField(e.target.value);
                  setCorrectionValue("");
                }}
              >
                {CORRECTION_FIELDS.map((field) => (
                  <option key={field.value} value={field.value}>
                    {field.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Novo valor
              {fieldSpec?.options ? (
                <select
                  value={correctionValue}
                  disabled={busy}
                  onChange={(e) => setCorrectionValue(e.target.value)}
                >
                  <option value="">Selecione…</option>
                  {fieldSpec.options.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  value={correctionValue}
                  disabled={busy}
                  onChange={(e) => setCorrectionValue(e.target.value)}
                />
              )}
            </label>
            <label>
              Justificativa
              <textarea
                value={correctionJustification}
                disabled={busy}
                rows={3}
                onChange={(e) =>
                  setCorrectionJustification(e.target.value)
                }
              />
            </label>
            <div className="cf-validation-panel__form-actions">
              <ActionButton
                variant="primary"
                disabled={
                  busy ||
                  !correctionValue ||
                  !correctionJustification.trim()
                }
                onClick={submitCorrection}
              >
                Enviar correção
              </ActionButton>
              <ActionButton
                variant="ghost"
                disabled={busy}
                onClick={() => setCorrectionOpen(false)}
              >
                Voltar
              </ActionButton>
            </div>
          </div>
        </CfDialog>
      ) : null}

      {reviewTarget ? (
        <CfDialog
          open
          title="Revisar correção estrutural"
          onClose={() => !busy && setReviewTarget(null)}
          closeAriaLabel="Fechar revisão"
        >
          <div className="cf-validation-panel__form">
            <p>
              {Object.entries(reviewTarget.changes)
                .map(([field, value]) => `${field} → ${value}`)
                .join("; ")}
            </p>
            <p className="cf-validation-panel__doc-detail">
              {reviewTarget.justification}
            </p>
            <label>
              Motivo da rejeição (opcional)
              <textarea
                value={reviewReason}
                disabled={busy}
                rows={2}
                onChange={(e) => setReviewReason(e.target.value)}
              />
            </label>
            <div className="cf-validation-panel__form-actions">
              <ActionButton
                variant="primary"
                disabled={busy}
                onClick={() => submitReview(true)}
              >
                Aprovar
              </ActionButton>
              <ActionButton
                variant="ghost"
                disabled={busy}
                onClick={() => submitReview(false)}
              >
                Rejeitar correção
              </ActionButton>
              <ActionButton
                variant="ghost"
                disabled={busy}
                onClick={() => setReviewTarget(null)}
              >
                Voltar
              </ActionButton>
            </div>
          </div>
        </CfDialog>
      ) : null}
    </div>
  );
}

