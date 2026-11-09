/** Intercâmbio de informações analista ↔ solicitante — PRC-REF-019.
 *
 * FIX-02: fluxo contínuo orientado pelo estado da rodada + capacidades
 * do backend. Sem alternância manual de papéis. Autorização efetiva
 * permanece na Engineering API. Retomada executável fica no cabeçalho. */

import { useCallback, useEffect, useMemo, useState } from "react";

import { HomeApiError } from "../../../api/httpClient";
import {
  EngineeringActionButton,
  EngineeringDetailCard,
  EngineeringStateBanner,
  EngineeringStatusBadge,
  EngineeringTextAreaField,
} from "../../../ui/engineeringUi";
import {
  acceptInformationQuestion,
  draftInformationAnswers,
  listInformationRounds,
  newPrcIdempotencyKey,
  requestInformationFollowUp,
  submitInformationAnswers,
  type PrcInformationQuestion,
  type PrcInformationRound,
  type PrcRequestDetail,
} from "../api/productRegistrationApi";
import {
  PRC_INFO_COPY,
  PRC_INFO_QUESTION_STATUS_LABELS,
  PRC_INFO_QUESTION_STATUS_VARIANTS,
  PRC_INFO_ROUND_STATUS_LABELS,
  prcPersonLabel,
} from "../prcCopy";
import {
  buildAnswerInputs,
  findActiveInformationRound,
  followUpInputFor,
  INFO_ANSWER_TEXT_MAX,
  INFO_QUESTION_TEXT_MAX,
  informationRoundConflictMessage,
  initialAnswerTexts,
  isRequesterSubject,
  resolveInfoPresentation,
  resolvedInformationRounds,
  validateInfoAnswersForSubmit,
} from "../prcInformationExchange";

type Feedback = { kind: "success" | "error"; text: string } | null;

function questionTitle(question: PrcInformationQuestion): string {
  return question.targetLabel || PRC_INFO_COPY.questionText;
}

function QuestionStatus({ status }: { status: string }) {
  return (
    <EngineeringStatusBadge
      label={PRC_INFO_QUESTION_STATUS_LABELS[status] || status}
      variant={PRC_INFO_QUESTION_STATUS_VARIANTS[status] || "neutral"}
    />
  );
}

function RoundHeader({ round }: { round: PrcInformationRound }) {
  return (
    <div className="engineering-prc__info-round-head">
      <strong>
        {`${PRC_INFO_COPY.roundLabel} ${round.sequence ?? ""}`.trim()}
      </strong>
      <EngineeringStatusBadge
        label={PRC_INFO_ROUND_STATUS_LABELS[round.status] || round.status}
        variant={round.status === "resolved" ? "success" : "warning"}
      />
      {round.requestedBy?.subject || round.requestedBy?.displayName ? (
        <span className="engineering-prc__muted">
          {`${PRC_INFO_COPY.requestedBy} ${prcPersonLabel(
            round.requestedBy?.subject,
            round.requestedBy?.displayName,
          )}`}
        </span>
      ) : null}
    </div>
  );
}

function ReadOnlyQuestions({ round }: { round: PrcInformationRound }) {
  return (
    <ol className="engineering-prc__info-qa">
      {round.questions.map((q) => (
        <li key={q.id} className="engineering-prc__info-qa-item">
          <div className="engineering-prc__info-qa-head">
            <strong>{questionTitle(q)}</strong>
            <QuestionStatus status={q.status} />
          </div>
          <p>{q.questionText}</p>
          <p className="engineering-prc__muted">
            {q.answer?.text
              ? `${PRC_INFO_COPY.answerLabel}: ${q.answer.text}`
              : PRC_INFO_COPY.noAnswerYet}
          </p>
        </li>
      ))}
    </ol>
  );
}

function RequesterAnswerForm({
  round,
  disabled,
  onDraft,
  onSubmit,
}: {
  round: PrcInformationRound;
  disabled: boolean;
  onDraft: (texts: Record<string, string>) => void;
  onSubmit: (texts: Record<string, string>) => void;
}) {
  const [texts, setTexts] = useState(() => initialAnswerTexts(round.questions));
  const [errors, setErrors] = useState<Record<string, string>>({});

  return (
    <div className="engineering-prc__info-answer-form">
      <p className="engineering-prc__muted">{PRC_INFO_COPY.requesterIntro}</p>
      {round.message ? (
        <p>
          <strong>{PRC_INFO_COPY.roundMessage}: </strong>
          {round.message}
        </p>
      ) : null}
      <ol className="engineering-prc__info-qa">
        {round.questions.map((q) => (
          <li key={q.id} className="engineering-prc__info-qa-item">
            <div className="engineering-prc__info-qa-head">
              <strong>{questionTitle(q)}</strong>
              <QuestionStatus status={q.status} />
            </div>
            <p>{q.questionText}</p>
            <EngineeringTextAreaField
              id={`prc-info-answer-${q.id}`}
              label={PRC_INFO_COPY.yourAnswer}
              value={texts[q.id] ?? ""}
              onChange={(value) => {
                setTexts((prev) => ({ ...prev, [q.id]: value }));
                setErrors((prev) => {
                  if (!prev[q.id]) return prev;
                  const next = { ...prev };
                  delete next[q.id];
                  return next;
                });
              }}
              maxLength={INFO_ANSWER_TEXT_MAX}
              rows={4}
              disabled={disabled}
            />
            {errors[q.id] ? (
              <p className="engineering-prc__field-error" role="alert">
                {errors[q.id]}
              </p>
            ) : null}
          </li>
        ))}
      </ol>
      <div className="engineering-prc__info-answer-actions">
        <EngineeringActionButton
          variant="ghost"
          softDisabled={disabled}
          onClick={() => onDraft(texts)}
        >
          {PRC_INFO_COPY.saveDraft}
        </EngineeringActionButton>
        <EngineeringActionButton
          variant="primary"
          softDisabled={disabled}
          onClick={() => {
            const result = validateInfoAnswersForSubmit(round.questions, texts);
            if (!result.valid) {
              setErrors(result.errors);
              return;
            }
            onSubmit(texts);
          }}
        >
          {PRC_INFO_COPY.submitAnswers}
        </EngineeringActionButton>
      </div>
    </div>
  );
}

function AnalystReview({
  round,
  disabled,
  onAccept,
  onFollowUp,
}: {
  round: PrcInformationRound;
  disabled: boolean;
  onAccept: (q: PrcInformationQuestion) => void;
  onFollowUp: (q: PrcInformationQuestion, text: string) => void;
}) {
  const [followUpFor, setFollowUpFor] = useState<string | null>(null);
  const [followUpText, setFollowUpText] = useState("");

  return (
    <div className="engineering-prc__info-review">
      <p className="engineering-prc__muted">{PRC_INFO_COPY.reviewIntro}</p>
      <ol className="engineering-prc__info-qa">
        {round.questions.map((q) => {
          const open = followUpFor === q.id;
          const submitted = q.status === "submitted";
          return (
            <li key={q.id} className="engineering-prc__info-qa-item">
              <div className="engineering-prc__info-qa-head">
                <strong>{questionTitle(q)}</strong>
                <QuestionStatus status={q.status} />
              </div>
              <p>{q.questionText}</p>
              <p className="engineering-prc__muted">
                {q.answer?.text
                  ? `${PRC_INFO_COPY.answerLabel}: ${q.answer.text}`
                  : PRC_INFO_COPY.noAnswerYet}
              </p>
              {submitted ? (
                <div className="engineering-prc__info-review-actions">
                  <EngineeringActionButton
                    variant="primary"
                    softDisabled={disabled}
                    onClick={() => onAccept(q)}
                  >
                    {PRC_INFO_COPY.acceptQuestion}
                  </EngineeringActionButton>
                  <EngineeringActionButton
                    variant="ghost"
                    softDisabled={disabled}
                    onClick={() => {
                      setFollowUpFor(q.id);
                      setFollowUpText("");
                    }}
                  >
                    {PRC_INFO_COPY.requestFollowUp}
                  </EngineeringActionButton>
                </div>
              ) : null}
              {open ? (
                <div className="engineering-prc__info-followup">
                  <EngineeringTextAreaField
                    id={`prc-info-followup-${q.id}`}
                    label={PRC_INFO_COPY.followUpQuestion}
                    value={followUpText}
                    onChange={setFollowUpText}
                    maxLength={INFO_QUESTION_TEXT_MAX}
                    rows={3}
                    required
                    disabled={disabled}
                  />
                  <div className="engineering-prc__info-review-actions">
                    <EngineeringActionButton
                      variant="ghost"
                      disabled={disabled}
                      onClick={() => setFollowUpFor(null)}
                    >
                      {PRC_INFO_COPY.followUpCancel}
                    </EngineeringActionButton>
                    <EngineeringActionButton
                      variant="primary"
                      softDisabled={disabled || !followUpText.trim()}
                      onClick={() => {
                        if (!followUpText.trim()) return;
                        onFollowUp(q, followUpText.trim());
                        setFollowUpFor(null);
                      }}
                    >
                      {PRC_INFO_COPY.followUpSubmit}
                    </EngineeringActionButton>
                  </div>
                </div>
              ) : null}
            </li>
          );
        })}
      </ol>
    </div>
  );
}

export function PrcInformationExchangePanel({
  requestId,
  requestStatus,
  requesterSubject,
  currentSubject,
  informationExchange,
  allowedActions,
  refreshToken,
  busy,
  onChanged,
}: {
  requestId: string;
  requestStatus: string;
  requesterSubject: string;
  currentSubject: string | null;
  informationExchange?: PrcRequestDetail["informationExchange"];
  allowedActions: string[];
  refreshToken?: string | number;
  busy: boolean;
  onChanged: () => void | Promise<void>;
}) {
  const [rounds, setRounds] = useState<PrcInformationRound[]>([]);
  const [hasOpenBlocker, setHasOpenBlocker] = useState(
    Boolean(informationExchange?.hasOpenBlocker),
  );
  const [state, setState] = useState<"loading" | "ok" | "error">("loading");
  const [acting, setActing] = useState(false);
  const [feedback, setFeedback] = useState<Feedback>(null);

  const isRequester = isRequesterSubject(currentSubject, requesterSubject);
  const canReviewFromApi = Boolean(informationExchange?.canReview);
  const canReview =
    canReviewFromApi ||
    allowedActions.includes("resume") ||
    allowedActions.includes("reject") ||
    allowedActions.includes("request_information");
  const canResume =
    allowedActions.includes("resume") &&
    requestStatus === "needs_information" &&
    !hasOpenBlocker;

  const reload = useCallback(async () => {
    try {
      const res = await listInformationRounds(requestId);
      setRounds(res.data.items);
      setHasOpenBlocker(Boolean(res.data.hasOpenBlocker));
      setState("ok");
    } catch {
      setState("error");
    }
  }, [requestId]);

  useEffect(() => {
    void reload();
  }, [reload, refreshToken]);

  useEffect(() => {
    if (informationExchange?.hasOpenBlocker != null) {
      setHasOpenBlocker(Boolean(informationExchange.hasOpenBlocker));
    }
  }, [informationExchange?.hasOpenBlocker]);

  const active = findActiveInformationRound(rounds);
  const history = resolvedInformationRounds(rounds);

  const canRespond = useMemo(() => {
    if (informationExchange?.canRespond != null) {
      return Boolean(informationExchange.canRespond);
    }
    return (
      isRequester &&
      Boolean(active) &&
      active?.status === "awaiting_requester"
    );
  }, [informationExchange?.canRespond, isRequester, active]);

  const presentation = resolveInfoPresentation({
    loadState: state,
    hasRounds: rounds.length > 0,
    activeStatus: active?.status ?? null,
    canRespond,
    canReview,
    canResume,
  });

  const run = useCallback(
    async (
      operation: () => Promise<unknown>,
      successText: string,
      notifyParent: boolean,
    ) => {
      setActing(true);
      setFeedback(null);
      try {
        await operation();
        setFeedback({ kind: "success", text: successText });
        await reload();
        if (notifyParent) await onChanged();
      } catch (e) {
        const err = e as HomeApiError;
        const conflictText = informationRoundConflictMessage(
          err.message,
          PRC_INFO_COPY.resumeConflict,
        );
        setFeedback({
          kind: "error",
          text:
            err.status === 409
              ? conflictText
              : err.message || "Falha na operação.",
        });
        if (err.status === 409) {
          await reload();
          if (notifyParent) await onChanged();
        }
      } finally {
        setActing(false);
      }
    },
    [reload, onChanged],
  );

  const showPanel = rounds.length > 0 || requestStatus === "needs_information";
  if (!showPanel) return null;

  const disabled = busy || acting;

  const saveDraft = (round: PrcInformationRound, texts: Record<string, string>) =>
    run(
      () =>
        draftInformationAnswers(
          requestId,
          round.id,
          {
            expectedRoundVersion: round.version,
            answers: buildAnswerInputs(round.questions, texts),
          },
          newPrcIdempotencyKey(`prc-info-draft-${round.id}`),
        ),
      PRC_INFO_COPY.draftSaved,
      false,
    );

  const submitAnswers = (
    round: PrcInformationRound,
    texts: Record<string, string>,
  ) =>
    run(
      () =>
        submitInformationAnswers(
          requestId,
          round.id,
          {
            expectedRoundVersion: round.version,
            answers: buildAnswerInputs(round.questions, texts),
          },
          newPrcIdempotencyKey(`prc-info-submit-${round.id}`),
        ),
      PRC_INFO_COPY.answersSubmitted,
      true,
    );

  const accept = (round: PrcInformationRound, q: PrcInformationQuestion) =>
    run(
      () =>
        acceptInformationQuestion(
          requestId,
          round.id,
          q.id,
          { expectedRoundVersion: round.version },
          newPrcIdempotencyKey(`prc-info-accept-${q.id}`),
        ),
      PRC_INFO_COPY.questionAccepted,
      true,
    );

  const followUp = (
    round: PrcInformationRound,
    q: PrcInformationQuestion,
    text: string,
  ) =>
    run(
      () =>
        requestInformationFollowUp(
          requestId,
          round.id,
          {
            expectedRoundVersion: round.version,
            questions: [followUpInputFor(q, text)],
            followUpQuestionIds: [q.id],
          },
          newPrcIdempotencyKey(`prc-info-followup-${q.id}`),
        ),
      PRC_INFO_COPY.followUpSent,
      true,
    );

  let body;
  switch (presentation) {
    case "loading":
      body = (
        <p className="engineering-prc__muted">{PRC_INFO_COPY.panelLoading}</p>
      );
      break;
    case "error":
      body = (
        <EngineeringStateBanner variant="error">
          {PRC_INFO_COPY.panelLoadError}
        </EngineeringStateBanner>
      );
      break;
    case "empty":
      body = (
        <p className="engineering-prc__muted">{PRC_INFO_COPY.panelEmpty}</p>
      );
      break;
    case "awaiting_requester_form":
      body = active ? (
        <div className="engineering-prc__info-round">
          <RoundHeader round={active} />
          <RequesterAnswerForm
            key={`${active.id}:${active.version}`}
            round={active}
            disabled={disabled}
            onDraft={(texts) => void saveDraft(active, texts)}
            onSubmit={(texts) => void submitAnswers(active, texts)}
          />
        </div>
      ) : null;
      break;
    case "awaiting_requester_watch":
      body = active ? (
        <div className="engineering-prc__info-round">
          <RoundHeader round={active} />
          <p className="engineering-prc__muted">
            {PRC_INFO_COPY.requesterWaitingOther}
          </p>
          <ReadOnlyQuestions round={active} />
        </div>
      ) : null;
      break;
    case "awaiting_review_analyst":
      body = active ? (
        <div className="engineering-prc__info-round">
          <RoundHeader round={active} />
          <AnalystReview
            key={`${active.id}:${active.version}`}
            round={active}
            disabled={disabled}
            onAccept={(q) => void accept(active, q)}
            onFollowUp={(q, text) => void followUp(active, q, text)}
          />
        </div>
      ) : null;
      break;
    case "awaiting_review_watch":
      body = active ? (
        <div className="engineering-prc__info-round">
          <RoundHeader round={active} />
          <p className="engineering-prc__muted">
            {PRC_INFO_COPY.requesterWaitingReview}
          </p>
          <ReadOnlyQuestions round={active} />
        </div>
      ) : null;
      break;
    case "resolved_ready":
      body = (
        <div className="engineering-prc__info-round">
          <p className="engineering-prc__muted">
            {PRC_INFO_COPY.resolvedReady}
          </p>
          <p className="engineering-prc__muted">
            {PRC_INFO_COPY.resumeReadyHint}
          </p>
        </div>
      );
      break;
    case "resolved_done":
    default:
      body = (
        <p className="engineering-prc__muted">
          {rounds.length
            ? PRC_INFO_COPY.resolvedSummary
            : PRC_INFO_COPY.panelEmpty}
        </p>
      );
      break;
  }

  const statusHint =
    presentation === "awaiting_requester_form" ||
    presentation === "awaiting_requester_watch"
      ? hasOpenBlocker
        ? PRC_INFO_COPY.resumeBlocked
        : null
      : presentation === "awaiting_review_analyst" ||
          presentation === "awaiting_review_watch"
        ? PRC_INFO_COPY.resumeBlockedReview
        : null;

  return (
    <EngineeringDetailCard
      title={PRC_INFO_COPY.panelTitle}
      headerActions={
        <EngineeringActionButton
          variant="ghost"
          softDisabled={disabled}
          onClick={() => void reload()}
        >
          {PRC_INFO_COPY.refresh}
        </EngineeringActionButton>
      }
    >
      <div className="engineering-prc__info-panel">
        {feedback ? (
          <EngineeringStateBanner
            variant={feedback.kind === "error" ? "error" : "success"}
          >
            {feedback.text}
          </EngineeringStateBanner>
        ) : null}

        {body}

        {statusHint && requestStatus === "needs_information" ? (
          <p className="engineering-prc__muted">{statusHint}</p>
        ) : null}

        {history.length ? (
          <details className="engineering-prc__info-history">
            <summary>{`${PRC_INFO_COPY.history} (${history.length})`}</summary>
            {history.map((round) => (
              <div key={round.id} className="engineering-prc__info-round">
                <RoundHeader round={round} />
                <ReadOnlyQuestions round={round} />
              </div>
            ))}
          </details>
        ) : null}
      </div>
    </EngineeringDetailCard>
  );
}
