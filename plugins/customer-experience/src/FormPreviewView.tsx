import { useMemo, useState } from "react";
import type { PreviewForm, PreviewFormPage, PreviewFormQuestion } from "./utils/formPreviewModel";
import type { BackgroundFit } from "./types";
import "./form-preview.css";

function resolveBackgroundFit(value: string | null | undefined): BackgroundFit {
  if (value === "fixed" || value === "tile" || value === "scale") return value;
  return "scale";
}

type Phase = "form" | "submitting" | "done";

type AnswerState = Record<string, { rating?: number; text?: string; choices?: string[] }>;

type WizardStep =
  | { kind: "intro" }
  | { kind: "question"; question: PreviewFormQuestion; page?: PreviewFormPage | null };

type FormPreviewViewProps = {
  form: PreviewForm;
};

function buildSteps(form: PreviewForm): WizardStep[] {
  if (!form.oneQuestionPerPage) {
    return [{ kind: "intro" }];
  }
  const pageById = new Map(form.pages.map((p) => [p.id, p]));
  return [
    { kind: "intro" },
    ...form.questions.map((question) => ({
      kind: "question" as const,
      question,
      page: question.pageId ? pageById.get(question.pageId) ?? null : null,
    })),
  ];
}

function isAnswered(question: PreviewFormQuestion, answer: AnswerState[string] | undefined): boolean {
  if (!answer) return false;
  if (question.type === "rating") return Boolean(answer.rating);
  if (question.type === "multi_choice") return Boolean(answer.choices?.length);
  return Boolean(answer.text?.trim());
}

function computeProgress(
  form: PreviewForm,
  stepIndex: number,
  answers: AnswerState,
  name: string,
): number {
  if (!form.oneQuestionPerPage) {
    const units = 1 + form.questions.filter((q) => q.required).length;
    let done = name.trim() ? 1 : 0;
    for (const q of form.questions) {
      if (q.required && isAnswered(q, answers[q.id])) done += 1;
    }
    return Math.round((done / Math.max(units, 1)) * 100);
  }
  const steps = buildSteps(form);
  const completed = steps.slice(0, stepIndex + 1).filter((step) => {
    if (step.kind === "intro") return Boolean(name.trim());
    return !step.question.required || isAnswered(step.question, answers[step.question.id]);
  }).length;
  return Math.round((completed / steps.length) * 100);
}

function resolveBackground(
  form: PreviewForm,
  step: WizardStep | null,
): string | null {
  if (step?.kind === "question") {
    return step.page?.backgroundImageUrl ?? form.backgroundImageUrl ?? null;
  }
  return form.backgroundImageUrl ?? null;
}

function resolvePointImage(step: WizardStep | null, question?: PreviewFormQuestion): string | null {
  if (step?.kind === "question") {
    return (
      step.page?.pointImageUrl ??
      step.question.pointImageUrl ??
      null
    );
  }
  return question?.pointImageUrl ?? null;
}

export default function FormPreviewView({ form }: FormPreviewViewProps) {
  const pages = form.pages ?? [];
  const wizard = form.oneQuestionPerPage;
  const steps = useMemo(
    () => buildSteps({ ...form, pages }),
    [form, pages, wizard],
  );
  const [stepIndex, setStepIndex] = useState(0);
  const [name, setName] = useState("");
  const [company, setCompany] = useState("");
  const [answers, setAnswers] = useState<AnswerState>({});
  const [phase, setPhase] = useState<Phase>("form");
  const [error, setError] = useState<string | null>(null);

  const currentStep = wizard ? steps[stepIndex] : null;
  const progress = computeProgress(form, stepIndex, answers, name);
  const backgroundUrl = resolveBackground(form, currentStep);
  const backgroundFit = resolveBackgroundFit(form.backgroundFit);

  const pageById = useMemo(
    () => new Map(pages.map((p) => [p.id, p])),
    [pages],
  );

  function patch(id: string, value: AnswerState[string]) {
    setAnswers((prev) => ({ ...prev, [id]: { ...prev[id], ...value } }));
  }

  function validateAll(): string | null {
    if (!name.trim()) return "Informe seu nome.";
    for (const q of form.questions) {
      if (!q.required) continue;
      if (!isAnswered(q, answers[q.id])) return `Responda: ${q.label}`;
    }
    return null;
  }

  function validateStep(): string | null {
    if (!wizard) return validateAll();
    const step = steps[stepIndex];
    if (step.kind === "intro") {
      return name.trim() ? null : "Informe seu nome.";
    }
    const q = step.question;
    if (q.required && !isAnswered(q, answers[q.id])) {
      return `Responda: ${q.label}`;
    }
    return null;
  }

  function finalizePreview() {
    const problem = validateAll();
    if (problem) {
      setError(problem);
      return;
    }
    setError(null);
    setPhase("done");
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    // Enter em campos de texto dispara submit nativo do <form>; no wizard isso
    // não pode enviar antes da última etapa (perguntas opcionais seriam puladas).
    if (wizard && stepIndex < steps.length - 1) {
      goNext();
      return;
    }
    finalizePreview();
  }

  function goNext() {
    const problem = validateStep();
    if (problem) {
      setError(problem);
      return;
    }
    setError(null);
    setStepIndex((prev) => Math.min(prev + 1, steps.length - 1));
  }

  function goPrev() {
    setError(null);
    setStepIndex((prev) => Math.max(prev - 1, 0));
  }

  if (phase === "done") {
    const firstName = name.trim().split(/\s+/)[0];
    return (
      <div className="cxform cxform--fullpage cxform--message">
        <div className="cxform-check" aria-hidden="true">✓</div>
        <h1 className="cxform-title">Obrigado{firstName ? `, ${firstName}` : ""}!</h1>
        <p className="cxform-subtitle">
          Prévia: nenhuma resposta foi enviada. É com elas que melhoramos a experiência de quem visita a DELPI.
        </p>
        <div className="cxform-signature">
          <span className="cxform-signature__line" />
          Equipe DELPI
        </div>
      </div>
    );
  }

  const viewportPhotoStyle = backgroundUrl
    ? ({ backgroundImage: `url(${backgroundUrl})` } as React.CSSProperties)
    : undefined;

  const renderIntroFields = () => (
    <>
      <label className="cxform-field">
        <span className="cxform-label">
          Seu nome <em className="cxform-req">*</em>
        </span>
        <input
          className="cxform-input"
          value={name}
          maxLength={200}
          placeholder="Como podemos te chamar?"
          onChange={(e) => setName(e.target.value)}
        />
      </label>
      <label className="cxform-field">
        <span className="cxform-label">Empresa</span>
        <input
          className="cxform-input"
          value={company}
          maxLength={200}
          placeholder="Onde você trabalha? (opcional)"
          onChange={(e) => setCompany(e.target.value)}
        />
      </label>
    </>
  );

  const renderScrollForm = () => {
    let lastPageId: string | null = null;
    return (
      <>
        {renderIntroFields()}
        {form.questions.map((q) => {
          const page = q.pageId ? pageById.get(q.pageId) : null;
          const showPageHeader = page && page.id !== lastPageId;
          if (page?.id) lastPageId = page.id;
          return (
            <div key={q.id}>
              {showPageHeader && page && (
                <div
                  className={`cxform-page-header${page.backgroundImageUrl ? " cxform-page-header--photo" : ""}`}
                  style={
                    page.backgroundImageUrl
                      ? ({
                          ["--cxform-page-photo" as string]: `url(${page.backgroundImageUrl})`,
                        } as React.CSSProperties)
                      : undefined
                  }
                >
                  {page.pointImageUrl && (
                    <figure className="cxform-illustration cxform-illustration--section" aria-hidden="true">
                      <img className="cxform-illustration__img" src={page.pointImageUrl} alt="" />
                    </figure>
                  )}
                  {page.title && <h2 className="cxform-page-title">{page.title}</h2>}
                </div>
              )}
              {!showPageHeader && q.pointImageUrl && (
                <figure className="cxform-illustration cxform-illustration--inline" aria-hidden="true">
                  <img className="cxform-illustration__img" src={q.pointImageUrl} alt="" />
                </figure>
              )}
              <QuestionField
                question={q}
                answer={answers[q.id]}
                onChange={(value) => patch(q.id, value)}
              />
            </div>
          );
        })}
      </>
    );
  };

  const renderWizardStep = () => {
    const step = steps[stepIndex];
    if (step.kind === "intro") {
      return renderIntroFields();
    }
    const pointImage = resolvePointImage(step);
    const pageTitle = step.page?.title?.trim();
    const showPageTitle = Boolean(pageTitle && pageTitle !== step.question.label.trim());
    return (
      <div className="cxform-step">
        {pointImage && (
          <figure className="cxform-illustration" aria-hidden="true">
            <img className="cxform-illustration__img" src={pointImage} alt="" />
          </figure>
        )}
        {showPageTitle && <h2 className="cxform-page-title">{pageTitle}</h2>}
        <QuestionField
          question={step.question}
          answer={answers[step.question.id]}
          onChange={(value) => patch(step.question.id, value)}
        />
      </div>
    );
  };

  const isLastWizardStep = wizard && stepIndex === steps.length - 1;

  return (
    <>
      {backgroundUrl && (
        <div className="cxform-viewport-bg" aria-hidden="true">
          <div
            className={`cxform-viewport-bg__photo cxform-viewport-bg__photo--${backgroundFit}`}
            style={viewportPhotoStyle}
          />
          <div className="cxform-viewport-bg__scrim" />
        </div>
      )}
      <div
        className={`cxform cxform--fullpage${wizard ? " cxform--wizard" : ""}`}
      >
      <header className="cxform-header">
        <span className="cxform-eyebrow">Programa Experiência do Cliente · DELPI</span>
        <h1 className="cxform-title">{form.title}</h1>
        {form.description && stepIndex === 0 && (
          <p className="cxform-subtitle">{form.description}</p>
        )}

        {(wizard || form.questions.length > 0) && (
          <div className="cxform-progress" aria-label={`Progresso: ${progress}%`}>
            <div className="cxform-progress__track">
              <div className="cxform-progress__fill" style={{ width: `${progress}%` }} />
            </div>
            <span className="cxform-progress__label">{progress}%</span>
          </div>
        )}
      </header>

      <form className="cxform-card" onSubmit={handleSubmit}>
        {wizard ? renderWizardStep() : renderScrollForm()}

        {error && <p className="cxform-error">{error}</p>}

        {wizard ? (
          <div className="cxform-nav">
            {stepIndex > 0 && (
              <button type="button" className="cxform-nav__btn cxform-nav__btn--ghost" onClick={goPrev}>
                Voltar
              </button>
            )}
            {!isLastWizardStep ? (
              <button type="button" className="cxform-nav__btn cxform-nav__btn--primary" onClick={goNext}>
                Próxima
              </button>
            ) : (
              // type="button" evita o clique de "Próxima" reativar submit quando o
              // botão é trocado no mesmo lugar ao chegar na última etapa.
              <button
                type="button"
                className="cxform-nav__btn cxform-nav__btn--primary"
                onClick={finalizePreview}
              >
                Concluir prévia
              </button>
            )}
          </div>
        ) : (
          <button type="submit" className="cxform-submit">
            Concluir prévia
          </button>
        )}
      </form>
      </div>
    </>
  );
}

function QuestionField({
  question,
  answer,
  onChange,
}: {
  question: PreviewFormQuestion;
  answer: AnswerState[string] | undefined;
  onChange: (value: AnswerState[string]) => void;
}) {
  const label = (
    <span className="cxform-label">
      {question.label} {question.required && <em className="cxform-req">*</em>}
    </span>
  );

  if (question.type === "rating") {
    const current = answer?.rating ?? 0;
    return (
      <fieldset className="cxform-field">
        <legend className="cxform-label">
          {question.label} {question.required && <em className="cxform-req">*</em>}
        </legend>
        {question.helpText && <span className="cxform-help">{question.helpText}</span>}
        <div className="cxform-stars" role="radiogroup" aria-label={question.label}>
          {[1, 2, 3, 4, 5].map((value) => (
            <button
              key={value}
              type="button"
              role="radio"
              aria-checked={current === value}
              aria-label={`${value}`}
              className={`cxform-star${value <= current ? " is-on" : ""}`}
              onClick={() => onChange({ rating: value })}
            >
              ★
            </button>
          ))}
        </div>
      </fieldset>
    );
  }

  if (question.type === "long_text") {
    return (
      <label className="cxform-field">
        {label}
        {question.helpText && <span className="cxform-help">{question.helpText}</span>}
        <textarea
          className="cxform-textarea"
          rows={3}
          maxLength={2000}
          value={answer?.text ?? ""}
          onChange={(e) => onChange({ text: e.target.value })}
        />
      </label>
    );
  }

  if (question.type === "short_text") {
    return (
      <label className="cxform-field">
        {label}
        {question.helpText && <span className="cxform-help">{question.helpText}</span>}
        <input
          className="cxform-input"
          maxLength={2000}
          value={answer?.text ?? ""}
          onChange={(e) => onChange({ text: e.target.value })}
        />
      </label>
    );
  }

  if (question.type === "yes_no" || question.type === "single_choice") {
    const options = question.type === "yes_no" ? ["Sim", "Não"] : question.options;
    return (
      <fieldset className="cxform-field">
        <legend className="cxform-label">
          {question.label} {question.required && <em className="cxform-req">*</em>}
        </legend>
        {question.helpText && <span className="cxform-help">{question.helpText}</span>}
        <div className="cxform-options">
          {options.map((opt) => (
            <label key={opt} className={`cxform-option${answer?.text === opt ? " is-on" : ""}`}>
              <input
                type="radio"
                name={question.id}
                checked={answer?.text === opt}
                onChange={() => onChange({ text: opt })}
              />
              {opt}
            </label>
          ))}
        </div>
      </fieldset>
    );
  }

  const selected = answer?.choices ?? [];
  const toggle = (opt: string) => {
    const next = selected.includes(opt)
      ? selected.filter((o) => o !== opt)
      : [...selected, opt];
    onChange({ choices: next });
  };
  return (
    <fieldset className="cxform-field">
      <legend className="cxform-label">
        {question.label} {question.required && <em className="cxform-req">*</em>}
      </legend>
      {question.helpText && <span className="cxform-help">{question.helpText}</span>}
      <div className="cxform-options">
        {question.options.map((opt) => (
          <label key={opt} className={`cxform-option${selected.includes(opt) ? " is-on" : ""}`}>
            <input type="checkbox" checked={selected.includes(opt)} onChange={() => toggle(opt)} />
            {opt}
          </label>
        ))}
      </div>
    </fieldset>
  );
}
