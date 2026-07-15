import { useMemo, useState } from "react";
import { submitPublicKaizenSuggestion } from "./api";
import "./kaizen-form.css";

const SECTOR_OPTIONS = ["Administrativo", "Produtivo", "Outra"] as const;

type Step = 1 | 2;
type Phase = "form" | "submitting" | "done" | "error";

const TOTAL_FIELDS = 6;

function isFilled(value: string, min = 1): boolean {
  return value.trim().length >= min;
}

export function KaizenSuggestionForm() {
  const [step, setStep] = useState<Step>(1);
  const [proposerName, setProposerName] = useState("");
  const [sector, setSector] = useState<(typeof SECTOR_OPTIONS)[number]>("Administrativo");
  const [sectorOther, setSectorOther] = useState("");
  const [employeeRegistration, setEmployeeRegistration] = useState("");
  const [workCenter, setWorkCenter] = useState("");
  const [problem, setProblem] = useState("");
  const [solution, setSolution] = useState("");
  const [honeypot, setHoneypot] = useState("");
  const [phase, setPhase] = useState<Phase>("form");
  const [error, setError] = useState<string | null>(null);

  const resolvedSector = sector === "Outra" ? sectorOther.trim() : sector;

  const fillPercent = useMemo(() => {
    const filled =
      Number(isFilled(proposerName)) +
      Number(isFilled(resolvedSector)) +
      Number(isFilled(employeeRegistration)) +
      Number(isFilled(workCenter)) +
      Number(isFilled(problem, 5)) +
      Number(isFilled(solution, 5));
    return Math.round((filled / TOTAL_FIELDS) * 100);
  }, [
    proposerName,
    resolvedSector,
    employeeRegistration,
    workCenter,
    problem,
    solution,
  ]);

  const firstName = proposerName.trim().split(/\s+/)[0] || "";

  function validateStep1(): boolean {
    if (!isFilled(proposerName) || !isFilled(resolvedSector) || !isFilled(employeeRegistration)) {
      setError("Preencha os campos de identificação.");
      return false;
    }
    setError(null);
    return true;
  }

  function validateStep2(): boolean {
    if (!isFilled(workCenter) || !isFilled(problem, 5) || !isFilled(solution, 5)) {
      setError("Descreva o local, o problema e a solução proposta.");
      return false;
    }
    setError(null);
    return true;
  }

  function goNext() {
    if (!validateStep1()) return;
    setStep(2);
  }

  function goBack() {
    setError(null);
    setStep(1);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (step === 1) {
      goNext();
      return;
    }
    if (!validateStep1() || !validateStep2()) return;

    setPhase("submitting");
    try {
      await submitPublicKaizenSuggestion({
        proposer_name: proposerName.trim(),
        sector: resolvedSector,
        employee_registration: employeeRegistration.trim(),
        work_center_or_location: workCenter.trim(),
        problem_description: problem.trim(),
        proposed_solution: solution.trim(),
        website: honeypot || undefined,
      });
      setPhase("done");
    } catch (err) {
      setPhase("error");
      setError(err instanceof Error ? err.message : "Erro ao enviar.");
    }
  }

  if (phase === "done") {
    return (
      <div className="kz-pub-done" role="status">
        <div className="kz-pub-done__check" aria-hidden="true">
          ✓
        </div>
        <p className="kz-pub-form__eyebrow">TRANSFORMA+</p>
        <h1>Sugestão enviada{firstName ? `, ${firstName}` : ""}!</h1>
        <p>
          Obrigado por contribuir. Sua ideia foi registrada com status{" "}
          <strong>Recebido</strong> e a equipe de qualidade já foi notificada para análise.
        </p>
        <div className="kz-pub-done__progress" aria-hidden="true">
          <div className="kz-pub-progress__track">
            <div className="kz-pub-progress__fill" style={{ width: "100%" }} />
          </div>
          <span className="kz-pub-progress__label">100%</span>
        </div>
      </div>
    );
  }

  return (
    <form
      className="kz-pub-form kz-pub-form--wizard"
      onSubmit={(event) => void handleSubmit(event)}
      noValidate
    >
      <header className="kz-pub-form__header">
        <p className="kz-pub-form__eyebrow">TRANSFORMA+</p>
        <h1>Sugestão de melhorias Kaizen</h1>
        <p className="kz-pub-form__lead">
          Etapa {step} de 2 · Campos com * são obrigatórios.
        </p>
        <div
          className="kz-pub-progress"
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={fillPercent}
          aria-label="Porcentagem de preenchimento"
        >
          <div className="kz-pub-progress__track">
            <div className="kz-pub-progress__fill" style={{ width: `${fillPercent}%` }} />
          </div>
          <span className="kz-pub-progress__label">{fillPercent}%</span>
        </div>
      </header>

      {step === 1 ? (
        <section className="kz-pub-card" aria-labelledby="kz-pub-id-title">
          <h2 id="kz-pub-id-title" className="kz-pub-card__title">
            1. Identificação
          </h2>
          <label className="kz-pub-field">
            <span className="kz-pub-label">
              Seu nome <span className="kz-pub-req" aria-hidden="true">*</span>
            </span>
            <input
              value={proposerName}
              onChange={(e) => setProposerName(e.target.value)}
              maxLength={200}
              required
              autoComplete="name"
              autoFocus
            />
          </label>
          <div className="kz-pub-field" role="group" aria-labelledby="kz-pub-sector-label">
            <p id="kz-pub-sector-label" className="kz-pub-label">
              Setor <span className="kz-pub-req" aria-hidden="true">*</span>
            </p>
            <div className="kz-pub-options">
              {SECTOR_OPTIONS.map((option) => (
                <label key={option} className="kz-pub-option">
                  <input
                    type="radio"
                    name="sector"
                    checked={sector === option}
                    onChange={() => setSector(option)}
                  />
                  <span>{option}</span>
                </label>
              ))}
            </div>
            {sector === "Outra" ? (
              <input
                className="kz-pub-field__nested"
                value={sectorOther}
                onChange={(e) => setSectorOther(e.target.value)}
                placeholder="Informe o setor"
                maxLength={200}
                required
                aria-label="Informe o setor"
              />
            ) : null}
          </div>
          <label className="kz-pub-field">
            <span className="kz-pub-label">
              Cadastro <span className="kz-pub-req" aria-hidden="true">*</span>
            </span>
            <input
              value={employeeRegistration}
              onChange={(e) => setEmployeeRegistration(e.target.value)}
              maxLength={50}
              required
              inputMode="numeric"
            />
          </label>
        </section>
      ) : (
        <section className="kz-pub-card" aria-labelledby="kz-pub-improve-title">
          <h2 id="kz-pub-improve-title" className="kz-pub-card__title">
            2. Melhoria
          </h2>
          <label className="kz-pub-field">
            <span className="kz-pub-label">
              Centros de trabalho (CT) e/ou local{" "}
              <span className="kz-pub-req" aria-hidden="true">*</span>
            </span>
            <input
              value={workCenter}
              onChange={(e) => setWorkCenter(e.target.value)}
              maxLength={200}
              required
              autoFocus
            />
          </label>
          <label className="kz-pub-field">
            <span className="kz-pub-label">
              Descrição do problema <span className="kz-pub-req" aria-hidden="true">*</span>
            </span>
            <textarea
              value={problem}
              onChange={(e) => setProblem(e.target.value)}
              maxLength={4000}
              rows={4}
              required
            />
          </label>
          <label className="kz-pub-field">
            <span className="kz-pub-label">
              Como solucionar o problema?{" "}
              <span className="kz-pub-req" aria-hidden="true">*</span>
            </span>
            <textarea
              value={solution}
              onChange={(e) => setSolution(e.target.value)}
              maxLength={4000}
              rows={4}
              required
            />
          </label>
        </section>
      )}

      <label className="kz-pub-hp" aria-hidden="true">
        Website
        <input
          tabIndex={-1}
          autoComplete="off"
          value={honeypot}
          onChange={(e) => setHoneypot(e.target.value)}
        />
      </label>

      {error ? (
        <p className="kz-pub-form__error" role="alert">
          {error}
        </p>
      ) : null}

      <div className="kz-pub-nav">
        {step === 2 ? (
          <button type="button" className="kz-pub-nav__btn kz-pub-nav__btn--ghost" onClick={goBack}>
            Voltar
          </button>
        ) : null}
        {step === 1 ? (
          <button type="submit" className="kz-pub-nav__btn kz-pub-nav__btn--primary">
            Continuar
          </button>
        ) : (
          <button
            type="submit"
            className="kz-pub-nav__btn kz-pub-nav__btn--primary"
            disabled={phase === "submitting"}
          >
            {phase === "submitting" ? "Enviando…" : "Enviar sugestão"}
          </button>
        )}
      </div>
    </form>
  );
}
