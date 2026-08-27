import { useCallback, useMemo, useState, type FormEvent } from "react";

import { CipaMeetingMinuteDocumentView } from "@delpi/cipa-meeting-minutes-presentation";
import { SignatureCapturePanel } from "@delpi/signature-kit";

import {
  fetchPublicSignatureImageBlob,
  submitPublicRefuse,
  submitPublicSign,
  type PublicSignContext,
} from "./signApi";
import "./sign.css";

type Phase = "form" | "submitting" | "done" | "refused";

type Props = {
  context: PublicSignContext;
  token: string;
};

export function CipaSignPage({ context, token }: Props) {
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
      <div className="cipa-sign cipa-sign--done">
        <div className="cipa-sign__done-badge" aria-hidden>
          !
        </div>
        <h1>Recusa registrada</h1>
        <p>A recusa foi enviada aos responsáveis pela ata.</p>
      </div>
    );
  }

  const showSignedBanner = phase === "done" || alreadySigned;

  return (
    <div className="cipa-sign cipa-sign--preview">
      {showSignedBanner ? (
        <div className="cipa-sign__banner cipa-sign__banner--success" role="status">
          <div className="cipa-sign__done-badge" aria-hidden>
            ✓
          </div>
          <div>
            <h1>{alreadySigned ? "Ata já assinada" : "Assinatura registrada"}</h1>
            <p>
              {alreadySigned
                ? "Sua assinatura já consta nesta ata. Consulte a prévia do documento abaixo."
                : "Obrigado. Sua assinatura da ata CIPA foi recebida."}
            </p>
            {subtitle ? <p className="cipa-sign__banner-meta">{subtitle}</p> : null}
          </div>
        </div>
      ) : (
        <header className="cipa-sign__header">
          <p className="cipa-sign__eyebrow">CIPA · Minha DELPI</p>
          <h1>Assinatura de ata</h1>
          <p className="cipa-sign__subtitle">{subtitle}</p>
        </header>
      )}

      <CipaMeetingMinuteDocumentView
        minute={context.minute}
        version={context.version}
        participants={context.participants as never[]}
        signers={context.signers as never[]}
        signatures={context.signatures}
        getSignatureImage={getSignatureImage}
        ariaLabel="Prévia da ata CIPA"
      />

      {!showSignedBanner ? (
        <form className="cipa-sign__form" onSubmit={onSign}>
          <label className="cipa-sign__label">
            Nome do signatário
            <input
              className="cipa-sign__input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              disabled={phase === "submitting"}
              required
            />
          </label>

          <label className="cipa-sign__check">
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

          {error ? <p className="cipa-sign__error">{error}</p> : null}

          <div className="cipa-sign__actions">
            <button
              type="submit"
              className="cipa-sign__primary"
              disabled={phase === "submitting"}
            >
              {phase === "submitting" ? "Enviando…" : "Assinar"}
            </button>
            <button
              type="button"
              className="cipa-sign__secondary"
              disabled={phase === "submitting"}
              onClick={() => setShowRefuse((v) => !v)}
            >
              Recusar
            </button>
          </div>
        </form>
      ) : null}

      {!showSignedBanner && showRefuse ? (
        <div className="cipa-sign__refuse">
          <label className="cipa-sign__label">
            Motivo da recusa
            <textarea
              className="cipa-sign__input cipa-sign__textarea"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              disabled={phase === "submitting"}
            />
          </label>
          <button
            type="button"
            className="cipa-sign__secondary"
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
