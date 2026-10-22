import { useCallback, useEffect, useRef, useState } from "react";

import { ApiRequestError } from "../../../api/httpClient";
import {
  SuppliesActionButton,
  SuppliesEmptyState,
  SuppliesLoadingCard,
  SuppliesModal,
  SuppliesSectionCard,
  SuppliesStateBanner,
} from "../../../app/suppliesUi";
import { SP_HELP } from "../../../content/helpTooltips";
import {
  createEnrichmentReview,
  getEnrichmentReview,
  listEnrichmentReviews,
} from "./api";
import {
  captureBulkDecision,
  capturePrepareOperation,
  captureSingleDecision,
  executeDecisionOperation,
  executePrepareOperation,
  isRecoverableForRetry,
  type RetryableOperation,
} from "./decisionOperations";
import { EnrichmentComparisonTable } from "./EnrichmentComparisonTable";
import { EnrichmentHistoryTable } from "./EnrichmentHistoryTable";
import {
  ENRICHMENT_CONTENT as C,
  mapEnrichmentError,
} from "./content";
import {
  bulkAcceptAllowed,
  isReviewActionable,
  newIdempotencyKey,
  pickActiveReview,
  summarizeProposals,
} from "./stateMachine";
import type {
  EnrichmentPrepareUpdateResult,
  EnrichmentReview,
  EnrichmentProposal,
} from "./types";

const HISTORY_PAGE_SIZE = 10;

type Notice = { variant: "default" | "error" | "success"; text: string };

type ActiveReview = { review: EnrichmentReview; proposals: EnrichmentProposal[] };

type EnrichmentSectionProps = {
  code: string;
  store: string;
};

export function EnrichmentSection({ code, store }: EnrichmentSectionProps) {
  const [history, setHistory] = useState<{
    items: EnrichmentReview[];
    total: number;
    page: number;
    loading: boolean;
    failed: boolean;
  }>({ items: [], total: 0, page: 1, loading: true, failed: false });
  const [active, setActive] = useState<ActiveReview | null>(null);
  const [activeLoading, setActiveLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [bulkConfirm, setBulkConfirm] = useState<"ACCEPT" | "REJECT" | null>(
    null,
  );
  const [draft, setDraft] = useState<EnrichmentPrepareUpdateResult | null>(null);
  const [failedOp, setFailedOp] = useState<RetryableOperation | null>(null);
  const sectionRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (
      typeof window !== "undefined" &&
      window.location.hash === "#enrichment"
    ) {
      sectionRef.current?.scrollIntoView({ block: "start" });
    }
  }, []);

  const loadHistory = useCallback(
    (page: number, signal?: AbortSignal) => {
      setHistory((h) => ({ ...h, loading: true }));
      return listEnrichmentReviews(code, store, page, HISTORY_PAGE_SIZE, signal)
        .then((envelope) => {
          setHistory({
            items: envelope.items ?? [],
            total: envelope.total ?? 0,
            page: envelope.page ?? page,
            loading: false,
            failed: false,
          });
          return envelope.items ?? [];
        })
        .catch(() => {
          setHistory((h) => ({ ...h, loading: false, failed: true }));
          return [] as EnrichmentReview[];
        });
    },
    [code, store],
  );

  const openReview = useCallback(
    (reviewId: string, signal?: AbortSignal) => {
      setActiveLoading(true);
      return getEnrichmentReview(code, store, reviewId, signal)
        .then((payload) => {
          setActive(payload);
          setDraft(null);
          setSelected(new Set());
          // Operação pendente pertence a outra revisão: descarte explícito —
          // nunca aplicar silenciosamente uma operação antiga fora de contexto.
          setFailedOp(null);
        })
        .catch((err: unknown) => {
          setNotice({
            variant: "error",
            text:
              err instanceof ApiRequestError
                ? mapEnrichmentError(err.status, err.code)
                : C.errorGeneric,
          });
        })
        .finally(() => setActiveLoading(false));
    },
    [code, store],
  );

  useEffect(() => {
    const controller = new AbortController();
    // Troca de fornecedor: a operação pendente pertence a outro contexto —
    // descarte explícito, nunca retry silencioso de operação antiga.
    setFailedOp(null);
    loadHistory(1, controller.signal).then((items) => {
      const candidate = pickActiveReview(items);
      if (candidate) openReview(candidate.review_id, controller.signal);
    });
    return () => controller.abort();
  }, [loadHistory, openReview]);

  /** Falha recuperável: guarda a operação capturada para retry idêntico. */
  const fail = (err: unknown, op?: RetryableOperation) => {
    if (err instanceof ApiRequestError) {
      setNotice({
        variant: "error",
        text: mapEnrichmentError(err.status, err.code),
      });
      if (
        err.code === "ENRICHMENT_REVISION_CONFLICT" ||
        err.status === 410 ||
        err.code === "ENRICHMENT_PROPOSAL_ALREADY_DECIDED"
      ) {
        if (active) void openReview(active.review.review_id);
      }
    } else {
      setNotice({ variant: "error", text: C.errorGeneric });
    }
    setFailedOp(op && isRecoverableForRetry(err) ? op : null);
  };

  const applyPayload = (payload: ActiveReview & { idempotent_replay?: boolean }) => {
    setActive({ review: payload.review, proposals: payload.proposals });
    setSelected(new Set());
    setFailedOp(null);
    if (payload.idempotent_replay) {
      setNotice({ variant: "default", text: C.replayNotice });
    } else {
      setNotice(null);
    }
  };

  /** Executa a operação capturada — retry é literalmente a mesma requisição. */
  const runOperation = (op: RetryableOperation): Promise<void> => {
    setBusy(true);
    if (op.kind === "prepare") {
      return executePrepareOperation(op)
        .then((result) => {
          setDraft(result);
          setFailedOp(null);
          setNotice({
            variant: "success",
            text: result.draft_fields.length ? C.draftReady : C.draftEmpty,
          });
        })
        .catch((err: unknown) => fail(err, op))
        .finally(() => setBusy(false));
    }
    return executeDecisionOperation(op)
      .then(applyPayload)
      .catch((err: unknown) => fail(err, op))
      .finally(() => setBusy(false));
  };

  const runConsult = () => {
    setCreating(true);
    setNotice(null);
    createEnrichmentReview(code, store)
      .then((payload) => {
        setActive(payload);
        setDraft(null);
        setFailedOp(null);
        void loadHistory(1);
      })
      .catch((err: unknown) => fail(err))
      .finally(() => setCreating(false));
  };

  /** Nova intenção: captura estado atual e gera chave idempotente nova. */
  const onDecide = (fieldKey: string, decision: "ACCEPT" | "REJECT") => {
    const review = active?.review;
    if (!review) return;
    void runOperation(
      captureSingleDecision(
        code,
        store,
        review.review_id,
        fieldKey,
        decision,
        review.revision,
        newIdempotencyKey(),
      ),
    );
  };

  const onConfirmBulk = (decision: "ACCEPT" | "REJECT") => {
    const review = active?.review;
    const fieldKeys = [...selected];
    if (!review || !fieldKeys.length) return;
    setBulkConfirm(null);
    void runOperation(
      captureBulkDecision(
        code,
        store,
        review.review_id,
        fieldKeys,
        decision,
        review.revision,
        newIdempotencyKey(),
      ),
    );
  };

  const onPrepare = () => {
    const review = active?.review;
    if (!review) return;
    void runOperation(
      capturePrepareOperation(code, store, review.review_id, review.revision),
    );
  };

  const toggleSelected = (fieldKey: string) => {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(fieldKey)) next.delete(fieldKey);
      else next.add(fieldKey);
      return next;
    });
  };

  const proposals = active?.proposals ?? [];
  const summary = summarizeProposals(proposals);
  const actionable = active ? isReviewActionable(active.review) : false;
  const bulkAcceptOk =
    active && bulkAcceptAllowed(proposals, selected) ? true : false;

  return (
    <section
      id="enrichment"
      ref={sectionRef}
      className="sp-enrichment"
      aria-label={C.sectionTitle}
    >
      <SuppliesSectionCard title={C.sectionTitle} hint={SP_HELP.suppliersEnrichment}>
        {notice ? (
          <SuppliesStateBanner variant={notice.variant}>
            {notice.text}{" "}
            {failedOp ? (
              <SuppliesActionButton
                type="button"
                variant="ghost"
                disabled={busy || creating}
                onClick={() => void runOperation(failedOp)}
              >
                {C.retryAction}
              </SuppliesActionButton>
            ) : null}
          </SuppliesStateBanner>
        ) : null}

        <p className="sp-enrichment__source-note">{C.sourceNote}</p>

        {!active && !activeLoading ? (
          <SuppliesEmptyState title={C.emptyTitle} message={C.emptyMessage} />
        ) : null}

        {activeLoading ? (
          <SuppliesLoadingCard title={C.historyLoading} variant="panel" />
        ) : null}

        <div className="sp-enrichment__actions">
          <SuppliesActionButton
            type="button"
            variant="primary"
            onClick={runConsult}
            disabled={creating || busy}
          >
            {creating
              ? C.consultLoading
              : active
                ? C.newConsultAction
                : C.consultAction}
          </SuppliesActionButton>
        </div>

        {active ? (
          <>
            <p className="sp-enrichment__meta">
              {C.summary(summary.different, summary.match, summary.other)}
              {" · "}
              {C.acceptedSummary(
                summary.accepted,
                summary.rejected,
                summary.pending,
              )}
              {" · "}
              {`${active.review.source_id} · ${active.review.source_retrieved_at ?? ""}`}
            </p>

            <EnrichmentComparisonTable
              proposals={proposals}
              busy={busy}
              actionable={actionable}
              selected={selected}
              onToggleSelected={toggleSelected}
              onDecide={onDecide}
            />

            {actionable && selected.size > 0 ? (
              <div className="sp-enrichment__bulk" aria-label={C.bulkBarLabel}>
                <SuppliesActionButton
                  type="button"
                  variant="primary"
                  disabled={busy || !bulkAcceptOk}
                  title={bulkAcceptOk ? undefined : C.bulkAcceptBlocked}
                  onClick={() => setBulkConfirm("ACCEPT")}
                >
                  {`${C.bulkAccept} (${selected.size})`}
                </SuppliesActionButton>
                <SuppliesActionButton
                  type="button"
                  variant="ghost"
                  disabled={busy}
                  onClick={() => setBulkConfirm("REJECT")}
                >
                  {`${C.bulkReject} (${selected.size})`}
                </SuppliesActionButton>
              </div>
            ) : null}

            {actionable ? (
              <div className="sp-enrichment__actions">
                <SuppliesActionButton
                  type="button"
                  variant="ghost"
                  disabled={busy}
                  title={C.prepareHint}
                  onClick={onPrepare}
                >
                  {C.prepareAction}
                </SuppliesActionButton>
              </div>
            ) : null}

            {draft ? (
              <div className="sp-enrichment__draft">
                <SuppliesSectionCard
                  title={C.draftTitle}
                  hint={C.prepareHint}
                >
                  <p className="sp-enrichment__meta">
                    {C.draftBaseline(draft.baseline_status)}
                  </p>
                  {draft.draft_fields.length ? (
                    <table className="sp-enrichment__draft-table">
                      <thead>
                        <tr>
                          <th>{C.columnField}</th>
                          <th>{C.draftColumnCurrent}</th>
                          <th>{C.draftColumnProposed}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {draft.draft_fields.map((item) => (
                          <tr key={item.proposal_id}>
                            <td>{item.field_key}</td>
                            <td>{item.current_value ?? C.currentNotProvided}</td>
                            <td>{item.proposed_value ?? "—"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : null}
                </SuppliesSectionCard>
              </div>
            ) : null}
          </>
        ) : null}

        {history.failed ? (
          <SuppliesStateBanner variant="default">
            {C.historyPartial}
          </SuppliesStateBanner>
        ) : null}

        <SuppliesSectionCard title={C.historyTitle} hint={C.historyHint}>
          <EnrichmentHistoryTable
            items={history.items}
            total={history.total}
            page={history.page}
            pageSize={HISTORY_PAGE_SIZE}
            loading={history.loading}
            activeReviewId={active?.review.review_id}
            onPageChange={(page) => void loadHistory(page)}
            onOpenReview={(id) => void openReview(id)}
          />
        </SuppliesSectionCard>
      </SuppliesSectionCard>

      <SuppliesModal
        open={bulkConfirm !== null}
        title={C.bulkConfirmTitle}
        onClose={() => setBulkConfirm(null)}
        footer={
          <>
            <SuppliesActionButton
              type="button"
              variant="primary"
              disabled={busy}
              onClick={() => {
                if (bulkConfirm) onConfirmBulk(bulkConfirm);
              }}
            >
              {C.bulkConfirmAction}
            </SuppliesActionButton>
            <SuppliesActionButton
              type="button"
              variant="ghost"
              disabled={busy}
              onClick={() => setBulkConfirm(null)}
            >
              {C.bulkCancelAction}
            </SuppliesActionButton>
          </>
        }
      >
        <p>
          {bulkConfirm === "ACCEPT"
            ? C.bulkConfirmAccept(selected.size)
            : C.bulkConfirmReject(selected.size)}
        </p>
      </SuppliesModal>
    </section>
  );
}
