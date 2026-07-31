import { useMemo, useState, type CSSProperties, type FormEvent } from "react";

import {
  submitPublicSipatResponse,
  type PublicSipatQuestion,
  type PublicSipatSurvey,
  type SipatAnswerPayload,
} from "./api";
import "./sipat-form.css";

type Phase = "form" | "submitting" | "done";
type AnswerMap = Record<string, { value?: string; choices?: string[] }>;

function isAnswered(question: PublicSipatQuestion, answer: AnswerMap[string] | undefined): boolean {
  if (!answer) return false;
  if (question.type === "multi_choice") {
    return Boolean(answer.choices?.length);
  }
  return Boolean(answer.value?.trim());
}

type Props = {
  survey: PublicSipatSurvey;
  token: string;
};

export function SipatFormPage({ survey, token }: Props) {
  const [answers, setAnswers] = useState<AnswerMap>({});
  const [phase, setPhase] = useState<Phase>("form");
  const [error, setError] = useState<string | null>(null);

  const questions = useMemo(
    () => [...survey.questions].sort((a, b) => (a.position ?? 0) - (b.position ?? 0)),
    [survey.questions],
  );

  const answeredRequired = questions.filter(
    (q) => !q.required || isAnswered(q, answers[q.id]),
  ).length;
  const fillPercent = Math.round((answeredRequired / Math.max(questions.length, 1)) * 100);

  const setValue = (questionId: string, value: string) => {
    setAnswers((prev) => ({ ...prev, [questionId]: { ...prev[questionId], value } }));
  };

  const toggleChoice = (questionId: string, option: string) => {
    setAnswers((prev) => {
      const current = prev[questionId]?.choices || [];
      const next = current.includes(option)
        ? current.filter((item) => item !== option)
        : [...current, option];
      return { ...prev, [questionId]: { ...prev[questionId], choices: next } };
    });
  };

  const buildPayload = (): SipatAnswerPayload[] =>
    questions.map((question) => {
      const answer = answers[question.id];
      if (question.type === "multi_choice") {
        return { question_id: question.id, choices: answer?.choices || [] };
      }
      return { question_id: question.id, value: answer?.value || "" };
    });

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    for (const question of questions) {
      if (question.required && !isAnswered(question, answers[question.id])) {
        setError(`Responda: ${question.label}`);
        return;
      }
    }
    setPhase("submitting");
    setError(null);
    const result = await submitPublicSipatResponse(token, buildPayload());
    if (!result.ok) {
      setError(result.message);
      setPhase("form");
      return;
    }
    setPhase("done");
  };

  if (phase === "done") {
    return (
      <div className="sipat-form sipat-form--done">
        <div className="sipat-form__done-badge" aria-hidden="true">
          ✓
        </div>
        <p className="sipat-form__eyebrow">SIPAT · CIPA</p>
        <h1>Obrigado pela participação</h1>
        <p>Sua resposta anônima foi registrada. Não coletamos nome nem matrícula.</p>
      </div>
    );
  }

  return (
    <div className="sipat-form">
      <header className="sipat-form__header">
        <div className="sipat-form__brand">
          <span className="sipat-form__brand-mark" aria-hidden="true">
            CIPA
          </span>
          <div>
            <p className="sipat-form__eyebrow">SIPAT · resposta anônima</p>
            <p className="sipat-form__brand-sub">Comissão Interna de Prevenção de Acidentes</p>
          </div>
        </div>
        <h1>{survey.title}</h1>
        {survey.description ? <p className="sipat-form__lead">{survey.description}</p> : null}
        <p className="sipat-form__privacy">
          Suas respostas são anônimas. Não pedimos identificação.
        </p>
        <div className="sipat-form__progress" aria-hidden="true">
          <div className="sipat-form__progress-track">
            <div className="sipat-form__progress-fill" style={{ width: `${fillPercent}%` }} />
          </div>
          <span className="sipat-form__progress-label">{fillPercent}%</span>
        </div>
      </header>

      <form className="sipat-form__body" onSubmit={(event) => void onSubmit(event)}>
        {questions.map((question, index) => (
          <fieldset key={question.id} className="sipat-form__question">
            <legend>
              <span className="sipat-form__q-index">{index + 1}</span>
              <span>
                {question.label}
                {question.required ? <span className="sipat-form__req"> *</span> : null}
              </span>
            </legend>
            {question.helpText ? <p className="sipat-form__help">{question.helpText}</p> : null}
            <QuestionInput
              question={question}
              answer={answers[question.id]}
              onValue={(value) => setValue(question.id, value)}
              onToggle={(option) => toggleChoice(question.id, option)}
            />
          </fieldset>
        ))}

        {error ? <p className="sipat-form__error">{error}</p> : null}

        <button
          type="submit"
          className="sipat-form__submit"
          disabled={phase === "submitting"}
        >
          {phase === "submitting" ? "Enviando…" : "Enviar respostas"}
        </button>
      </form>
    </div>
  );
}

function QuestionInput({
  question,
  answer,
  onValue,
  onToggle,
}: {
  question: PublicSipatQuestion;
  answer: AnswerMap[string] | undefined;
  onValue: (value: string) => void;
  onToggle: (option: string) => void;
}) {
  const options = question.options || [];

  if (question.type === "likert_5") {
    return (
      <LikertSlider
        questionId={question.id}
        options={options.length >= 2 ? options : ["1", "2", "3", "4", "5"]}
        value={answer?.value}
        onValue={onValue}
      />
    );
  }

  if (question.type === "text_short") {
    return (
      <input
        className="sipat-form__control"
        type="text"
        maxLength={500}
        value={answer?.value || ""}
        onChange={(event) => onValue(event.target.value)}
        placeholder="Digite sua resposta"
      />
    );
  }

  if (question.type === "text_long") {
    return (
      <textarea
        className="sipat-form__control sipat-form__control--area"
        rows={4}
        maxLength={4000}
        value={answer?.value || ""}
        onChange={(event) => onValue(event.target.value)}
        placeholder="Escreva com detalhes, se quiser"
      />
    );
  }

  if (question.type === "multi_choice") {
    return (
      <div className="sipat-form__options sipat-form__options--grid">
        {options.map((option) => {
          const checked = Boolean(answer?.choices?.includes(option));
          return (
            <label
              key={option}
              className={`sipat-form__chip${checked ? " sipat-form__chip--on" : ""}`}
            >
              <input
                type="checkbox"
                checked={checked}
                onChange={() => onToggle(option)}
              />
              <span>{option}</span>
            </label>
          );
        })}
      </div>
    );
  }

  if (question.type === "yes_no") {
    return (
      <div className="sipat-form__options sipat-form__options--row">
        {options.map((option) => {
          const checked = answer?.value === option;
          return (
            <label
              key={option}
              className={`sipat-form__chip sipat-form__chip--wide${checked ? " sipat-form__chip--on" : ""}`}
            >
              <input
                type="radio"
                name={`q-${question.id}`}
                checked={checked}
                onChange={() => onValue(option)}
              />
              <span>{option}</span>
            </label>
          );
        })}
      </div>
    );
  }

  return (
    <div className="sipat-form__options sipat-form__options--grid">
      {options.map((option) => {
        const checked = answer?.value === option;
        return (
          <label
            key={option}
            className={`sipat-form__chip${checked ? " sipat-form__chip--on" : ""}`}
          >
            <input
              type="radio"
              name={`q-${question.id}`}
              checked={checked}
              onChange={() => onValue(option)}
            />
            <span>{option}</span>
          </label>
        );
      })}
    </div>
  );
}

function LikertSlider({
  questionId,
  options,
  value,
  onValue,
}: {
  questionId: string;
  options: string[];
  value: string | undefined;
  onValue: (value: string) => void;
}) {
  const index = value ? options.indexOf(value) : -1;
  const selected = index >= 0;
  const pct = selected ? (index / Math.max(options.length - 1, 1)) * 100 : 0;
  const lowLabel = options[0] ?? "1";
  const highLabel = options[options.length - 1] ?? "5";

  return (
    <div className="sipat-likert">
      <div className="sipat-likert__value" aria-live="polite">
        {selected ? (
          <>
            Nível <strong>{value}</strong>
            <span className="sipat-likert__hint"> · arraste para ajustar</span>
          </>
        ) : (
          <span className="sipat-likert__hint">Arraste para a direita quanto maior a nota</span>
        )}
      </div>
      <div className="sipat-likert__track-wrap">
        <input
          id={`sipat-likert-${questionId}`}
          className="sipat-likert__range"
          type="range"
          min={0}
          max={options.length - 1}
          step={1}
          value={selected ? index : 0}
          aria-valuetext={selected ? String(value) : "não respondido"}
          onChange={(event) => {
            const next = options[Number(event.target.value)];
            if (next) onValue(next);
          }}
          onPointerDown={(event) => {
            if (selected) return;
            const target = event.currentTarget;
            const rect = target.getBoundingClientRect();
            const ratio = Math.min(1, Math.max(0, (event.clientX - rect.left) / rect.width));
            const nextIndex = Math.round(ratio * (options.length - 1));
            const next = options[nextIndex];
            if (next) onValue(next);
          }}
          style={
            {
              "--sipat-likert-pct": `${pct}%`,
              opacity: selected ? 1 : 0.72,
            } as CSSProperties
          }
        />
        <div
          className="sipat-likert__ticks"
          aria-hidden="true"
          style={{ gridTemplateColumns: `repeat(${options.length}, 1fr)` }}
        >
          {options.map((option) => (
            <button
              key={option}
              type="button"
              className={`sipat-likert__tick${value === option ? " sipat-likert__tick--on" : ""}`}
              onClick={() => onValue(option)}
            >
              {option}
            </button>
          ))}
        </div>
      </div>
      <div className="sipat-likert__ends">
        <span>Menor ({lowLabel})</span>
        <span>Maior ({highLabel})</span>
      </div>
    </div>
  );
}
