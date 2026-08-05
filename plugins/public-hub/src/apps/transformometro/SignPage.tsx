import { useMemo, useState, type FormEvent } from "react";

import {
  submitPublicRefuse,
  submitPublicSign,
  type PublicSignContext,
} from "./api";
import { SimpleSignaturePad } from "./SimpleSignaturePad";
import "./sign.css";

type Phase = "form" | "submitting" | "done" | "refused";

type Props = {
  context: PublicSignContext;
  token: string;
};

function Section({ title, html }: { title: string; html?: string }) {
  if (!html?.trim()) return null;
  return (
    <section className="tm-sign__section">
      <h2>{title}</h2>
      <div className="tm-sign__html" dangerouslySetInnerHTML={{ __html: html }} />
    </section>
  );
}

export function SignPage({ context, token }: Props) {
  const [name, setName] = useState(context.signer.display_name || "");
  const [accepted, setAccepted] = useState(false);
  const [png, setPng] = useState<Blob | null>(null);
  const [reason, setReason] = useState("");
  const [showRefuse, setShowRefuse] = useState(false);
  const [phase, setPhase] = useState<Phase>("form");
  const [error, setError] = useState<string | null>(null);

  const subtitle = useMemo(() => {
    const number = context.minute.minute_number || "";
    const title = context.minute.title || "";
    return [number, title].filter(Boolean).join(" — ");
  }, [context.minute.minute_number, context.minute.title]);

  async function onSign(event: FormEvent) {
    event.preventDefault();
    if (!accepted || !name.trim()) {
      setError("Confirme o nome e aceite o termo para assinar.");
      return;
    }
    if (!png) {
      setError("Desenhe a assinatura antes de confirmar.");
      return;
    }
    setPhase("submitting");
    setError(null);
    const result = await submitPublicSign(token, { signature: png, displayName: name.trim() });
    if (!result.ok) {
      setError(result.message);
      setPhase("form");
      return;
    }
    setPhase("done");
  }

  async function onRefuse() {
    if (!reason.trim()) {
      setError("Informe a justificativa da recusa.");
      return;
    }
    setPhase("submitting");
    setError(null);
    const result = await submitPublicRefuse(token, reason.trim());
    if (!result.ok) {
      setError(result.message);
      setPhase("form");
      return;
    }
    setPhase("refused");
  }

  if (phase === "done" || phase === "refused") {
    return (
      <div className="tm-sign tm-sign--done">
        <div className="tm-sign__done-badge" aria-hidden>
          {phase === "done" ? "✓" : "!"}
        </div>
        <h1>{phase === "done" ? "Assinatura registrada" : "Recusa registrada"}</h1>
        <p>
          {phase === "done"
            ? "Obrigado. Sua assinatura da ata Transforma+ foi recebida."
            : "A recusa foi enviada aos responsáveis pela ata."}
        </p>
      </div>
    );
  }

  return (
    <div className="tm-sign">
      <header className="tm-sign__header">
        <p className="tm-sign__eyebrow">Transformômetro · Transforma+</p>
        <h1>Assinatura de ata</h1>
        <p className="tm-sign__subtitle">{subtitle}</p>
      </header>

      <Section title="Pauta" html={context.version.agenda_html} />
      <Section title="Desenvolvimento" html={context.version.body_html} />
      <Section title="Decisões" html={context.version.decisions_html} />
      <Section title="Pendências" html={context.version.pending_html} />
      <Section title="Observações" html={context.version.observations_html} />

      <form className="tm-sign__form" onSubmit={onSign}>
        <label className="tm-sign__label">
          Nome do signatário
          <input
            className="tm-sign__input"
            value={name}
            onChange={(e) => setName(e.target.value)}
            disabled={phase === "submitting"}
            required
          />
        </label>

        <label className="tm-sign__check">
          <input
            type="checkbox"
            checked={accepted}
            onChange={(e) => setAccepted(e.target.checked)}
            disabled={phase === "submitting"}
          />
          <span>{context.terms}</span>
        </label>

        <SimpleSignaturePad disabled={phase === "submitting"} onChange={setPng} />

        {error ? <p className="tm-sign__error">{error}</p> : null}

        <div className="tm-sign__actions">
          <button type="submit" className="tm-sign__primary" disabled={phase === "submitting"}>
            {phase === "submitting" ? "Enviando…" : "Assinar"}
          </button>
          <button
            type="button"
            className="tm-sign__secondary"
            disabled={phase === "submitting"}
            onClick={() => setShowRefuse((v) => !v)}
          >
            Recusar
          </button>
        </div>
      </form>

      {showRefuse ? (
        <div className="tm-sign__refuse">
          <label className="tm-sign__label">
            Motivo da recusa
            <textarea
              className="tm-sign__input tm-sign__textarea"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              disabled={phase === "submitting"}
            />
          </label>
          <button type="button" className="tm-sign__secondary" onClick={onRefuse} disabled={phase === "submitting"}>
            Confirmar recusa
          </button>
        </div>
      ) : null}
    </div>
  );
}
