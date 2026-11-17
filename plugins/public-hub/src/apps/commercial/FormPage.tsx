import { useEffect, useMemo, useRef, useState } from "react";
import type { FormEvent } from "react";
import {
  submitPublicSurvey,
  type PublicSurveyState,
  type SurveyQuestionItem,
  type SurveyQuestionnaire,
} from "./api.ts";
import { SurveyStateView, type SurveyTerminalStatus } from "./SurveyStateView";
import {
  NOT_APPLICABLE,
  OPEN_TEXT_MAX_LENGTH,
  REQUIRED_ASSESSMENTS,
  buildSteps,
  buildSubmitPayload,
  countCompleted,
  createEmptyAnswers,
  describeAnswer,
  firstIncompleteStep,
  formatSurveyWindow,
  hasUnsentAnswers,
  pendingKeys,
  progressPercent,
  type SurveyAnswers,
  type SurveyStep,
} from "./surveyForm.ts";
import "./form.css";

type OpenSurvey = Extract<PublicSurveyState, { status: "open" }>;

type Phase =
  | { kind: "intro" }
  | { kind: "step"; index: number; fromReview: boolean }
  | { kind: "review" }
  | { kind: "done" }
  | { kind: "terminal"; status: SurveyTerminalStatus };

const RECOMMENDATION_VALUES = Array.from({ length: 11 }, (_, value) => value);

function fieldId(key: string): string {
  return `satform-q-${key}`;
}

export function SurveyFormView({ survey }: { survey: OpenSurvey }) {
  const { questionnaire } = survey;
  const steps = useMemo(() => buildSteps(questionnaire), [questionnaire]);
  const [phase, setPhase] = useState<Phase>({ kind: "intro" });
  const [answers, setAnswers] = useState<SurveyAnswers>(createEmptyAnswers);
  const [flagged, setFlagged] = useState<ReadonlySet<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const submittingRef = useRef(false);
  const headingRef = useRef<HTMLHeadingElement | null>(null);

  const completed = countCompleted(questionnaire, answers);
  const percent = progressPercent(completed);
  const unsent = hasUnsentAnswers(answers);
  const warnOnLeave = unsent && phase.kind !== "done" && phase.kind !== "terminal";

  // Aviso nativo de saída: só enquanto houver respostas não enviadas. Sem rascunho persistente.
  useEffect(() => {
    if (!warnOnLeave) return;
    const handler = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [warnOnLeave]);

  // Move o foco ao título ao trocar de tela (teclado/leitor de tela).
  const phaseKey =
    phase.kind === "step" ? `step-${phase.index}` : phase.kind === "terminal" ? `t-${phase.status}` : phase.kind;
  useEffect(() => {
    if (phaseKey !== "intro") headingRef.current?.focus();
  }, [phaseKey]);

  function setDimension(key: string, value: number | typeof NOT_APPLICABLE) {
    setAnswers((prev) => ({ ...prev, dimensions: { ...prev.dimensions, [key]: value } }));
    unflag(key);
  }

  function unflag(key: string) {
    setFlagged((prev) => {
      if (!prev.has(key)) return prev;
      const next = new Set(prev);
      next.delete(key);
      return next;
    });
  }

  function focusFirst(keys: string[]) {
    window.requestAnimationFrame(() => {
      document.getElementById(fieldId(keys[0] ?? ""))?.focus();
    });
  }

  function validateStep(step: SurveyStep): boolean {
    const pending = pendingKeys(step, answers);
    if (pending.length === 0) {
      setError(null);
      setFlagged(new Set());
      return true;
    }
    setFlagged(new Set(pending));
    setError(
      pending.length === 1
        ? "Falta 1 avaliação obrigatória nesta etapa."
        : `Faltam ${pending.length} avaliações obrigatórias nesta etapa.`,
    );
    focusFirst(pending);
    return false;
  }

  function goToStep(index: number, fromReview = false) {
    setError(null);
    setFlagged(new Set());
    setPhase({ kind: "step", index, fromReview });
  }

  function handleNext(step: SurveyStep, fromReview: boolean) {
    if (!validateStep(step)) return;
    if (fromReview) {
      setPhase({ kind: "review" });
      return;
    }
    if (step.index < 3) {
      goToStep(step.index + 1);
      return;
    }
    setPhase({ kind: "review" });
  }

  async function confirmSubmit() {
    if (submittingRef.current) return;
    const payload = buildSubmitPayload(questionnaire, answers);
    if (!payload) {
      setError("Há avaliações obrigatórias sem resposta. Corrija antes de enviar.");
      return;
    }
    submittingRef.current = true;
    setSubmitting(true);
    setError(null);
    try {
      const result = await submitPublicSurvey(survey.token, payload);
      if (result.outcome === "submitted") {
        // Sucesso só com confirmação do servidor; a tela final não mostra nenhuma resposta.
        setAnswers(createEmptyAnswers());
        setPhase({ kind: "done" });
        return;
      }
      if (
        result.outcome === "already_submitted" ||
        result.outcome === "not_open" ||
        result.outcome === "closed" ||
        result.outcome === "invalid"
      ) {
        setPhase({ kind: "terminal", status: result.outcome });
        return;
      }
      setError(result.message);
    } finally {
      submittingRef.current = false;
      setSubmitting(false);
    }
  }

  if (phase.kind === "terminal") {
    return (
      <SurveyStateView
        status={phase.status}
        campaignName={survey.campaignName}
        startsAt={survey.startsAt}
        endsAt={survey.endsAt}
      />
    );
  }

  if (phase.kind === "done") {
    return (
      <div className="satform satform--message" role="status">
        <div className="satform-check" aria-hidden="true">
          ✓
        </div>
        <h1 className="satform-title" tabIndex={-1} ref={headingRef}>
          Obrigado por participar!
        </h1>
        <p className="satform-subtitle">
          Sua avaliação foi registrada. Ela contribui para melhorar os produtos, os serviços e o
          relacionamento da DELPI com você. A resposta não poderá ser alterada.
        </p>
      </div>
    );
  }

  const currentStep = phase.kind === "step" ? steps[phase.index - 1] : null;
  const period = formatSurveyWindow(survey.startsAt, survey.endsAt);

  return (
    <div className="satform">
      <header className="satform-header">
        <span className="satform-eyebrow">Pesquisa de Satisfação do Cliente · DELPI</span>
        {phase.kind === "intro" ? (
          <h1 className="satform-title">{survey.campaignName || "Pesquisa de Satisfação do Cliente"}</h1>
        ) : (
          <h1 className="satform-title" tabIndex={-1} ref={headingRef}>
            {phase.kind === "review"
              ? "Revisar respostas"
              : `Etapa ${currentStep?.index} de 3 — ${currentStep?.title}`}
          </h1>
        )}
        {phase.kind !== "intro" ? (
          <div className="satform-progress">
            <div
              className="satform-progress__track"
              role="progressbar"
              aria-label="Progresso das avaliações obrigatórias"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={percent}
              aria-valuetext={`${completed} de ${REQUIRED_ASSESSMENTS} avaliações concluídas`}
            >
              <div className="satform-progress__fill" style={{ width: `${percent}%` }} />
            </div>
            <span className="satform-progress__label">
              {percent}% · {completed} de {REQUIRED_ASSESSMENTS} avaliações concluídas
            </span>
          </div>
        ) : null}
      </header>

      {phase.kind === "intro" ? (
        <section className="satform-card">
          <p className="satform-subtitle">Sua avaliação ajuda a melhorar nossos produtos e serviços.</p>
          {survey.companyName ? (
            <p className="satform-help">Pesquisa destinada à empresa: {survey.companyName}</p>
          ) : null}
          {period ? <p className="satform-help">Prazo da pesquisa: {period}</p> : null}
          <p className="satform-help">
            São 15 perguntas em 3 etapas, com revisão antes do envio. Não pedimos dados pessoais do
            respondente.
          </p>
          <div className="satform-nav">
            <button type="button" className="satform-btn satform-btn--primary" onClick={() => goToStep(1)}>
              Iniciar pesquisa
            </button>
          </div>
        </section>
      ) : null}

      {phase.kind === "step" && currentStep ? (
        <form
          className="satform-card"
          noValidate
          onSubmit={(event: FormEvent) => {
            // Enter nunca envia: o POST só ocorre em «Confirmar e enviar».
            event.preventDefault();
            handleNext(currentStep, phase.fromReview);
          }}
        >
          <StepFields
            step={currentStep}
            questionnaire={questionnaire}
            answers={answers}
            flagged={flagged}
            onDimension={setDimension}
            onOverall={(value) => {
              setAnswers((prev) => ({ ...prev, overall: value }));
              unflag("overall_score");
            }}
            onRecommendation={(value) => {
              setAnswers((prev) => ({ ...prev, recommendation: value }));
              unflag("recommendation_score");
            }}
            onText={(key, value) => setAnswers((prev) => ({ ...prev, [key]: value }))}
          />
          {error ? (
            <p className="satform-error" role="alert">
              {error}
            </p>
          ) : null}
          <div className="satform-nav">
            {phase.fromReview ? (
              <button type="button" className="satform-btn satform-btn--ghost" onClick={() => setPhase({ kind: "review" })}>
                Voltar à revisão sem alterar
              </button>
            ) : currentStep.index > 1 ? (
              <button
                type="button"
                className="satform-btn satform-btn--ghost"
                onClick={() => goToStep(currentStep.index - 1)}
              >
                Anterior
              </button>
            ) : null}
            <button type="submit" className="satform-btn satform-btn--primary">
              {phase.fromReview ? "Voltar à revisão" : currentStep.index === 3 ? "Revisar respostas" : "Próxima"}
            </button>
          </div>
        </form>
      ) : null}

      {phase.kind === "review" ? (
        <ReviewCard
          steps={steps}
          questionnaire={questionnaire}
          answers={answers}
          error={error}
          submitting={submitting}
          onEdit={(index) => goToStep(index, true)}
          onFixIncomplete={() => {
            const step = firstIncompleteStep(steps, answers);
            if (step) goToStep(step.index, true);
          }}
          onConfirm={() => void confirmSubmit()}
        />
      ) : null}
    </div>
  );
}

type StepFieldsProps = {
  step: SurveyStep;
  questionnaire: SurveyQuestionnaire;
  answers: SurveyAnswers;
  flagged: ReadonlySet<string>;
  onDimension: (key: string, value: number | typeof NOT_APPLICABLE) => void;
  onOverall: (value: number) => void;
  onRecommendation: (value: number) => void;
  onText: (key: "strengths" | "improvements" | "unmet_needs", value: string) => void;
};

function StepFields({
  step,
  questionnaire,
  answers,
  flagged,
  onDimension,
  onOverall,
  onRecommendation,
  onText,
}: StepFieldsProps) {
  return (
    <>
      {step.items.map((item) => {
        if (item.kind === "dimension") {
          return (
            <ScaleQuestion
              key={item.key}
              item={item}
              scaleLabels={questionnaire.scaleLabels}
              value={answers.dimensions[item.key]}
              invalid={flagged.has(item.key)}
              onSelect={(value) => onDimension(item.key, value)}
            />
          );
        }
        if (item.kind === "overall") {
          return (
            <ScaleQuestion
              key={item.key}
              item={{ ...item, allowsNotApplicable: false }}
              scaleLabels={questionnaire.scaleLabels}
              value={answers.overall}
              invalid={flagged.has(item.key)}
              onSelect={(value) => onOverall(value as number)}
            />
          );
        }
        if (item.kind === "recommendation") {
          return (
            <RecommendationQuestion
              key={item.key}
              item={item}
              value={answers.recommendation}
              invalid={flagged.has(item.key)}
              onSelect={onRecommendation}
            />
          );
        }
        const textKey = item.key as "strengths" | "improvements" | "unmet_needs";
        return (
          <label key={item.key} className="satform-field">
            <span className="satform-label">
              {item.prompt} <em className="satform-opt-tag">(opcional)</em>
            </span>
            <textarea
              className="satform-textarea"
              rows={3}
              maxLength={OPEN_TEXT_MAX_LENGTH}
              value={answers[textKey]}
              onChange={(event) => onText(textKey, event.target.value)}
            />
          </label>
        );
      })}
    </>
  );
}

type ScaleQuestionProps = {
  item: SurveyQuestionItem;
  scaleLabels: Record<number, string>;
  value: number | typeof NOT_APPLICABLE | undefined;
  invalid: boolean;
  onSelect: (value: number | typeof NOT_APPLICABLE) => void;
};

function ScaleQuestion({ item, scaleLabels, value, invalid, onSelect }: ScaleQuestionProps) {
  const scale = [1, 2, 3, 4, 5];
  return (
    <fieldset
      id={fieldId(item.key)}
      tabIndex={-1}
      className={`satform-field${invalid ? " is-invalid" : ""}`}
      aria-invalid={invalid || undefined}
      aria-describedby={invalid ? `${fieldId(item.key)}-error` : undefined}
    >
      <legend className="satform-label">
        {item.prompt} <em className="satform-req">*</em>
      </legend>
      <div className="satform-scale">
        {scale.map((option) => (
          <label key={option} className={`satform-opt${value === option ? " is-on" : ""}`}>
            <input
              type="radio"
              name={item.key}
              value={option}
              checked={value === option}
              aria-label={`${option} — ${scaleLabels[option] ?? ""}`}
              onChange={() => onSelect(option)}
            />
            <span className="satform-opt__num" aria-hidden="true">
              {option}
            </span>
            <span className="satform-opt__text" aria-hidden="true">
              {scaleLabels[option] ?? ""}
            </span>
          </label>
        ))}
        {item.allowsNotApplicable ? (
          <label className={`satform-opt satform-opt--na${value === NOT_APPLICABLE ? " is-on" : ""}`}>
            <input
              type="radio"
              name={item.key}
              value={NOT_APPLICABLE}
              checked={value === NOT_APPLICABLE}
              onChange={() => onSelect(NOT_APPLICABLE)}
            />
            <span className="satform-opt__text">Não se aplica</span>
          </label>
        ) : null}
      </div>
      {invalid ? (
        <p id={`${fieldId(item.key)}-error`} className="satform-error">
          Selecione uma nota{item.allowsNotApplicable ? " ou “Não se aplica”" : ""}.
        </p>
      ) : null}
    </fieldset>
  );
}

function RecommendationQuestion({
  item,
  value,
  invalid,
  onSelect,
}: {
  item: SurveyQuestionItem;
  value: number | undefined;
  invalid: boolean;
  onSelect: (value: number) => void;
}) {
  return (
    <fieldset
      id={fieldId(item.key)}
      tabIndex={-1}
      className={`satform-field${invalid ? " is-invalid" : ""}`}
      aria-invalid={invalid || undefined}
      aria-describedby={invalid ? `${fieldId(item.key)}-error` : undefined}
    >
      <legend className="satform-label">
        {item.prompt} <em className="satform-req">*</em>
      </legend>
      <div className="satform-nps">
        {RECOMMENDATION_VALUES.map((option) => (
          <label key={option} className={`satform-opt satform-opt--nps${value === option ? " is-on" : ""}`}>
            <input
              type="radio"
              name={item.key}
              value={option}
              checked={value === option}
              aria-label={`${option}`}
              onChange={() => onSelect(option)}
            />
            <span className="satform-opt__num" aria-hidden="true">
              {option}
            </span>
          </label>
        ))}
      </div>
      {invalid ? (
        <p id={`${fieldId(item.key)}-error`} className="satform-error">
          Selecione um valor de 0 a 10.
        </p>
      ) : null}
    </fieldset>
  );
}

type ReviewCardProps = {
  steps: SurveyStep[];
  questionnaire: SurveyQuestionnaire;
  answers: SurveyAnswers;
  error: string | null;
  submitting: boolean;
  onEdit: (index: number) => void;
  onFixIncomplete: () => void;
  onConfirm: () => void;
};

function ReviewCard({
  steps,
  questionnaire,
  answers,
  error,
  submitting,
  onEdit,
  onFixIncomplete,
  onConfirm,
}: ReviewCardProps) {
  const incomplete = firstIncompleteStep(steps, answers);
  return (
    <section className="satform-card" aria-label="Revisão das respostas">
      {steps.map((step) => (
        <div key={step.index} className="satform-review-section">
          <div className="satform-review-head">
            <h2 className="satform-page-title">
              Etapa {step.index}: {step.title}
            </h2>
            <button
              type="button"
              className="satform-btn satform-btn--ghost"
              aria-label={`Editar etapa ${step.index}: ${step.title}`}
              disabled={submitting}
              onClick={() => onEdit(step.index)}
            >
              Editar
            </button>
          </div>
          <dl className="satform-review-list">
            {step.items.map((item) => (
              <div key={item.key} className="satform-review-item">
                <dt>{item.prompt}</dt>
                <dd>{describeAnswer(item, answers, questionnaire.scaleLabels)}</dd>
              </div>
            ))}
          </dl>
        </div>
      ))}
      <p className="satform-help">
        Após confirmar, esta resposta <strong>não poderá ser editada</strong>.
      </p>
      {incomplete ? (
        <p className="satform-error" role="alert">
          Há avaliações obrigatórias sem resposta.{" "}
          <button type="button" className="satform-link" onClick={onFixIncomplete}>
            Corrigir agora
          </button>
        </p>
      ) : null}
      {error ? (
        <p className="satform-error" role="alert">
          {error}
        </p>
      ) : null}
      <div className="satform-nav">
        <button
          type="button"
          className="satform-btn satform-btn--primary"
          disabled={submitting || incomplete !== null}
          onClick={onConfirm}
        >
          {submitting ? "Enviando..." : "Confirmar e enviar"}
        </button>
      </div>
    </section>
  );
}
