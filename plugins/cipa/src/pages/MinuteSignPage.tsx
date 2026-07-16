import { useEffect, useState } from "react";
import {
  ActionButton,
  BackLink,
  FieldLabel,
  HelpTooltip,
  NativeCheckboxControl,
  NativeTextAreaControl,
  NativeTextControl,
  SignaturePad,
} from "@delpi/plugin-ui/index";

import {
  fetchMySignatureImageBlob,
  getMySignatureProfile,
  getSignContext,
  refuseMinute,
  signMinute,
} from "../api/cipaApi";
import { UNIT_LABELS } from "../constants/labels";
import { helpTooltips } from "../content/helpTooltips";
import { navigateCipa } from "../hooks/useCipaRouterPath";

type Props = {
  unitCode: "01" | "02";
  minuteId: string;
};

export function MinuteSignPage({ unitCode, minuteId }: Props) {
  const [context, setContext] = useState<Record<string, unknown> | null>(null);
  const [name, setName] = useState("");
  const [accepted, setAccepted] = useState(false);
  const [png, setPng] = useState<Blob | null>(null);
  const [savedPreviewUrl, setSavedPreviewUrl] = useState<string | null>(null);
  const [hasSavedSignature, setHasSavedSignature] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [refuseReason, setRefuseReason] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      getSignContext(minuteId, controller.signal),
      getMySignatureProfile(controller.signal).catch(() => null),
    ])
      .then(async ([data, profile]) => {
        setContext(data);
        const signer = data.signer as { display_name?: string } | undefined;
        const signerName = (signer?.display_name || "").trim();
        const profileName = (profile?.display_name || "").trim();
        setName(signerName || profileName);

        if (profile?.has_signature) {
          setHasSavedSignature(true);
          try {
            const blob = await fetchMySignatureImageBlob(controller.signal);
            setSavedPreviewUrl((prev) => {
              if (prev) URL.revokeObjectURL(prev);
              return URL.createObjectURL(blob);
            });
          } catch {
            setHasSavedSignature(false);
          }
        }
      })
      .catch((err) => {
        if (!(err instanceof DOMException && err.name === "AbortError")) {
          setError(err instanceof Error ? err.message : "Erro");
        }
      });
    return () => {
      controller.abort();
      setSavedPreviewUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return null;
      });
    };
  }, [minuteId]);

  async function submitSignature(signatureBlob: Blob) {
    if (!accepted || !name.trim()) {
      setError("Preencha nome, aceite o termo e informe a assinatura.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const form = new FormData();
      form.append("signature", signatureBlob, "signature.png");
      form.append("display_name_confirmed", name.trim());
      form.append("terms_accepted", "true");
      form.append("session_id", crypto.randomUUID());
      await signMinute(minuteId, form, crypto.randomUUID());
      navigateCipa(`/apps/cipa/filial-${unitCode}/minutes/${minuteId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao assinar");
    } finally {
      setBusy(false);
    }
  }

  async function confirmSign() {
    if (!png) {
      setError("Preencha nome, aceite o termo e desenhe a assinatura.");
      return;
    }
    await submitSignature(png);
  }

  async function confirmUseSavedSignature() {
    try {
      const blob = await fetchMySignatureImageBlob();
      await submitSignature(blob);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao usar assinatura cadastrada.");
    }
  }

  async function confirmRefuse() {
    if (!refuseReason.trim()) {
      setError("Informe a justificativa da recusa.");
      return;
    }
    setBusy(true);
    try {
      await refuseMinute(minuteId, refuseReason.trim());
      navigateCipa(`/apps/cipa/filial-${unitCode}/minutes/${minuteId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao recusar");
    } finally {
      setBusy(false);
    }
  }

  const minute = (context?.minute || {}) as Record<string, unknown>;
  const version = (context?.version || {}) as Record<string, unknown>;
  const terms = String(context?.terms || "");

  return (
    <div className="cipa-page-stack cipa-sign-page">
      <header className="cipa-header">
        <div>
          <BackLink
            onClick={() => navigateCipa(`/apps/cipa/filial-${unitCode}/minutes/${minuteId}`)}
          >
            Voltar para a ata
          </BackLink>
          <h1>Assinatura da ata</h1>
          <p>
            {UNIT_LABELS[unitCode]} · {String(minute.minute_number || "")} —{" "}
            {String(minute.title || "")}
          </p>
        </div>
      </header>

      {error && <p className="cipa-error">{error}</p>}

      <section className="cipa-card">
        <h2>Resumo</h2>
        <div
          className="cipa-prose"
          dangerouslySetInnerHTML={{
            __html: String(version.body_html || "<p>Sem conteúdo.</p>"),
          }}
        />
      </section>

      <section className="cipa-card">
        <div className="cipa-field">
          <FieldLabel
            label="Nome do signatário"
            htmlFor="cipa-signer-name"
            className="cipa-field__label"
          />
          <NativeTextControl id="cipa-signer-name" value={name} onChange={setName} />
        </div>
        <NativeCheckboxControl
          className="cipa-check"
          checked={accepted}
          onChange={setAccepted}
          label={terms}
        />

        {hasSavedSignature && savedPreviewUrl ? (
          <div className="cipa-signature-preview">
            <p>
              Assinatura cadastrada{" "}
              <ActionButton
                variant="link"
                onClick={() => navigateCipa("/apps/cipa/my-signature")}
              >
                (gerenciar)
              </ActionButton>
            </p>
            <img
              src={savedPreviewUrl}
              alt="Assinatura cadastrada"
              className="cipa-signature-img"
            />
            <div className="cipa-footer-actions">
              <ActionButton
                variant="primary"
                disabled={busy}
                onClick={() => void confirmUseSavedSignature()}
              >
                Usar assinatura cadastrada
              </ActionButton>
            </div>
          </div>
        ) : null}

        <p>
          Assinatura <HelpTooltip content={helpTooltips.signaturePad} />
          {hasSavedSignature ? " — ou desenhe uma nova só para esta ata" : ""}
        </p>
        <SignaturePad onChange={setPng} />
        <div className="cipa-footer-actions">
          <ActionButton variant="primary" disabled={busy} onClick={() => void confirmSign()}>
            Confirmar assinatura
          </ActionButton>
        </div>
      </section>

      <section className="cipa-card">
        <h2>Recusar assinatura</h2>
        <NativeTextAreaControl
          value={refuseReason}
          onChange={setRefuseReason}
          rows={3}
          placeholder="Justificativa obrigatória"
          aria-label="Justificativa da recusa"
        />
        <ActionButton disabled={busy} onClick={() => void confirmRefuse()}>
          Recusar
        </ActionButton>
      </section>
    </div>
  );
}
