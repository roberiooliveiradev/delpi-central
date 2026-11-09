/** Intercâmbio de informações analista ↔ solicitante — PRC-REF-019.
 *
 * Painel da visão geral do detalhe:
 *  - solicitante: responde (rascunho/envio) a rodada `awaiting_requester`;
 *  - analista: avalia respostas (`awaiting_review`) — aceita, pede
 *    complemento ou retoma o atendimento;
 *  - histórico de rodadas resolvidas recolhido.
 *
 * O papel exibido é só apresentação: a Engineering API decide
 * autorização (403/409 aparecem como feedback). `canReview`/`canResume`
 * derivam de `allowedActions` do backend. */

import { useCallback, useEffect, useState } from "react";

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
} from "../api/productRegistrationApi";
import {
  PRC_INFO_COPY,
  PRC_INFO_QUESTION_STATUS_LABELS,
  PRC_INFO_QUESTION_STATUS_VARIANTS,
  PRC_INFO_ROUND_STATUS_LABELS,
  prcPersonLabel,
} from "../prcCopy";
import {
  allInformationQuestionsAccepted,
  buildAnswerInputs,
  findActiveInformationRound,
  followUpInputFor,
  INFO_ANSWER_TEXT_MAX,
  INFO_QUESTION_TEXT_MAX,
  initialAnswerTexts,
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

/** Perguntas e respostas em leitura (histórico / visão sem ação). */
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
  const [texts, setTexts] = useState<Record<string, string>>(() =>
    initialAnswerTexts(round.questions),
  );
  const [errors, setErrors] = useState<Record<string, string>>({});

  const submit = () => {
    const check = validateInfoAnswersForSubmit(round.questions, texts);
    if (!check.valid) {
      setErrors(check.errors);
      return;
    }
    setErrors({});
    onSubmit(texts);
  };

  return (
    <div className="engineering-prc__info-answer-form">
      <p className="engineering-prc__muted">{PRC_INFO_COPY.requesterIntro}</p>
      {round.message ? (
        <p>
          <strong>{PRC_INFO_COPY.roundMessage}:</strong> {round.message}
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
                setTexts((s) => ({ ...s, [q.id]: value }));
                setErrors((e) => {
                  if (!e[q.id]) return e;
                  const next = { ...e };
                  delete next[q.id];
                  return next;
                });
              }}
              maxLength={INFO_ANSWER_TEXT_MAX}
              rows={3}
              required
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
      <div className="engineering-prc__actions">
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
          onClick={submit}
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
  onAccept: (question: PrcInformationQuestion) => void;
  onFollowUp: (question: PrcInformationQuestion, text: string) => void;
}) {
  const [followUpId, setFollowUpId] = useState<string | null>(null);
  const [followUpText, setFollowUpText] = useState("");
  const [followUpError, setFollowUpError] = useState("");

  const sendFollowUp = (question: PrcInformationQuestion) => {
    if (!followUpText.trim()) {
      setFollowUpError("Escreva a pergunta de complemento.");
      return;
    }
    setFollowUpError("");
    onFollowUp(question, followUpText);
    setFollowUpId(null);
    setFollowUpText("");
  };

  return (
    <div className="engineering-prc__info-review">
      <p className="engineering-prc__muted">{PRC_INFO_COPY.reviewIntro}</p>
      <ol className="engineering-prc__info-qa">
        {round.questions.map((q) => {
          const reviewable = q.status === "submitted";
          return (
            <li key={q.id} className="engineering-prc__info-qa-item">
              <div className="engineering-prc__info-qa-head">
                <strong>{questionTitle(q)}</strong>
                <QuestionStatus status={q.status} />
              </div>
              <p>{q.questionText}</p>
              <p>
                <strong>{PRC_INFO_COPY.answerLabel}:</strong>{" "}
                {q.answer?.text || PRC_INFO_COPY.noAnswerYet}
              </p>
              {reviewable ? (
                <div className="engineering-prc__actions">
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
                      setFollowUpId(followUpId === q.id ? null : q.id);
                      setFollowUpText("");
                      setFollowUpError("");
                    }}
                  >
                    {PRC_INFO_COPY.requestFollowUp}
                  </EngineeringActionButton>
                </div>
              ) : null}
              {followUpId === q.id ? (
                <div className="engineering-prc__info-followup">
                  <EngineeringTextAreaField
                    id={`prc-info-followup-${q.id}`}
                    label={PRC_INFO_COPY.followUpQuestion}
                    value={followUpText}
                    onChange={(value) => {
                      setFollowUpText(value);
                      setFollowUpError("");
                    }}
                    maxLength={INFO_QUESTION_TEXT_MAX}
                    rows={3}
                    required
                    disabled={disabled}
                  />
                  {followUpError ? (
                    <p className="engineering-prc__field-error" role="alert">
                      {followUpError}
                    </p>
                  ) : null}
                  <div className="engineering-prc__actions">
                    <EngineeringActionButton
                      variant="primary"
                      softDisabled={disabled}
                      onClick={() => sendFollowUp(q)}
                    >
                      {PRC_INFO_COPY.followUpSubmit}
                    </EngineeringActionButton>
                    <EngineeringActionButton
                      variant="ghost"
                      disabled={disabled}
                      onClick={() => {
                        setFollowUpId(null);
                        setFollowUpText("");
                        setFollowUpError("");
                      }}
                    >
                      {PRC_INFO_COPY.followUpCancel}
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
  canReview,
  canResume,
  refreshToken,
  busy,
  onChanged,
  onResume,
}: {
  requestId: string;
  requestStatus: string;
  /** `detail.requester.subject`. */
  requesterSubject: string;
  /** `sub` do access token — só para escolher a visão; nunca autorização. */
  currentSubject: string | null;
  /** Backend liberou ação de analista (`allowedActions` inclui resume). */
  canReview: boolean;
  canResume: boolean;
  /** Muda quando o caso é recarregado — dispara releitura das rodadas. */
  refreshToken?: string | number;
  busy: boolean;
  onChanged: () => void | Promise<void>;
  onResume: () => void;
}) {
  const [rounds, setRounds] = useState<PrcInformationRound[]>([]);
  const [hasOpenBlocker, setHasOpenBlocker] = useState(false);
  const [state, setState] = useState<"loading" | "ok" | "error">("loading");
  const [acting, setActing] = useState(false);
  const [feedback, setFeedback] = useState<Feedback>(null);

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
        setFeedback({
          kind: "error",
          text:
            err.status === 409
              ? `Conflito — ${err.message} Os esclarecimentos foram recarregados.`
              : err.message || "Falha na operação.",
        });
        if (err.status === 409) await reload();
      } finally {
        setActing(false);
      }
    },
    [reload, onChanged],
  );

  const active = findActiveInformationRound(rounds);
  const history = resolvedInformationRounds(rounds);
  const showPanel = rounds.length > 0 || requestStatus === "needs_information";
  if (!showPanel) return null;

  const disabled = busy || acting;
  const isRequesterView =
    !currentSubject ||
    !requesterSubject ||
    currentSubject === requesterSubject;
  const resumeReady =
    !hasOpenBlocker ||
    (active ? allInformationQuestionsAccepted(active.questions) : false);

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
  if (state === "loading" && !rounds.length) {
    body = (
      <p className="engineering-prc__muted">{PRC_INFO_COPY.panelLoading}</p>
    );
  } else if (state === "error" && !rounds.length) {
    body = (
      <EngineeringStateBanner variant="error">
        {PRC_INFO_COPY.panelLoadError}
      </EngineeringStateBanner>
    );
  } else if (!active) {
    body = (
      <p className="engineering-prc__muted">
        {rounds.length ? PRC_INFO_COPY.noActiveRound : PRC_INFO_COPY.panelEmpty}
      </p>
    );
  } else if (active.status === "awaiting_requester") {
    body = (
      <div className="engineering-prc__info-round">
        <RoundHeader round={active} />
        {isRequesterView && !canReview ? (
          <RequesterAnswerForm
            key={`${active.id}:${active.version}`}
            round={active}
            disabled={disabled}
            onDraft={(texts) => void saveDraft(active, texts)}
            onSubmit={(texts) => void submitAnswers(active, texts)}
          />
        ) : (
          <>
            <p className="engineering-prc__muted">
              {PRC_INFO_COPY.requesterWaitingOther}
            </p>
            <ReadOnlyQuestions round={active} />
          </>
        )}
      </div>
    );
  } else {
    body = (
      <div className="engineering-prc__info-round">
        <RoundHeader round={active} />
        {canReview ? (
          <AnalystReview
            key={`${active.id}:${active.version}`}
            round={active}
            disabled={disabled}
            onAccept={(q) => void accept(active, q)}
            onFollowUp={(q, text) => void followUp(active, q, text)}
          />
        ) : (
          <>
            <p className="engineering-prc__muted">
              {PRC_INFO_COPY.requesterWaitingReview}
            </p>
            <ReadOnlyQuestions round={active} />
          </>
        )}
      </div>
    );
  }

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

        {canResume && requestStatus === "needs_information" ? (
          <div className="engineering-prc__info-resume">
            {!resumeReady ? (
              <p className="engineering-prc__muted">
                {PRC_INFO_COPY.resumeBlocked}
              </p>
            ) : null}
            <EngineeringActionButton
              variant="primary"
              disabled={disabled || !resumeReady}
              onClick={onResume}
            >
              {PRC_INFO_COPY.resume}
            </EngineeringActionButton>
          </div>
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
