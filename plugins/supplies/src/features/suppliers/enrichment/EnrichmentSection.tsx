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
  decideEnrichmentBulk,
  decideEnrichmentField,
  getEnrichmentReview,
  listEnrichmentReviews,
  prepareEnrichmentUpdate,
} from "./api";
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

type FailedAction = {
  key: string;
  run: (idempotencyKey: string) => Promise<void>;
};

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
  const [failedAction, setFailedAction] = useState<FailedAction | null>(null);
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
    loadHistory(1, controller.signal).then((items) => {
      const candidate = pickActiveReview(items);
      if (candidate) openReview(candidate.review_id, controller.signal);
    });
    return () => controller.abort();
  }, [loadHistory, openReview]);

  /** Falha recuperável: guarda ação + chave idempotente para retry igual. */
  const fail = (err: unknown, action?: FailedAction) => {
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
    if (
      action &&
      (!(err instanceof ApiRequestError) ||
        err.status >= 500 ||
        err.status === 429)
    ) {
      setFailedAction(action);
    } else {
      setFailedAction(null);
    }
  };

  const applyPayload = (payload: ActiveReview & { idempotent_replay?: boolean }) => {
    setActive({ review: payload.review, proposals: payload.proposals });
    setSelected(new Set());
    setFailedAction(null);
    if (payload.idempotent_replay) {
      setNotice({ variant: "default", text: C.replayNotice });
    } else {
      setNotice(null);
    }
  };

  const runConsult = () => {
    setCreating(true);
    setNotice(null);
    createEnrichmentReview(code, store)
      .then((payload) => {
        setActive(payload);
        setDraft(null);
        void loadHistory(1);
      })
      .catch((err: unknown) => fail(err))
      .finally(() => setCreating(false));
  };

  const runDecision = (
    fieldKey: string,
    decision: "ACCEPT" | "REJECT",
    key: string,
  ) => {
    const review = active?.review;
    if (!review) return Promise.resolve();
    const action: FailedAction = {
      key,
      run: (k) => runDecision(fieldKey, decision, k),
    };
    setBusy(true);
    return decideEnrichmentField(code, store, review.review_id, {
      field_key: fieldKey,
      decision,
      expected_revision: review.revision,
      idempotency_key: key,
    })
      .then(applyPayload)
      .catch((err: unknown) => fail(err, action))
      .finally(() => setBusy(false));
  };

  const onDecide = (fieldKey: string, decision: "ACCEPT" | "REJECT") => {
    void runDecision(fieldKey, decision, newIdempotencyKey());
  };

  const runBulk = (decision: "ACCEPT" | "REJECT", key: string) => {
    const review = active?.review;
    const fieldKeys = [...selected];
    if (!review || !fieldKeys.length) return Promise.resolve();
    const action: FailedAction = {
      key,
      run: (k) => runBulk(decision, k),
    };
    setBusy(true);
    setBulkConfirm(null);
    return decideEnrichmentBulk(code, store, review.review_id, {
      field_keys: fieldKeys,
      decision,
      expected_revision: review.revision,
      idempotency_key: key,
    })
      .then(applyPayload)
      .catch((err: unknown) => fail(err, action))
      .finally(() => setBusy(false));
  };

  const runPrepare = (key: string) => {
    const review = active?.review;
    if (!review) return Promise.resolve();
    const action: FailedAction = { key, run: runPrepare };
    setBusy(true);
    return prepareEnrichmentUpdate(code, store, review.review_id, review.revision)
      .then((result) => {
        setDraft(result);
        setFailedAction(null);
        setNotice({
          variant: "success",
          text: result.draft_fields.length ? C.draftReady : C.draftEmpty,
        });
      })
      .catch((err: unknown) => fail(err, action))
      .finally(() => setBusy(false));
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
            {failedAction ? (
              <SuppliesActionButton
                type="button"
                variant="ghost"
                disabled={busy || creating}
                onClick={() => void failedAction.run(failedAction.key)}
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
                  onClick={() => void runPrepare(newIdempotencyKey())}
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
                if (bulkConfirm) void runBulk(bulkConfirm, newIdempotencyKey());
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
