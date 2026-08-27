import { useCallback, useMemo, useState, type FormEvent } from "react";

import { SignatureCapturePanel } from "@delpi/signature-kit";
import { MeetingMinuteDocumentView } from "@delpi/transformometro-meeting-minutes-presentation";

import {
  fetchPublicSignatureImageBlob,
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

  const getSignatureImage = useCallback(
    (signatureId: string) => fetchPublicSignatureImageBlob(token, signatureId),
    [token],
  );

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
    const result = await submitPublicSign(token, {
      signature: png,
      displayName: name.trim(),
    });
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

  const showSignedBanner = phase === "done" || alreadySigned;

  return (
    <div className="tm-sign tm-sign--preview">
      {showSignedBanner ? (
        <div className="tm-sign__banner tm-sign__banner--success" role="status">
          <div className="tm-sign__done-badge" aria-hidden>
            ✓
          </div>
          <div>
            <h1>{alreadySigned ? "Ata já assinada" : "Assinatura registrada"}</h1>
            <p>
              {alreadySigned
                ? "Sua assinatura já consta nesta ata. Consulte a prévia do documento abaixo."
                : "Obrigado. Sua assinatura da ata Transforma+ foi recebida."}
            </p>
            {subtitle ? <p className="tm-sign__banner-meta">{subtitle}</p> : null}
          </div>
        </div>
      ) : (
        <header className="tm-sign__header">
          <p className="tm-sign__eyebrow">Transformômetro · Transforma+</p>
          <h1>Assinatura de ata</h1>
          <p className="tm-sign__subtitle">{subtitle}</p>
        </header>
      )}

      <section className="pub-sign-document" aria-label="Documento">
        <h2 className="pub-sign-document__title">Documento</h2>
        <MeetingMinuteDocumentView
          minute={context.minute}
          version={context.version}
          participants={context.participants}
          signers={context.signers}
          signatures={context.signatures}
          getSignatureImage={getSignatureImage}
          ariaLabel="Prévia da ata Transforma+"
        />
      </section>

      {!showSignedBanner ? (
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
            <button
              type="submit"
              className="tm-sign__primary"
              disabled={phase === "submitting"}
            >
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
      ) : null}

      {!showSignedBanner && showRefuse ? (
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
          <button
            type="button"
            className="tm-sign__secondary"
            onClick={onRefuse}
            disabled={phase === "submitting"}
          >
            Confirmar recusa
          </button>
        </div>
      ) : null}
    </div>
  );
}
