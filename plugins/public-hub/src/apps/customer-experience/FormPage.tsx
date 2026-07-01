import { useState } from "react";
import {
  submitFormResponse,
  type FormAnswerPayload,
  type PublicForm,
  type PublicQuestion,
} from "./api";
import "./form.css";

type Phase = "form" | "submitting" | "done";

type AnswerState = Record<string, { rating?: number; text?: string; choices?: string[] }>;

export function FormView({ form }: { form: PublicForm }) {
  const [name, setName] = useState("");
  const [company, setCompany] = useState("");
  const [answers, setAnswers] = useState<AnswerState>({});
  const [phase, setPhase] = useState<Phase>("form");
  const [error, setError] = useState<string | null>(null);

  function patch(id: string, value: AnswerState[string]) {
    setAnswers((prev) => ({ ...prev, [id]: { ...prev[id], ...value } }));
  }

  function validate(): string | null {
    if (!name.trim()) return "Informe seu nome.";
    for (const q of form.questions) {
      if (!q.required) continue;
      const a = answers[q.id];
      const empty =
        !a ||
        (q.type === "rating" && !a.rating) ||
        (q.type === "multi_choice" && (!a.choices || a.choices.length === 0)) ||
        (q.type !== "rating" && q.type !== "multi_choice" && !a.text?.trim());
      if (empty) return `Responda: ${q.label}`;
    }
    return null;
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    const problem = validate();
    if (problem) {
      setError(problem);
      return;
    }
    setError(null);
    setPhase("submitting");

    const payloadAnswers: FormAnswerPayload[] = form.questions
      .map((q): FormAnswerPayload | null => {
        const a = answers[q.id];
        if (!a) return null;
        if (q.type === "rating") return a.rating ? { questionId: q.id, rating: a.rating } : null;
        if (q.type === "multi_choice")
          return a.choices && a.choices.length ? { questionId: q.id, choices: a.choices } : null;
        return a.text?.trim() ? { questionId: q.id, text: a.text.trim() } : null;
      })
      .filter((x): x is FormAnswerPayload => x !== null);

    const result = await submitFormResponse(form.token, {
      respondentName: name.trim(),
      respondentCompany: company.trim() || null,
      answers: payloadAnswers,
    });

    if (result.ok) {
      setPhase("done");
      return;
    }
    setError(result.message);
    setPhase("form");
  }

  if (phase === "done") {
    const firstName = name.trim().split(/\s+/)[0];
    return (
      <div className="cxform cxform--message">
        <div className="cxform-check" aria-hidden="true">✓</div>
        <h1 className="cxform-title">Obrigado{firstName ? `, ${firstName}` : ""}!</h1>
        <p className="cxform-subtitle">
          Suas respostas chegaram até a nossa equipe. É com elas que melhoramos a experiência de quem visita a DELPI.
        </p>
        <div className="cxform-signature">
          <span className="cxform-signature__line" />
          Equipe DELPI
        </div>
      </div>
    );
  }

  return (
    <div className="cxform">
      <span className="cxform-eyebrow">Programa Experiência do Cliente · DELPI</span>
      <h1 className="cxform-title">{form.title}</h1>
      {form.description && <p className="cxform-subtitle">{form.description}</p>}

      <form className="cxform-card" onSubmit={handleSubmit}>
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

        {form.questions.map((q) => (
          <QuestionField
            key={q.id}
            question={q}
            answer={answers[q.id]}
            onChange={(value) => patch(q.id, value)}
          />
        ))}

        {error && <p className="cxform-error">{error}</p>}

        <button type="submit" className="cxform-submit" disabled={phase === "submitting"}>
          {phase === "submitting" ? "Enviando..." : "Enviar respostas"}
        </button>
      </form>
    </div>
  );
}

function QuestionField({
  question,
  answer,
  onChange,
}: {
  question: PublicQuestion;
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

  // multi_choice
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
