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
  type MinuteDetail,
} from "../api/cipaApi";
import { MinuteDocumentView } from "../components/MinuteDocumentView";
import { UNIT_LABELS } from "../constants/labels";
import { helpTooltips } from "../content/helpTooltips";
import { navigateCipa } from "../hooks/useCipaRouterPath";
import {
  CipaFormActions,
  CipaPageHeader,
  CipaSectionCard,
  CipaStateBanner,
} from "../ui/cipaUi";

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
  const documentDetail: MinuteDetail = {
    minute,
    version,
    participants: (context?.participants || []) as Record<string, unknown>[],
    signers: (context?.signers || []) as Record<string, unknown>[],
    signatures: (context?.signatures || []) as Record<string, unknown>[],
    action_items: [],
    versions: [],
  };

  return (
    <div className="cipa-page-stack cipa-sign-page">
      <CipaPageHeader
        nav={
          <BackLink
            onClick={() => navigateCipa(`/apps/cipa/filial-${unitCode}/minutes/${minuteId}`)}
          >
            Voltar para a ata
          </BackLink>
        }
        title="Assinatura da ata"
        subtitle={`${UNIT_LABELS[unitCode]} · ${String(minute.minute_number || "")} — ${String(minute.title || "")}`}
      />

      {error ? <CipaStateBanner variant="error">{error}</CipaStateBanner> : null}

      {context ? <MinuteDocumentView detail={documentDetail} /> : null}

      <CipaSectionCard title="Confirmar assinatura">
        <div className="cipa-field">
          <FieldLabel label="Nome do signatário" htmlFor="cipa-signer-name" />
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
            <CipaFormActions>
              <ActionButton
                variant="primary"
                disabled={busy}
                onClick={() => void confirmUseSavedSignature()}
              >
                Usar assinatura cadastrada
              </ActionButton>
            </CipaFormActions>
          </div>
        ) : null}

        <p>
          Assinatura <HelpTooltip content={helpTooltips.signaturePad} />
          {hasSavedSignature ? " — ou desenhe uma nova só para esta ata" : ""}
        </p>
        <SignaturePad className="delpi-ui-signature-pad--tall" onChange={setPng} />
        <CipaFormActions>
          <ActionButton variant="primary" disabled={busy} onClick={() => void confirmSign()}>
            Confirmar assinatura
          </ActionButton>
        </CipaFormActions>
      </CipaSectionCard>

      <CipaSectionCard title="Recusar assinatura">
        <NativeTextAreaControl
          value={refuseReason}
          onChange={setRefuseReason}
          rows={3}
          placeholder="Justificativa obrigatória"
          aria-label="Justificativa da recusa"
        />
        <CipaFormActions>
          <ActionButton disabled={busy} onClick={() => void confirmRefuse()}>
            Recusar
          </ActionButton>
        </CipaFormActions>
      </CipaSectionCard>
    </div>
  );
}
