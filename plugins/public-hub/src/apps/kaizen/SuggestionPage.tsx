import { useState } from "react";
import { submitPublicKaizenSuggestion } from "./api";
import "./kaizen-form.css";

const SECTOR_OPTIONS = ["Administrativo", "Produtivo", "Outra"] as const;

type Phase = "form" | "submitting" | "done" | "error";

export function KaizenSuggestionForm() {
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

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    const resolvedSector = sector === "Outra" ? sectorOther.trim() : sector;
    if (!proposerName.trim() || !resolvedSector || !employeeRegistration.trim()) {
      setError("Preencha os campos de identificação.");
      return;
    }
    if (!workCenter.trim() || problem.trim().length < 5 || solution.trim().length < 5) {
      setError("Descreva o local, o problema e a solução proposta.");
      return;
    }
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
      <div className="kz-pub-done">
        <h1>Sugestão recebida</h1>
        <p>
          Obrigado! Sua ideia de melhoria foi registrada com status <strong>Recebido</strong> e a
          equipe de qualidade será notificada.
        </p>
      </div>
    );
  }

  return (
    <form className="kz-pub-form" onSubmit={(event) => void handleSubmit(event)} noValidate>
      <header className="kz-pub-form__header">
        <p className="kz-pub-form__eyebrow">TRANSFORMA+</p>
        <h1>Sugestão de melhorias Kaizen</h1>
        <p className="kz-pub-form__lead">
          Preencha os dados mínimos. Campos com * são obrigatórios.
        </p>
      </header>

      <section className="kz-pub-card" aria-labelledby="kz-pub-id-title">
        <h2 id="kz-pub-id-title" className="kz-pub-card__title">
          Identificação
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
          />
        </label>
        <div
          className="kz-pub-field"
          role="group"
          aria-labelledby="kz-pub-sector-label"
        >
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

      <section className="kz-pub-card" aria-labelledby="kz-pub-improve-title">
        <h2 id="kz-pub-improve-title" className="kz-pub-card__title">
          Melhoria
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

      {/* honeypot */}
      <label className="kz-pub-hp" aria-hidden="true">
        Website
        <input
          tabIndex={-1}
          autoComplete="off"
          value={honeypot}
          onChange={(e) => setHoneypot(e.target.value)}
        />
      </label>

      {error ? <p className="kz-pub-form__error" role="alert">{error}</p> : null}

      <button type="submit" className="kz-pub-form__submit" disabled={phase === "submitting"}>
        {phase === "submitting" ? "Enviando…" : "Enviar sugestão"}
      </button>
    </form>
  );
}
