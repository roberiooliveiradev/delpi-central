import { useState } from "react";
import { submitFeedback, type FeedbackStatus } from "./api";
import "./feedback.css";

type Phase = "form" | "submitting" | "done" | "already";

const RATING_LABELS: Record<number, string> = {
  1: "Muito abaixo",
  2: "Abaixo",
  3: "Na média",
  4: "Muito bom",
  5: "Excepcional",
};

export function FeedbackView({ token, status }: { token: string; status: FeedbackStatus }) {
  const firstName = status.fullName.trim().split(/\s+/)[0];

  const [rating, setRating] = useState(0);
  const [hover, setHover] = useState(0);
  const [likedMost, setLikedMost] = useState("");
  const [suggestions, setSuggestions] = useState("");
  const [phase, setPhase] = useState<Phase>(status.submitted ? "already" : "form");
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (rating < 1) {
      setError("Escolha uma nota de 1 a 5 estrelas.");
      return;
    }
    setError(null);
    setPhase("submitting");
    const result = await submitFeedback(token, { rating, likedMost, suggestions });
    if (result.ok) {
      setPhase("done");
      return;
    }
    if (result.status === 409) {
      setPhase("already");
      return;
    }
    setError(result.message);
    setPhase("form");
  }

  if (phase === "done") {
    return (
      <FeedbackMessage
        title={`Valeu, ${firstName}!`}
        body="Seu retorno chegou até a nossa equipe. É com ele que a gente melhora a experiência de quem visita a DELPI."
      />
    );
  }

  if (phase === "already") {
    return (
      <FeedbackMessage
        title={`Obrigado, ${firstName}!`}
        body="Você já compartilhou sua experiência com a gente. Agradecemos de coração pelo seu tempo."
      />
    );
  }

  const active = hover || rating;

  return (
    <div className="cxfb">
      <span className="cxfb-eyebrow">Programa Experiência do Cliente · DELPI</span>
      <h1 className="cxfb-title">Como foi sua experiência, {firstName}?</h1>
      <p className="cxfb-subtitle">
        Você acabou de montar um cabo na DELPI. Conta pra gente como foi — leva menos de um minuto.
      </p>

      <form className="cxfb-card" onSubmit={handleSubmit}>
        <fieldset className="cxfb-field">
          <legend className="cxfb-label">Sua nota para a visita</legend>
          <div
            className="cxfb-stars"
            role="radiogroup"
            aria-label="Nota de 1 a 5 estrelas"
            onMouseLeave={() => setHover(0)}
          >
            {[1, 2, 3, 4, 5].map((value) => (
              <button
                key={value}
                type="button"
                role="radio"
                aria-checked={rating === value}
                aria-label={`${value} ${value === 1 ? "estrela" : "estrelas"}`}
                className={`cxfb-star${value <= active ? " is-on" : ""}`}
                onMouseEnter={() => setHover(value)}
                onFocus={() => setHover(value)}
                onBlur={() => setHover(0)}
                onClick={() => setRating(value)}
              >
                ★
              </button>
            ))}
          </div>
          <span className="cxfb-rating-label">{active ? RATING_LABELS[active] : "Toque nas estrelas"}</span>
        </fieldset>

        <label className="cxfb-field">
          <span className="cxfb-label">O que você mais gostou?</span>
          <textarea
            className="cxfb-textarea"
            value={likedMost}
            maxLength={2000}
            rows={3}
            placeholder="O atendimento, montar o cabo, conhecer a fábrica..."
            onChange={(event) => setLikedMost(event.target.value)}
          />
        </label>

        <label className="cxfb-field">
          <span className="cxfb-label">Alguma sugestão pra gente melhorar?</span>
          <textarea
            className="cxfb-textarea"
            value={suggestions}
            maxLength={2000}
            rows={3}
            placeholder="Opcional"
            onChange={(event) => setSuggestions(event.target.value)}
          />
        </label>

        {error && <p className="cxfb-error">{error}</p>}

        <button type="submit" className="cxfb-submit" disabled={phase === "submitting"}>
          {phase === "submitting" ? "Enviando..." : "Enviar feedback"}
        </button>
      </form>
    </div>
  );
}

function FeedbackMessage({ title, body }: { title: string; body: string }) {
  return (
    <div className="cxfb cxfb--message">
      <div className="cxfb-check" aria-hidden="true">
        ✓
      </div>
      <h1 className="cxfb-title">{title}</h1>
      <p className="cxfb-subtitle">{body}</p>
      <div className="cxfb-signature">
        <span className="cxfb-signature__line" />
        Equipe DELPI
      </div>
    </div>
  );
}
