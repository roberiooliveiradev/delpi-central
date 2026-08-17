import { useState, type FormEvent } from "react";
import { submitPublicDenuncia } from "./api";
import "./denuncia.css";

const MIN_LENGTH = 10;
const MAX_LENGTH = 8000;

export function CanalDenunciaPublicForm() {
  const [description, setDescription] = useState("");
  const [honeypot, setHoneypot] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const trimmed = description.trim();
  const canSubmit =
    !submitting && trimmed.length >= MIN_LENGTH && description.length <= MAX_LENGTH;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) return;
    setSubmitting(true);
    setError(null);
    try {
      await submitPublicDenuncia({
        description: trimmed,
        website: honeypot || undefined,
      });
      setDescription("");
      setDone(true);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Não foi possível enviar a denúncia.");
    } finally {
      setSubmitting(false);
    }
  }

  if (done) {
    return (
      <div className="cd-pub">
        <header className="cd-pub__header">
          <p className="cd-pub__eyebrow">Ouvidoria · Sigilo</p>
          <h1>Canal de Denúncia</h1>
        </header>
        <p className="cd-pub__success" role="status">
          Denúncia enviada com sucesso. A Ouvidoria recebeu seu relato para análise.
        </p>
      </div>
    );
  }

  return (
    <div className="cd-pub">
      <header className="cd-pub__header">
        <p className="cd-pub__eyebrow">Ouvidoria · Sigilo</p>
        <h1>Canal de Denúncia</h1>
        <p className="cd-pub__lead">
          Envie um relato à Ouvidoria da DELPI sem precisar de conta no Minha DELPI.
          O envio é anônimo: não pedimos nome, e-mail nem identificação.
        </p>
      </header>

      <form className="cd-pub__form" onSubmit={(event) => void handleSubmit(event)} noValidate>
        <label className="cd-pub__label" htmlFor="cd-pub-description">
          Relato da denúncia
        </label>
        <textarea
          id="cd-pub-description"
          className="cd-pub__textarea"
          value={description}
          onChange={(event) => {
            setDescription(event.target.value.slice(0, MAX_LENGTH));
            setError(null);
          }}
          disabled={submitting}
          maxLength={MAX_LENGTH}
          rows={12}
          placeholder="Descreva o ocorrido com o máximo de clareza e objetividade."
        />
        <div className="cd-pub__meta">
          <span>Mínimo de {MIN_LENGTH} caracteres.</span>
          <span>
            {description.length} / {MAX_LENGTH}
          </span>
        </div>

        <label className="cd-pub__hp" aria-hidden="true">
          Website
          <input
            tabIndex={-1}
            autoComplete="off"
            value={honeypot}
            onChange={(event) => setHoneypot(event.target.value)}
          />
        </label>

        {error ? (
          <p className="cd-pub__error" role="alert">
            {error}
          </p>
        ) : null}

        <button type="submit" className="cd-pub__submit" disabled={!canSubmit} aria-busy={submitting || undefined}>
          {submitting ? "Enviando…" : "Enviar denúncia"}
        </button>
      </form>
    </div>
  );
}
