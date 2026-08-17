import { useMemo, useState, type FormEvent } from "react";

import { SignatureCapturePanel } from "@delpi/signature-kit";

import {
  submitPublicRefuse,
  submitPublicSign,
  type PublicSignContext,
} from "./api";
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

function AtaBody({ context }: { context: PublicSignContext }) {
  return (
    <>
      <Section title="Pauta" html={context.version.agenda_html} />
      <Section title="Desenvolvimento" html={context.version.body_html} />
      <Section title="Decisões" html={context.version.decisions_html} />
      <Section title="Pendências" html={context.version.pending_html} />
      <Section title="Observações" html={context.version.observations_html} />
    </>
  );
}

export function SignPage({ context, token }: Props) {
  const alreadySigned = context.outcome === "already_signed";
  const [name, setName] = useState(context.signer.display_name || "");
  const [accepted, setAccepted] = useState(false);
  const [png, setPng] = useState<Blob | null>(null);
  const [reason, setReason] = useState("");
  const [showRefuse, setShowRefuse] = useState(false);
  const [phase, setPhase] = useState<Phase>(alreadySigned ? "done" : "form");
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
      setError("Capture a assinatura antes de confirmar.");
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

  if (phase === "refused") {
    return (
      <div className="tm-sign tm-sign--done">
        <div className="tm-sign__done-badge" aria-hidden>
          !
        </div>
        <h1>Recusa registrada</h1>
        <p>A recusa foi enviada aos responsáveis pela ata.</p>
      </div>
    );
  }

  if (phase === "done" || alreadySigned) {
    return (
      <div className="tm-sign">
        <div className="tm-sign__banner tm-sign__banner--success" role="status">
          <div className="tm-sign__done-badge" aria-hidden>
            ✓
          </div>
          <div>
            <h1>
              {alreadySigned ? "Ata já assinada" : "Assinatura registrada"}
            </h1>
            <p>
              {alreadySigned
                ? "Sua assinatura já consta nesta ata. Você pode consultar o conteúdo abaixo."
                : "Obrigado. Sua assinatura da ata Transforma+ foi recebida. Conteúdo da ata abaixo."}
            </p>
          </div>
        </div>

        <header className="tm-sign__header">
          <p className="tm-sign__eyebrow">Transformômetro · Transforma+</p>
          <h1>Ata assinada</h1>
          <p className="tm-sign__subtitle">{subtitle}</p>
        </header>

        <AtaBody context={context} />
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

      <AtaBody context={context} />

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

        <SignatureCapturePanel
          disabled={phase === "submitting"}
          displayName={name}
          showPreview
          padProps={{ className: "delpi-ui-signature-pad--tall" }}
          onChange={setPng}
        />

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
